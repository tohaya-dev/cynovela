-- Cynovela をはじめる (§5-2 / たたき台 v15)
-- アイコンから開く起動の画面。選ぶのはこの画面、待つ処理は tools/launcher-app/launcher-core.sh が背景で持つ。
-- ∴ この画面が出ている間も、起動を待っている間も、他のアプリを操作できる (§5-2-1 の 2)。

on repoDir()
	set appPath to POSIX path of (path to me)
	set AppleScript's text item delimiters to "/"
	set parts to text items of appPath
	set AppleScript's text item delimiters to ""
	set n to (count parts)
	repeat while n > 0 and item n of parts is ""
		set n to n - 1
	end repeat
	set parentParts to items 1 thru (n - 1) of parts
	set AppleScript's text item delimiters to "/"
	set p to parentParts as string
	set AppleScript's text item delimiters to ""
	return p
end repoDir

on runSh(cmdText)
	return do shell script "/bin/bash -lc " & quoted form of cmdText
end runSh

on runCore(repo, sub)
	return runSh("/bin/bash " & quoted form of (repo & "/tools/launcher-app/launcher-core.sh") & " " & sub)
end runCore

on showErr(titleText, bodyText, logPath)
	display dialog titleText & return & return & bodyText & return & return & "詳しい記録: " & logPath buttons {"OK"} default button "OK" with icon caution
end showErr

on stateValue(stText, keyName)
	repeat with p in paragraphs of stText
		set s to p as string
		if s starts with (keyName & "=") then
			if (length of s) is ((length of keyName) + 1) then return ""
			return text ((length of keyName) + 2) thru -1 of s
		end if
	end repeat
	return ""
end stateValue

on modeLabel(m)
	if m is "full" then return "精度を優先"
	if m is "text" then return "容量を優先"
	if m is "minimal" then return "動作確認用"
	return m
end modeLabel

on extLabel(e)
	if e is "deny" then return "許可しない"
	return "許可"
end extLabel

-- 1回目の問い: どの資料から始めますか (v15 §4)
on askSource(repo)
	repeat
		set c to choose from list {"お試しの資料で始める — 同梱のサンプル資料。すぐに動作を確認できます", "自分のフォルダを選ぶ — フォルダを選ぶ画面が開きます", "何も入れずに始める — 空の状態で開きます。あとから画面で追加します"} with title "Cynovela" with prompt ("どの資料から始めますか？" & return & "あとから画面でも追加できます。いま決めなくてもかまいません。") default items {"お試しの資料で始める — 同梱のサンプル資料。すぐに動作を確認できます"} OK button name "続ける" cancel button name "キャンセル"
		if c is false then return missing value
		set ch to item 1 of c as string
		if ch starts with "お試し" then return " --demo"
		if ch starts with "何も入れずに" then return " --empty"
		try
			set f to choose folder with prompt "読み込むフォルダを選んでください"
			set addOut to runCore(repo, "add-root " & quoted form of (POSIX path of f))
			display dialog addOut buttons {"OK"} default button "OK" with icon note with title "Cynovela"
			return ""
		on error
			-- フォルダ選択のキャンセルは選び直しへ戻る (黙って別の選択肢にしない)
		end try
	end repeat
end askSource

-- 2回目の問い: どの構成で動かしますか (v15 §4 の2回目の形。説明は本文に置き「くわしく」の選択肢は置かない)
on askConfig()
	set c to choose from list {"精度を優先（推奨） — AIモデル 約 4.8 GB", "容量を優先 — AIモデル 約 2.2 GB", "動作確認用 — AIモデル 約 2.2 GB"} with title "Cynovela" with prompt ("どの構成で動かしますか？" & return & "資料の読み取りの正確さは、どれを選んでも同じです。変わるのは、答えを関連の高い順に並べ替えるかどうかと、必要な容量だけです。" & return & "迷ったら「精度を優先」で問題ありません。あとから変更できます。") default items {"精度を優先（推奨） — AIモデル 約 4.8 GB"} OK button name "続ける" cancel button name "キャンセル"
	if c is false then return missing value
	set ch to item 1 of c as string
	if ch starts with "精度を優先" then return "full"
	if ch starts with "容量を優先" then return "text"
	return "minimal"
end askConfig

