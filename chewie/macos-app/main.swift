// ============================================================
//  Cynovela .app の入口 (macos-app-20260830)
//
//  この入口は「起動のやり方」を一切持たない。起動の手順は launch.sh と
//  tools/launch-body.sh に既に在り、Portable 版で実際に動いているものである。
//  ここがやるのは次の 5 つだけで、これ以上のことはしない。
//
//    1. launch.sh を、自分の process group を持つ子として起こす
//    2. その出力を窓 (NSTextView) に流し、末尾を追う
//    3. 立ち上がりの様子を出し続ける (押したあと何も出ない形にはしない)
//    4. 本体が応じたらブラウザを開く
//    5. Cmd+Q で process group へ普通の終了要求を送る
//
//  渡し方は次の 1 通りだけである。
//    cwd = <包み>/Contents/Resources/cynovela
//    bash launch.sh --no-prompt --python <包み>/Contents/Resources/env/bin/python
//
//  🔴 cwd を配布物のディレクトリツリーにするのは必須である。config.py は
//     cynovela.yaml を「いまの居場所からの相対」で読む。ここを間違えると
//     設定を読まないまま既定値で立ち上がる。
//
//  🔴 子には端末を与えない (stdin は /dev/null)。∴ launch.sh は「透過の道」を
//     通って tools/launch-body.sh を exec する。--python を既に付けているので
//     同梱環境の探索は行われない。聞く・待つ・流す の対話の道には入らない。
//     (対話の道は配布物の中へ書き込む。包みは読み取り専用なので入ってはいけない。)
//
//  保存先は包みの外に置く。~/Library/Application Support/Cynovela を根とし、
//  CYNOVELA_DATA_ROOT で本体へ渡す。記録の置き場だけは、本体がロギングを
//  組み立てる時点が保存先の解決より前に在るため、CYNOVELA_LOG_DIR でも渡す。
// ============================================================

import AppKit
import Foundation

let appName = "Cynovela"

// ── 包みの中の場所 ───────────────────────────────────────────
struct Layout {
    let resources: URL
    let treeDir: URL       // Contents/Resources/cynovela  (配布物のディレクトリツリー)
    let envPython: URL     // Contents/Resources/env/bin/python
    let launchScript: URL
    let bundledStore: URL  // 初回に写す元 (配布物に同梱された初期状態)
    let dataRoot: URL      // ~/Library/Application Support/Cynovela
    let logDir: URL

    init() {
        let res = Bundle.main.resourceURL ?? Bundle.main.bundleURL
        resources = res
        treeDir = res.appendingPathComponent("cynovela", isDirectory: true)
        envPython = res.appendingPathComponent("env/bin/python")
        launchScript = treeDir.appendingPathComponent("launch.sh")
        bundledStore = treeDir.appendingPathComponent("store", isDirectory: true)
        let support = FileManager.default.urls(for: .applicationSupportDirectory,
                                               in: .userDomainMask).first
            ?? URL(fileURLWithPath: NSHomeDirectory()).appendingPathComponent("Library/Application Support")
        dataRoot = support.appendingPathComponent(appName, isDirectory: true)
        logDir = dataRoot.appendingPathComponent("logs", isDirectory: true)
    }
}

// ── 自分の process group を持つ子 ─────────────────────────────
//   Foundation の Process は process group を分けられない。分けないと、
//   Cmd+Q で本体だけが残る・止め損なうという形になる。∴ posix_spawn を
//   直接使い、POSIX_SPAWN_SETPGROUP で子を group leader にする。
//   止めるときは kill(-pgid, SIGTERM) で群ごとへ普通の終了要求を送る。
final class ChildProcess {
    private(set) var pid: pid_t = -1
    private var readFD: Int32 = -1
    private var exited = false
    private let lock = NSLock()

    var onOutput: ((String) -> Void)?
    var onExit: ((Int32) -> Void)?

    var isRunning: Bool {
        lock.lock(); defer { lock.unlock() }
        return pid > 0 && !exited
    }

