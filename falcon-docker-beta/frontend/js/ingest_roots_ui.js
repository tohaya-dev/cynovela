// B4: 取り込み元 (読ませるフォルダ) を画面から足す・見る・外す。
//
//   端末を叩かせないための画面。管理者だけに出す (受け口の側も _require_admin)。
//   決定 3-4 に従い、足すときはフォルダを辿って選ばせる。フルパスの手入力欄は作らない。
//   同時に複数は選ばせない (選べるのは「いま開いているフォルダ」1件だけ)。
//
//   コンテナ (コンテナ) で動く形態では、画面から受け取り手の機械のフォルダを辿れないため、
//   受け口が can_add_from_screen: false を返す。その場合も「足す」の押し口は消さず (決定 31-1)、
//   押すとターミナルへ貼る1行 (コピーできる) と Cynovela-add-folder.command のガイドを出す。

let _irState = { current: '', parent: null, home: '', canAdd: false, restartNeeded: false, addLine: '' };

async function renderIngestRoots() {
  const host = document.getElementById('ingest-roots-panel');
  if (!host) return;
  let data;
  try {
    data = await API.get('/api/ingest-roots');
  } catch (e) {
    host.innerHTML = `<div style="padding:10px;color:#b91c1c;">${escapeHtml(
      lj(`Could not read the ingest sources: ${e.message}`, `取り込み元を読めませんでした: ${e.message}`)
    )}</div>`;
    return;
  }
  _irState.canAdd = !!data.can_add_from_screen;
  _irState.restartNeeded = !!data.restart_required_to_apply;
  _irState.home = data.start_dir || '';
  _irState.addLine = data.add_from_terminal || './launch.sh --add';

  const rows = (data.roots || []).map(r => `
    <tr>
      <td style="padding:6px 8px;">${escapeHtml(r.label || r.name || '')}</td>
      <td style="padding:6px 8px;color:#475569;word-break:break-all;">${escapeHtml(r.host_path || '')}</td>
      <td style="padding:6px 8px;">${r.exists
        ? `<span style="color:#059669;">${lj('found', 'あります')}</span>`
        : (_irState.restartNeeded
          ? `<span style="color:#b45309;">${lj('readable after restart', '起動し直すと読み込めます')}</span>`
          : `<span style="color:#b45309;">${lj('missing', '見つかりません')}</span>`)}</td>
      <td style="padding:6px 8px;text-align:right;">
        <button class="btn btn-sm btn-danger" data-role-min="admin"
                onclick="irRemoveRoot('${escapeHtml(r.name)}')">🗑 ${lj('Remove', '外す')}</button>
      </td>
    </tr>`).join('');

  const empty = `<tr><td colspan="4" style="padding:14px;text-align:center;color:#94a3b8;">${
    lj('No ingest sources yet. Add one below.', 'まだ1件もありません。下から足してください。')
  }</td></tr>`;

  const addBlock = _irState.canAdd
    ? `<button class="btn btn-primary" data-role-min="admin" onclick="irOpenPicker()">
         📁 ${lj('Add an ingest source', '取り込み元を足す')}
       </button>
       <div style="margin-top:6px;color:#64748b;font-size:14px;">
         ${lj('Pick a folder by walking into it. One at a time.',
              'フォルダを辿って選びます。一度に選べるのは1件です。')}
       </div>`
    : `<button class="btn btn-primary" data-role-min="admin" onclick="irOpenTerminalGuide()">
         📁 ${lj('Add an ingest source', '取り込み元を足す')}
       </button>`;

  const restartNote = _irState.restartNeeded
    ? `<div style="margin-top:8px;color:#b45309;">${lj(
        'Newly added sources become readable the next time you run the entry point.',
        '足した取り込み元が読めるようになるのは、次に入口を叩いたあとです。')}</div>`
    : `<div style="margin-top:8px;color:#059669;">${lj(
        'Added sources stay after a restart and take effect right away.',
        '足した取り込み元は起動し直しても残り、すぐに使えます。')}</div>`;

  host.innerHTML = `
    <div style="margin-bottom:8px;color:#475569;">${lj(
      'Folders listed here are the only places this app may read from.',
      'ここに並んでいるフォルダだけが、このアプリが読める場所です。')}</div>
    <table style="width:100%;border-collapse:collapse;background:#fff;border:1px solid #e2e8f0;border-radius:6px;">
      <thead><tr style="background:#f1f5f9;">
        <th style="padding:6px 8px;text-align:left;">${lj('Name', '名前')}</th>
        <th style="padding:6px 8px;text-align:left;">${lj('Folder', 'フォルダ')}</th>
        <th style="padding:6px 8px;text-align:left;">${lj('State', '状態')}</th>
        <th></th>
      </tr></thead>
      <tbody>${rows || empty}</tbody>
    </table>
    <div style="margin-top:12px;">${addBlock}</div>
    ${restartNote}`;
  if (typeof applyRoleRestrictions === 'function') applyRoleRestrictions();
}