-- AIモデルが未取得なら、容量と通信量を表示して確認する (選ぶまで通信しない)
on modelGate(repo, modeOpt)
	set hasModel to runSh("ls -d " & quoted form of (repo & "/store/models/models--BAAI--bge-m3/snapshots/") & "*/ >/dev/null 2>&1 && echo yes || echo no")
	if hasModel is "yes" then return modeOpt
	set qm to button returned of (display dialog "AIモデルがまだ入っていません。" & return & "いま取り寄せると、インターネットから約 2.2 GB を受け取ります。" & return & "取り寄せから使えるようになるまで、目安として数分かかります。回線の速さによって変わります。" & return & "取り寄せは初回だけです。二回目からはこの画面は出ません。" buttons {"キャンセル", "取り寄せる"} default button "取り寄せる" with icon caution with title "Cynovela")
	if qm is "キャンセル" then return missing value
	-- 「取り寄せる」が押されたことを起動側へ伝える。実際の取得は launch.sh が持つ
	-- (非対話の起動では対話の問いかけが出ないため、この印が無いと取得が走らない)
	return modeOpt & " --fetch-model"
end modelGate

-- 詳しい設定 (v15 §5)。既定の道では一度も聞かない
on askSettings(repo)
	set portOpt to " --port auto"
	set r to display dialog ("詳しい設定 — ポート番号" & return & return & "自動の場合は空いているポート番号を選びます。使用中だった場合のみお知らせします。") buttons {"キャンセル", "指定する", "自動で決める"} default button "自動で決める" with title "Cynovela" with icon note
	set b to button returned of r
	if b is "キャンセル" then return missing value
	if b is "指定する" then
		set r2 to display dialog "ポート番号" default answer "8765" buttons {"キャンセル", "続ける"} default button "続ける" with title "Cynovela"
		if button returned of r2 is "キャンセル" then return missing value
		set pnum to text returned of r2
		try
			set pcheck to pnum as integer
			set portOpt to " --port " & pnum
		on error
			display dialog "ポート番号は数字で指定してください。自動で決めます。" buttons {"OK"} default button "OK" with icon caution
			set portOpt to " --port auto"
		end try
	end if
	set extOpt to ""
	set r3 to display dialog ("詳しい設定 — 外部アクセス" & return & return & "「許可する」の場合、同じネットワーク上の他の端末から、表示されるアドレスでアクセスできます。社内で画面を見せるときに使います。" & return & "「許可しない」の場合、同じネットワーク上の他の端末からはアクセスできなくなり、この Mac のブラウザからのみ開けます（ターミナルでは --local-only）。") buttons {"キャンセル", "許可しない", "許可する（既定）"} default button "許可する（既定）" with title "Cynovela" with icon note
	set b3 to button returned of r3
	if b3 is "キャンセル" then return missing value
	if b3 is "許可しない" then set extOpt to " --no-external"
	set ddOpt to ""
	set ddLabel to "既定の場所"
	set r4 to display dialog ("詳しい設定 — データの保存先" & return & return & "読み込んだ資料と索引を保存する場所です。外付けドライブを使いたいときに変更します。") buttons {"キャンセル", "変更する", "既定のまま"} default button "既定のまま" with title "Cynovela" with icon note
	set b4 to button returned of r4
	if b4 is "キャンセル" then return missing value
	if b4 is "変更する" then
		try
			set df to choose folder with prompt "データの保存先を選んでください"
			set ddPath to POSIX path of df
			set ddOpt to " --data-dir " & quoted form of ddPath
			set ddLabel to ddPath
		end try
	end if

	set brOpt to ""
	set r5 to display dialog ("詳しい設定 — 起動後の動作" & return & return & "起動後にブラウザを自動で開くかどうかです。") buttons {"キャンセル", "開かない", "ブラウザを自動で開く（既定）"} default button "ブラウザを自動で開く（既定）" with title "Cynovela" with icon note
	set b5 to button returned of r5
	if b5 is "キャンセル" then return missing value
	if b5 is "開かない" then set brOpt to " --no-browser"
	set summaryTxt to "この設定で起動します:" & return & "  ポート番号: " & portOpt & return & "  外部アクセス: "
	if extOpt is "" then
		set summaryTxt to summaryTxt & "許可する"
	else
		set summaryTxt to summaryTxt & "許可しない"
	end if
	set summaryTxt to summaryTxt & return & "  データの保存先: " & ddLabel & return & "  起動後にブラウザを開く: "
	if brOpt is "" then
		set summaryTxt to summaryTxt & "開く"
	else
		set summaryTxt to summaryTxt & "開かない"
	end if
	set r6 to display dialog summaryTxt buttons {"キャンセル", "既定に戻す", "この設定で起動する"} default button "この設定で起動する" with title "Cynovela" with icon note
	set b6 to button returned of r6
	if b6 is "キャンセル" then return missing value
	if b6 is "既定に戻す" then return ""
	return portOpt & extOpt & ddOpt & brOpt
end askSettings