    /// 起こす。cwd の指定は bash に任せる (posix_spawn の chdir は OS の版に依るため)。
    func start(script: URL, cwd: URL, args: [String], env: [String: String]) throws {
        var fds: [Int32] = [-1, -1]
        guard pipe(&fds) == 0 else {
            throw NSError(domain: "Cynovela", code: 1,
                          userInfo: [NSLocalizedDescriptionKey: "パイプを作れませんでした"])
        }
        let rfd = fds[0], wfd = fds[1]

        var actions: posix_spawn_file_actions_t?
        posix_spawn_file_actions_init(&actions)
        // 端末は与えない。これが「透過の道」へ入る条件でもある。
        posix_spawn_file_actions_addopen(&actions, 0, "/dev/null", O_RDONLY, 0)
        posix_spawn_file_actions_adddup2(&actions, wfd, 1)
        posix_spawn_file_actions_adddup2(&actions, wfd, 2)
        posix_spawn_file_actions_addclose(&actions, rfd)
        posix_spawn_file_actions_addclose(&actions, wfd)

        var attr: posix_spawnattr_t?
        posix_spawnattr_init(&attr)
        // 0 = 子自身を group leader にする (pgid == 子の pid)
        posix_spawnattr_setpgroup(&attr, 0)
        posix_spawnattr_setflags(&attr, Int16(POSIX_SPAWN_SETPGROUP))

        //   cd はシェルにさせ、そのまま exec させる。exec なので process group は
        //   保たれ、掴んでいる pid はそのまま本体 (最後は python) を指す。
        let shellLine = "cd \"$1\" || exit 1; shift; exec bash \"$@\""
        var argv: [String] = ["/bin/bash", "-c", shellLine, "cynovela-launcher",
                              cwd.path, script.path]
        argv.append(contentsOf: args)
        let envv: [String] = env.map { "\($0.key)=\($0.value)" }

        var cArgv: [UnsafeMutablePointer<CChar>?] = argv.map { strdup($0) }
        cArgv.append(nil)
        var cEnvv: [UnsafeMutablePointer<CChar>?] = envv.map { strdup($0) }
        cEnvv.append(nil)
        defer {
            for p in cArgv where p != nil { free(p) }
            for p in cEnvv where p != nil { free(p) }
            posix_spawn_file_actions_destroy(&actions)
            posix_spawnattr_destroy(&attr)
        }

        var newPid: pid_t = -1
        let rc = posix_spawn(&newPid, "/bin/bash", &actions, &attr, cArgv, cEnvv)
        close(wfd)
        guard rc == 0 else {
            close(rfd)
            throw NSError(domain: "Cynovela", code: Int(rc),
                          userInfo: [NSLocalizedDescriptionKey:
                                        "起動できませんでした (posix_spawn: \(String(cString: strerror(rc))))"])
        }
        pid = newPid
        readFD = rfd
        pumpOutput()
        waitForExit()
    }

    private func pumpOutput() {
        let fd = readFD
        DispatchQueue.global(qos: .utility).async { [weak self] in
            var buf = [UInt8](repeating: 0, count: 8192)
            var pending = Data()
            while true {
                let n = read(fd, &buf, buf.count)
                if n <= 0 { break }
                pending.append(contentsOf: buf[0..<n])
                // 行の途中で切れた分は次へ持ち越す
                while let nl = pending.firstIndex(of: 0x0A) {
                    let lineData = pending[pending.startIndex..<nl]
                    pending = pending[pending.index(after: nl)...]
                    let line = String(decoding: lineData, as: UTF8.self)
                    DispatchQueue.main.async { self?.onOutput?(line) }
                }
                if pending.count > 65536 {
                    let line = String(decoding: pending, as: UTF8.self)
                    pending = Data()
                    DispatchQueue.main.async { self?.onOutput?(line) }
                }
            }
            if !pending.isEmpty {
                let line = String(decoding: pending, as: UTF8.self)
                DispatchQueue.main.async { self?.onOutput?(line) }
            }
            close(fd)
        }
    }

    private func waitForExit() {
        let target = pid
        DispatchQueue.global(qos: .utility).async { [weak self] in
            var status: Int32 = 0
            while waitpid(target, &status, 0) < 0 && errno == EINTR { continue }
            let code: Int32
            if (status & 0x7F) == 0 { code = (status >> 8) & 0xFF } else { code = 128 + (status & 0x7F) }
            self?.lock.lock(); self?.exited = true; self?.lock.unlock()
            DispatchQueue.main.async { self?.onExit?(code) }
        }
    }

    /// 群ごとに普通の終了要求を送る。叩き殺さない。
    func requestStop() {
        guard isRunning else { return }
        kill(-pid, SIGTERM)
    }
}

// ── 保存先の用意 ─────────────────────────────────────────────
enum DataRoot {
    /// 写さないもの。モデルは包みの中に置いたまま使う (config.py が
    /// 配布物のディレクトリツリーの store/models を先に見るため、写す必要が無い)。
    static let skip: Set<String> = ["models", "logs", "env-check.txt", ".DS_Store"]