function irGoToSettingsRoots() {
  if (typeof navigate === 'function') navigate('settings');
  const acc = document.querySelector('.settings-acc[data-acc-key="ingest-roots"]');
  if (acc) { acc.open = true; acc.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
  renderIngestRoots();
}

async function irOpenPicker() {
  document.getElementById('ir-picker-modal')?.remove();
  const m = document.createElement('div');
  m.id = 'ir-picker-modal';
  m.className = 'modal-overlay active';
  m.innerHTML = `
    <div class="modal" style="width:560px;max-width:90vw;">
      <h3 style="margin:0 0 10px 0;">📁 ${lj('Choose a folder to add', '足すフォルダを選ぶ')}</h3>
      <div id="ir-cur" style="font-size:15px;color:#475569;margin-bottom:8px;padding:6px 10px;
           background:#f8fafc;border-radius:4px;word-break:break-all;">…</div>
      <div style="display:flex;gap:6px;margin-bottom:8px;">
        <button id="ir-up" class="btn btn-sm" onclick="irPickerUp()">↑ ${lj('Up', '上へ')}</button>
      </div>
      <div id="ir-list" style="max-height:46vh;overflow-y:auto;border:1px solid #e2e8f0;border-radius:6px;
           padding:4px;background:#fff;min-height:120px;"></div>
      <div style="display:flex;gap:8px;margin-top:14px;justify-content:flex-end;">
        <button class="btn" onclick="document.getElementById('ir-picker-modal')?.remove()">${lj('Cancel', 'やめる')}</button>
        <button id="ir-ok" class="btn btn-primary" onclick="irAddCurrent()">✅ ${lj('Add this folder', 'このフォルダを足す')}</button>
      </div>
    </div>`;
  document.body.appendChild(m);
  await irPickerLoad('');
}

async function irPickerLoad(path) {
  let d;
  try {
    d = await API.get(`/api/ingest-roots/browse${path ? `?path=${encodeURIComponent(path)}` : ''}`);
  } catch (e) {
    showToast(lj(`Cannot open that folder: ${e.message}`, `そのフォルダは開けません: ${e.message}`), 'error');
    return;
  }
  _irState.current = d.current_path || '';
  _irState.parent = d.parent_path;
  const cur = document.getElementById('ir-cur');
  if (cur) cur.textContent = _irState.current;
  const up = document.getElementById('ir-up');
  if (up) up.disabled = !d.parent_path;
  const list = document.getElementById('ir-list');
  if (!list) return;
  const fs = d.folders || [];
  list.innerHTML = fs.length
    ? fs.map(f => `<div style="padding:7px 10px;cursor:pointer;border-radius:4px;"
         onmouseover="this.style.background='#f1f5f9'" onmouseout="this.style.background=''"
         onclick="irPickerLoad('${escapeHtml(f.path).replace(/'/g, "\\'")}')">📁 ${escapeHtml(f.name)}</div>`).join('')
    : `<div style="padding:14px;color:#94a3b8;text-align:center;">${lj('(no folders here)', '(この下にフォルダはありません)')}</div>`;
}

async function irPickerUp() {
  if (_irState.parent) await irPickerLoad(_irState.parent);
}

async function irAddCurrent() {
  const p = _irState.current;
  if (!p) return;
  try {
    const r = await API.post('/api/ingest-roots', { path: p });
    document.getElementById('ir-picker-modal')?.remove();
    showToast(r.already
      ? lj('That folder was already added.', 'そのフォルダは既に足してありました。')
      : lj(`Added: ${r.label || r.name}`, `足しました: ${r.label || r.name}`), 'success');
    await renderIngestRoots();
  } catch (e) {
    showToast(lj(`Could not add: ${e.message}`, `足せませんでした: ${e.message}`), 'error');
  }
}

// P-1 (決定 31-1): コンテナで動く形で「取り込み元を足す」を押したときのガイド。
//   弾いて終わらせない。ターミナルへ貼る1行をコピーできる形で出し、
//   Cynovela-add-folder.command でも同じことができる旨を添える。
//   can_add_from_screen が true の形態 (この Mac で直接動く形) ではこのガイドは出さない。
function irOpenTerminalGuide() {
  document.getElementById('ir-add-guide-modal')?.remove();
  const line = _irState.addLine || './launch.sh --add';
  const m = document.createElement('div');
  m.id = 'ir-add-guide-modal';
  m.className = 'modal-overlay active';
  m.innerHTML = `
    <div class="modal" style="width:560px;max-width:90vw;">
      <h3 style="margin:0 0 10px 0;">📁 ${lj('Add an ingest source', '取り込み元を足す')}</h3>
      <div style="margin-bottom:6px;">${lj('This build cannot add a folder from this screen.', 'この形では、画面からフォルダを足せません。')}</div>
      <div style="margin-bottom:4px;">${lj('Instead, run this one line in the terminal:', 'かわりに、ターミナルで次の1行を叩いてください。')}</div>
      <code id="ir-add-line" style="display:inline-block;margin:2px 0 4px 16px;padding:6px 10px;background:#0f172a;color:#e2e8f0;border-radius:4px;">${escapeHtml(line)}</code>
      <div style="margin-left:16px;color:#475569;">${lj('A folder picker will open.', 'フォルダを選ぶ画面が出ます。')}</div>
      <div style="margin-left:16px;color:#475569;margin-bottom:10px;">${lj('After you choose, restart to make it readable.', '選んだあと、起動し直すと読み込めるようになります。')}</div>
      <div>${lj('Double-clicking "Cynovela-add-folder.command" in the app folder', '配布物のフォルダの中にある「Cynovela-add-folder.command」を')}</div>
      <div style="margin-bottom:14px;">${lj('does the same thing.', 'ダブルクリックしても、同じことができます。')}</div>
      <div style="display:flex;gap:8px;justify-content:flex-end;">
        <button class="btn btn-primary" onclick="irCopyAddLine()">${lj('Copy this line', 'この1行をコピー')}</button>
        <button class="btn" onclick="document.getElementById('ir-add-guide-modal')?.remove()">${lj('Close', '閉じる')}</button>
      </div>
    </div>`;
  document.body.appendChild(m);
}

// 貼る1行をバックアップ (クリップボード) へ写す。LAN 越しの http では navigator.clipboard が
// 使えない (secure context でない) ため、選択とコピーの命令で写す道も持つ。
async function irCopyAddLine() {
  const line = _irState.addLine || './launch.sh --add';
  let ok = false;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(line);
      ok = true;
    }
  } catch (e) { ok = false; }
  if (!ok) {
    const ta = document.createElement('textarea');
    ta.value = line;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    ta.remove();
  }
  showToast(ok
    ? lj('Copied.', 'コピーしました。')
    : lj('Could not copy. Please select the line and copy it yourself.', 'コピーできませんでした。行を選択して手でコピーしてください。'),
    ok ? 'success' : 'error');
}