on startFlow(repo, extraOpts)
	set srcOpt to askSource(repo)
	if srcOpt is missing value then return
	set modeOpt to askConfig()
	if modeOpt is missing value then return
	set modeOpt to modelGate(repo, modeOpt)
	if modeOpt is missing value then return
	runCore(repo, "start" & srcOpt & " --mode " & modeOpt & extraOpts)
end startFlow

-- 起動中の画面 (v15 §3)。5秒ごとに進み具合と経過時間を出し直す
on showStarting(repo)
	repeat
		set stTxt to runCore(repo, "status")
		set s to stateValue(stTxt, "STATE")
		if s is not "starting" then
			-- 起動が実らずに止まった場合、黙って最初の画面へ戻さない。
			-- AIモデルの取得に失敗したときは launch.sh がその旨を記録に書くため、それを画面に出す
			if s is not "running" then
				set mc to runSh("tail -n 20 " & quoted form of (repo & "/store/launch-app.log") & " 2>/dev/null | grep -c '取り寄せ先に繋がりませんでした' || true")
				if mc is not "0" then
					display dialog "AIモデルの取り寄せ先に繋がりませんでした。" & return & "インターネットに繋がっているかをご確認ください。" & return & "繋がっているのに失敗する場合は、同梱の LICENSES-MODELS の一覧にある入手先から手で受け取り、" & return & "この配布物の store/models の中へ置いてから、もう一度お試しください。" buttons {"OK"} default button "OK" with icon caution with title "Cynovela"
				end if
			end if
			return true
		end if
		set lastLine to stateValue(stTxt, "LAST")
		set txt to "◐ 起動中" & return & "いま: " & lastLine & return & "経過 " & stateValue(stTxt, "ELAPSED") & "" & return & return & "完了するとブラウザが自動で開きます。この画面は閉じてかまいません。"
		set r to display dialog txt buttons {"起動を中止する", "閉じる（起動は続行）"} default button "閉じる（起動は続行）" with title "Cynovela" with icon note giving up after 5
		if gave up of r then
			-- 出し直して更新する
		else if button returned of r is "起動を中止する" then
			runCore(repo, "abort")
			display dialog "起動を中止しました。" buttons {"OK"} default button "OK" with icon note with title "Cynovela"
			return false
		else
			return false
		end if
	end repeat
end showStarting

-- 読み込むフォルダを管理する (一覧・追加・削除)
on manageRoots(repo)
	repeat
		set c to choose from list {"確認する（一覧）", "追加する", "削除する"} with title "Cynovela" with prompt "読み込むフォルダを管理する" OK button name "続ける" cancel button name "キャンセル"
		if c is false then return
		set ch to item 1 of c as string
		if ch starts with "確認する" then
			set outp to runCore(repo, "list-roots")
			if outp is "[]" then set outp to "(登録されているフォルダはありません)"
			display dialog "読み込むフォルダの一覧:" & return & return & outp buttons {"閉じる"} default button "閉じる" with title "Cynovela"
		else if ch starts with "追加する" then
			try
				set f to choose folder with prompt "読み込むフォルダを選んでください"
				set addOut to runCore(repo, "add-root " & quoted form of (POSIX path of f))
				display dialog addOut buttons {"OK"} default button "OK" with icon note with title "Cynovela"
			end try
		else
			set namesTxt to runCore(repo, "root-names")
			if namesTxt is "" then
				display dialog "(登録されているフォルダはありません)" buttons {"閉じる"} default button "閉じる" with title "Cynovela"
			else
				set nsel to choose from list (paragraphs of namesTxt) with title "Cynovela" with prompt "削除するものを選んでください" OK button name "続ける" cancel button name "キャンセル"
				if nsel is not false then
					set rmOut to runCore(repo, "remove-root " & quoted form of (item 1 of nsel as string))
					display dialog rmOut buttons {"OK"} default button "OK" with icon note with title "Cynovela"
				end if
			end if
		end if
	end repeat
end manageRoots

-- 動作環境を確認する。結果だけで終わらせず、そこから起動へ進める (v15 §6)
on runCheckFlow(repo)
	display notification "動作環境を確認しています…" with title "Cynovela"
	set outp to runSh("/bin/bash " & quoted form of (repo & "/tools/launcher-app/launcher-core.sh") & " check | head -n 40")
	set r to display dialog ("この Mac の動作環境を確認しました。" & return & return & outp & return & return & "全文: store/env-check.txt") buttons {"閉じる", "精度を優先の構成で起動する"} default button "閉じる" with title "Cynovela"
	if button returned of r is "精度を優先の構成で起動する" then
		set srcOpt to askSource(repo)
		if srcOpt is missing value then return
		set modeOpt to modelGate(repo, "full")
		if modeOpt is missing value then return
		runCore(repo, "start" & srcOpt & " --mode " & modeOpt)
	end if