    static func seed(from source: URL, to dest: URL) throws {
        let fm = FileManager.default
        try fm.createDirectory(at: dest, withIntermediateDirectories: true)
        let items = (try? fm.contentsOfDirectory(atPath: source.path)) ?? []
        for name in items where !skip.contains(name) {
            let src = source.appendingPathComponent(name)
            let dst = dest.appendingPathComponent(name)
            if fm.fileExists(atPath: dst.path) { continue }
            try fm.copyItem(at: src, to: dst)   // 写すだけ。元は動かさない。
        }
        try fm.createDirectory(at: dest.appendingPathComponent("logs"),
                               withIntermediateDirectories: true)
    }
}

// ── 窓 ───────────────────────────────────────────────────────
final class AppDelegate: NSObject, NSApplicationDelegate {
    let layout = Layout()
    let child = ChildProcess()

    var window: NSWindow!
    var textView: NSTextView!
    var scrollView: NSScrollView!
    var statusLabel: NSTextField!
    var spinner: NSProgressIndicator!
    var openButton: NSButton!

    var port: Int = 8765
    var opened = false
    var serverUp = false
    var started = Date()
    var ticker: Timer?
    var poller: Timer?
    var quitting = false
    var deferredTermination = false   // .terminateLater を返したときだけ真
    var demoMode = false

    // ── 立ち上げ ─────────────────────────────────────────────
    func applicationDidFinishLaunching(_ note: Notification) {
        buildMenu()
        buildWindow()
        NSApp.activate(ignoringOtherApps: true)

        guard checkBundle() else { return }
        guard prepareDataRoot() else { return }
        readPortFromConfig()
        startChild()
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ s: NSApplication) -> Bool { true }

    /// Cmd+Q。群へ普通の終了要求を送り、落ち着くのを待ってから終わる。
    func applicationShouldTerminate(_ s: NSApplication) -> NSApplication.TerminateReply {
        guard child.isRunning, !quitting else { return .terminateNow }
        quitting = true
        deferredTermination = true
        setStatus("終了しています…")
        spinner.startAnimation(nil)
        child.requestStop()
        // 落ちなければ 10 秒で諦めて終わる (待ち続けて固まる形にはしない)
        DispatchQueue.main.asyncAfter(deadline: .now() + 10) {
            NSApp.reply(toApplicationShouldTerminate: true)
        }
        return .terminateLater
    }