function irRemoveRoot(name) {
  confirmAction(
    lj('Remove ingest source', '取り込み元を外す'),
    lj('This app will stop reading from that folder. The folder and its files are not touched.',
       'このアプリはそのフォルダを読まなくなります。フォルダと中の資料には触りません。'),
    '🗑',
    async () => {
      try {
        await API.del(`/api/ingest-roots/${encodeURIComponent(name)}`);
        showToast(lj('Removed.', '外しました。'), 'success');
        await renderIngestRoots();
      } catch (e) {
        showToast(lj(`Could not remove: ${e.message}`, `外せませんでした: ${e.message}`), 'error');
      }
    }
  );
}

// B4: 取り込み元が0件のときに、フォルダ選びの画面から足す道へ渡すガイド。
//   「登録されていません」で終わらせず、押せる道を1つ出す。
function irNoRootsHtml() {
  return `<div style="padding:16px;text-align:center;">
    <div style="font-weight:600;color:#0f172a;margin-bottom:6px;">${lj('No ingest sources yet', '取り込み元がまだ1件もありません')}</div>
    <div style="color:#64748b;margin-bottom:10px;">${lj('Add a folder to let this app read from it.', '読ませたいフォルダを足すと、ここに出ます。')}</div>
    <button class="btn btn-primary" onclick="document.getElementById('folder-browser-modal')?.remove(); irGoToSettingsRoots();">
      \u{1F4C1} ${lj('Add an ingest source', '取り込み元を足す')}
    </button>
    <div style="margin-top:8px;color:#94a3b8;font-size:13px;">${lj('or from the entry point: ./launch.sh --add', 'または入口から: ./launch.sh --add')}</div>
  </div>`;
}