end runCheckFlow

-- 使う前のご注意 (免責5点。中身は README.md を読み込む)
on noticeDialog(repo)
	set t to runCore(repo, "doc notice")
	display dialog t buttons {"キャンセル", "読みました"} default button "読みました" with title "使う前のご注意"
end noticeDialog

-- このツールについて (中身は README.md を読み込む)
on aboutFlow(repo)
	set t to runCore(repo, "doc about")
	set r to display dialog t buttons {"動作環境", "使う前のご注意", "閉じる"} default button "閉じる" with title "Cynovela について"
	set b to button returned of r
	if b is "動作環境" then
		display dialog runCore(repo, "doc env") buttons {"閉じる"} default button "閉じる" with title "動作環境"
	else if b is "使う前のご注意" then
		noticeDialog(repo)
	end if
end aboutFlow

-- 稼働中の最初の画面 (5つ)
on runningMenu(repo, stTxt)
	set addr to runCore(repo, "address")
	set hdr to "● 稼働中   " & addr & return & "経過 " & stateValue(stTxt, "ELAPSED") & " ／ 構成: " & modeLabel(stateValue(stTxt, "MODE")) & " ／ 外部アクセス: " & extLabel(stateValue(stTxt, "EXTERNAL"))
	set c to choose from list {"画面を開く — ブラウザで開きます", "アドレスをコピー — 他の Mac から開くときに使います", "読み込むフォルダを管理する — 登録されているものの確認・追加・削除", "再起動する", "停止する"} with title "Cynovela" with prompt hdr default items {"画面を開く — ブラウザで開きます"} OK button name "続ける" cancel button name "キャンセル"
	if c is false then return false
	set ch to item 1 of c as string
	if ch starts with "画面を開く" then
		runSh("open " & quoted form of addr)
		return false
	else if ch starts with "アドレスをコピー" then
		set the clipboard to addr
		display notification "コピーしました: " & addr with title "Cynovela"
		return true
	else if ch starts with "読み込むフォルダ" then
		manageRoots(repo)
		return true
	else if ch starts with "再起動する" then
		runCore(repo, "restart")
		return true
	else
		runCore(repo, "stop")
		display dialog "止めました。" buttons {"OK"} default button "OK" with icon note with title "Cynovela"
		return false
	end if
end runningMenu

-- 停止中の最初の画面 (6つ)
on stoppedMenu(repo, stTxt)
	set c to choose from list {"起動する — 資料を読み込んで、質問できる状態にします", "設定を変えて起動する — ポート番号・外部アクセス・データの保存先", "読み込むフォルダを管理する — 登録されているものの確認・追加・削除", "動作環境を確認する — 起動せずに、必要なものがそろっているかだけ調べます", "ターミナルから使う — コマンド一覧を開きます", "このツールについて — できること・使い方"} with title "Cynovela" with prompt "○ 停止中" default items {"起動する — 資料を読み込んで、質問できる状態にします"} OK button name "続ける" cancel button name "キャンセル"
	if c is false then return false
	set ch to item 1 of c as string
	if ch starts with "起動する" then
		startFlow(repo, "")
		return true
	else if ch starts with "設定を変えて起動する" then
		set o to askSettings(repo)
		if o is missing value then return true
		startFlow(repo, o)
		return true
	else if ch starts with "読み込むフォルダ" then
		manageRoots(repo)
		return true
	else if ch starts with "動作環境を確認する" then
		runCheckFlow(repo)
		return true
	else if ch starts with "ターミナルから使う" then
		runSh("open -e " & quoted form of (repo & "/USE-FROM-TERMINAL.txt"))
		return true
	else
		aboutFlow(repo)
		return true
	end if
end stoppedMenu

on run
	set repo to repoDir()
	set logPath to repo & "/store/launch-app.log"
	set launchSh to repo & "/launch.sh"

	try
		do shell script "test -f " & quoted form of launchSh
	on error
		display dialog "起動用のファイルが見つかりません。" & return & return & "この「Cynovela をはじめる」は、配布物のフォルダの中に置いたまま使ってください。" buttons {"OK"} default button "OK" with icon stop
		return
	end try


	repeat
		set stTxt to runCore(repo, "status")
		set s to stateValue(stTxt, "STATE")
		if s is "starting" then
			if not showStarting(repo) then return
		else if s is "running" then
			if not runningMenu(repo, stTxt) then return
		else
			if not stoppedMenu(repo, stTxt) then return
		end if
	end repeat
end run