    // ── 画面 ─────────────────────────────────────────────────
    func buildWindow() {
        let rect = NSRect(x: 0, y: 0, width: 860, height: 560)
        window = NSWindow(contentRect: rect,
                          styleMask: [.titled, .closable, .miniaturizable, .resizable],
                          backing: .buffered, defer: false)
        window.title = appName
        window.center()
        window.setFrameAutosaveName("CynovelaMainWindow")

        let content = NSView(frame: rect)

        spinner = NSProgressIndicator(frame: NSRect(x: 16, y: rect.height - 36, width: 18, height: 18))
        spinner.style = .spinning
        spinner.controlSize = .small
        spinner.isIndeterminate = true
        spinner.autoresizingMask = [.minYMargin]
        content.addSubview(spinner)

        statusLabel = NSTextField(labelWithString: "起動の準備をしています…")
        statusLabel.frame = NSRect(x: 42, y: rect.height - 36, width: rect.width - 200, height: 18)
        statusLabel.autoresizingMask = [.width, .minYMargin]
        statusLabel.lineBreakMode = .byTruncatingTail
        content.addSubview(statusLabel)

        openButton = NSButton(title: "ブラウザで開く", target: self, action: #selector(openBrowserNow))
        openButton.frame = NSRect(x: rect.width - 150, y: rect.height - 41, width: 134, height: 26)
        openButton.autoresizingMask = [.minXMargin, .minYMargin]
        openButton.bezelStyle = .rounded
        openButton.isEnabled = false
        content.addSubview(openButton)

        scrollView = NSScrollView(frame: NSRect(x: 0, y: 0, width: rect.width, height: rect.height - 48))
        scrollView.autoresizingMask = [.width, .height]
        scrollView.hasVerticalScroller = true
        scrollView.borderType = .noBorder

        textView = NSTextView(frame: scrollView.bounds)
        textView.isEditable = false
        textView.isSelectable = true
        textView.autoresizingMask = [.width]
        textView.font = NSFont.monospacedSystemFont(ofSize: 11, weight: .regular)
        textView.textContainerInset = NSSize(width: 10, height: 8)
        scrollView.documentView = textView
        content.addSubview(scrollView)

        window.contentView = content
        window.makeKeyAndOrderFront(nil)
        spinner.startAnimation(nil)
    }

    func buildMenu() {
        let main = NSMenu()

        let appItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "\(appName) について", action: #selector(about), keyEquivalent: "")
            .target = self
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "保存先を Finder で開く", action: #selector(revealDataRoot), keyEquivalent: "")
            .target = self
        appMenu.addItem(withTitle: "保存されているデータを削除…", action: #selector(deleteDataRoot), keyEquivalent: "")
            .target = self
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "\(appName) を終了", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu
        main.addItem(appItem)

        // 記録を選んで写せるように、標準の編集メニューを置く
        let editItem = NSMenuItem()
        let editMenu = NSMenu(title: "編集")
        editMenu.addItem(withTitle: "コピー", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "すべてを選択", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editItem.submenu = editMenu
        main.addItem(editItem)

        NSApp.mainMenu = main
    }

    // ── 前提の確認 ───────────────────────────────────────────
    func checkBundle() -> Bool {
        let fm = FileManager.default
        for (path, what) in [(layout.launchScript.path, "launch.sh"),
                             (layout.envPython.path, "同梱の python"),
                             (layout.treeDir.path, "配布物のディレクトリツリー")] {
            if !fm.fileExists(atPath: path) {
                fail("この \(appName).app は壊れています。\(what) が見つかりません:\n\(path)\n\n入れ直してください。")
                return false
            }
        }
        return true
    }

    /// 初回だけ。黙って引き継がない・黙って捨てない (受け取り手に選ばせる)。
    func prepareDataRoot() -> Bool {
        let fm = FileManager.default
        if fm.fileExists(atPath: layout.dataRoot.path) {
            try? fm.createDirectory(at: layout.logDir, withIntermediateDirectories: true)
            return true
        }

        let a = NSAlert()
        a.messageText = "保存先をどうしますか"
        a.informativeText = """
        \(appName) は資料・索引・記録を次の場所に保存します。

            \(layout.dataRoot.path)

        まだ何もありません。新しく始めるか、いま使っている Portable 版の
        フォルダから引き継ぐかを選んでください。

        引き継ぐ場合も、選んだフォルダは読むだけで、そのまま残ります。
        """
        a.addButton(withTitle: "新しく始める")
        a.addButton(withTitle: "既存のフォルダから引き継ぐ…")
        a.addButton(withTitle: "終了")

        switch a.runModal() {
        case .alertFirstButtonReturn:
            do {
                try DataRoot.seed(from: layout.bundledStore, to: layout.dataRoot)
                append("[入口] 保存先を新しく作りました: \(layout.dataRoot.path)")
            } catch {
                fail("保存先を作れませんでした:\n\(error.localizedDescription)")
                return false
            }
        case .alertSecondButtonReturn:
            guard let picked = pickPortableFolder() else {
                NSApp.terminate(nil)
                return false
            }
            do {
                try DataRoot.seed(from: picked, to: layout.dataRoot)
                append("[入口] 保存先を引き継ぎました: \(picked.path)")
                append("[入口]   → \(layout.dataRoot.path) (写しただけで、元はそのまま残っています)")
            } catch {
                fail("引き継ぎに失敗しました:\n\(error.localizedDescription)")
                return false
            }
        default:
            NSApp.terminate(nil)
            return false
        }
        return true
    }

    /// Portable 版のフォルダを選ばせ、その中の store/ を返す。
    func pickPortableFolder() -> URL? {
        while true {
            let p = NSOpenPanel()
            p.title = "引き継ぐ Portable 版のフォルダを選んでください"
            p.message = "launch.sh と store/ が入っているフォルダを選びます。"
            p.canChooseDirectories = true
            p.canChooseFiles = false
            p.allowsMultipleSelection = false
            guard p.runModal() == .OK, let url = p.url else { return nil }

            // store/ そのものを選ばれても受ける
            let candidates = [url.appendingPathComponent("store", isDirectory: true), url]
            for c in candidates {
                var isDir: ObjCBool = false
                if FileManager.default.fileExists(atPath: c.path, isDirectory: &isDir), isDir.boolValue,
                   FileManager.default.fileExists(atPath: c.appendingPathComponent("db").path)
                    || FileManager.default.fileExists(atPath: c.appendingPathComponent("secret.key").path) {
                    return c
                }
            }
            let w = NSAlert()
            w.messageText = "そのフォルダは引き継げません"
            w.informativeText = "選ばれた場所に store/ が見つかりませんでした:\n\(url.path)\n\nもう一度選び直すか、新しく始めてください。"
            w.addButton(withTitle: "選び直す")
            w.addButton(withTitle: "終了")
            if w.runModal() != .alertFirstButtonReturn { return nil }
        }
    }

    /// 開く番号。設定から読み、出力に番号が出たらそちらを採る。
    func readPortFromConfig() {
        let yaml = layout.treeDir.appendingPathComponent("cynovela.yaml")
        guard let text = try? String(contentsOf: yaml, encoding: .utf8) else { return }
        var inServer = false
        for raw in text.split(separator: "\n", omittingEmptySubsequences: false) {
            let line = String(raw)
            if !line.hasPrefix(" ") && !line.hasPrefix("\t") {
                inServer = line.hasPrefix("server:")
                continue
            }
            if inServer, let r = line.range(of: "port:") {
                let v = line[r.upperBound...].trimmingCharacters(in: .whitespaces)
                if let n = Int(v), n > 0, n < 65536 { port = n }
                return
            }
        }
    }

    // ── 起こす ───────────────────────────────────────────────
    func startChild() {
        var env = ProcessInfo.processInfo.environment
        env["CYNOVELA_DATA_ROOT"] = layout.dataRoot.path
        // ロギングの組み立ては保存先の解決より前に走る。∴ ここでも渡す。
        env["CYNOVELA_LOG_DIR"] = layout.logDir.path
        // 機械側の conda を掴む余地を作らない。--python は既に渡してある。
        env["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
        env["LANG"] = env["LANG"] ?? "ja_JP.UTF-8"

        var args = ["--no-prompt", "--python", layout.envPython.path]
        if demoMode { args.append("--demo") }

        child.onOutput = { [weak self] line in self?.handleLine(line) }
        child.onExit = { [weak self] code in self?.handleExit(code) }

        append("[入口] 保存先 : \(layout.dataRoot.path)")
        append("[入口] 記録   : \(layout.logDir.path)")
        append("[入口] 起動   : bash launch.sh \(args.joined(separator: " "))")
        append("[入口] 作業場所: \(layout.treeDir.path)")
        append("")

        started = Date()
        setStatus("起動しています… (はじめの一回はモデルの読み込みで少し時間がかかります)")
        ticker = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.tick()
        }
        poller = Timer.scheduledTimer(withTimeInterval: 1.5, repeats: true) { [weak self] _ in
            self?.pollServer()
        }

        do {
            try child.start(script: layout.launchScript, cwd: layout.treeDir, args: args, env: env)
        } catch {
            spinner.stopAnimation(nil)
            fail("起動できませんでした:\n\(error.localizedDescription)")
        }
    }

    func handleLine(_ line: String) {
        append(line)
        // 出力に番号が出たらそれを正とする (--port で変えられているかもしれない)
        for marker in ["http://localhost:", "http://127.0.0.1:"] {
            if let r = line.range(of: marker) {
                let tail = line[r.upperBound...]
                let digits = tail.prefix { $0.isNumber }
                if let n = Int(digits), n > 0, n < 65536 { port = n }
            }
        }
        let t = line.trimmingCharacters(in: .whitespaces)
        if !t.isEmpty && !serverUp {
            setStatus(String(t.prefix(150)))
        }
    }

    func handleExit(_ code: Int32) {
        ticker?.invalidate(); poller?.invalidate()
        spinner.stopAnimation(nil)
        if quitting {
            // 遅らせた終了を返していないときは、返す先が無いので呼ばない
            if deferredTermination { NSApp.reply(toApplicationShouldTerminate: true) }
            return
        }
        openButton.isEnabled = false
        if code == 0 {
            setStatus("終了しました。")
            append("\n[入口] 本体が終了しました (終了コード 0)")
        } else {
            setStatus("起動できませんでした (終了コード \(code))。上の記録を確認してください。")
            append("\n[入口] 本体が終了しました (終了コード \(code))")
            append("[入口] 記録の置き場: \(layout.logDir.path)")
        }
    }

    func tick() {
        guard !serverUp else { return }
        let s = Int(Date().timeIntervalSince(started))
        let base = statusLabel.stringValue
            .replacingOccurrences(of: #"\s*\[\d+ 秒\]$"#, with: "", options: .regularExpression)
        statusLabel.stringValue = "\(base) [\(s) 秒]"
    }

    func pollServer() {
        guard !serverUp, child.isRunning else { return }
        guard let url = URL(string: "http://127.0.0.1:\(port)/api/health") else { return }
        var req = URLRequest(url: url)
        req.timeoutInterval = 2.0
        req.httpMethod = "GET"
        URLSession.shared.dataTask(with: req) { [weak self] _, resp, _ in
            guard resp is HTTPURLResponse else { return }   // 応じた = 立ち上がった
            DispatchQueue.main.async { self?.serverBecameReady() }
        }.resume()
    }

    func serverBecameReady() {
        guard !serverUp else { return }
        serverUp = true
        ticker?.invalidate(); poller?.invalidate()
        spinner.stopAnimation(nil)
        openButton.isEnabled = true
        let took = Int(Date().timeIntervalSince(started))
        setStatus("起動しました (\(took) 秒)。 http://localhost:\(port)")
        append("\n[入口] 立ち上がりました。ブラウザを開きます: http://localhost:\(port)")
        openBrowserNow()
    }

    @objc func openBrowserNow() {
        guard let u = URL(string: "http://localhost:\(port)/") else { return }
        if !opened || serverUp { NSWorkspace.shared.open(u) }
        opened = true
    }

    // ── メニュー ─────────────────────────────────────────────
    @objc func about() {
        let a = NSAlert()
        a.messageText = appName
        a.informativeText = """
        版 \(Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "?")

        保存先:
        \(layout.dataRoot.path)

        この .app を捨てても、上の保存先は残ります。
        消すときは「保存されているデータを削除…」を使ってください。
        """
        a.runModal()
    }

    @objc func revealDataRoot() {
        NSWorkspace.shared.selectFile(nil, inFileViewerRootedAtPath: layout.dataRoot.path)
    }

    @objc func deleteDataRoot() {
        let a = NSAlert()
        a.alertStyle = .critical
        a.messageText = "保存されているデータを削除しますか"
        a.informativeText = """
        次のフォルダを、中身ごと完全に削除します。取り消せません。

            \(layout.dataRoot.path)

        取り込んだ資料そのもの (元のフォルダ) は消えません。消えるのは
        \(appName) が作ったデータベース・索引・記録・控えです。

        削除のあと \(appName) は終了します。
        """
        a.addButton(withTitle: "削除する")
        a.addButton(withTitle: "やめる")
        guard a.runModal() == .alertFirstButtonReturn else { return }

        quitting = true
        setStatus("終了しています (削除の前に本体を止めます)…")
        child.requestStop()

        // 止まるのを少し待ってから消す。動いている最中に消さない。
        DispatchQueue.main.asyncAfter(deadline: .now() + 6) { [weak self] in
            guard let self = self else { return }
            do {
                if FileManager.default.fileExists(atPath: self.layout.dataRoot.path) {
                    try FileManager.default.removeItem(at: self.layout.dataRoot)
                }
                let done = NSAlert()
                done.messageText = "削除しました"
                done.informativeText = self.layout.dataRoot.path
                done.runModal()
            } catch {
                let e = NSAlert()
                e.alertStyle = .warning
                e.messageText = "削除できませんでした"
                e.informativeText = error.localizedDescription
                e.runModal()
            }
            if self.deferredTermination { NSApp.reply(toApplicationShouldTerminate: true) }
            NSApp.terminate(nil)
        }
    }

    // ── 小物 ─────────────────────────────────────────────────
    func append(_ line: String) {
        let atBottom = isScrolledToBottom()
        let s = NSAttributedString(
            string: line + "\n",
            attributes: [.font: NSFont.monospacedSystemFont(ofSize: 11, weight: .regular),
                         .foregroundColor: NSColor.textColor])
        textView.textStorage?.append(s)
        if atBottom { textView.scrollToEndOfDocument(nil) }
    }

    func isScrolledToBottom() -> Bool {
        guard let doc = scrollView.documentView else { return true }
        let visible = scrollView.contentView.bounds
        return visible.maxY >= doc.bounds.maxY - 24
    }

    func setStatus(_ s: String) { statusLabel.stringValue = s }

    func fail(_ message: String) {
        ticker?.invalidate(); poller?.invalidate()
        spinner.stopAnimation(nil)
        setStatus("起動できませんでした。")
        append("\n[入口] " + message)
        let a = NSAlert()
        a.alertStyle = .critical
        a.messageText = "\(appName) を起動できませんでした"
        a.informativeText = message
        a.runModal()
    }
}

// ── ここから走り出す ─────────────────────────────────────────
let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
