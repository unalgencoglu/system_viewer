const modalOverlay = document.getElementById('process-modal');
const themeBtn = document.getElementById('theme-toggle');
const cpuCard = document.getElementById('cpu-card');
const corePanel = document.getElementById('core-panel');
const cpuHistory = [];
const ramHistory = [];
const MAX_POINTS = 30;

// ------------------------------------------------------------------
// Yardımcılar
// ------------------------------------------------------------------

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

// Süreç adları kullanıcıdan gelir; HTML olarak yorumlanmasın diye kaçırıyoruz
function escapeHtml(text) {
    return String(text)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0;
    while (bytes >= 1024 && i < units.length - 1) { bytes /= 1024; i++; }
    return bytes.toFixed(i === 0 ? 0 : 1) + ' ' + units[i];
}

function formatDuration(seconds) {
    seconds = Math.max(0, Math.floor(seconds));
    const d = Math.floor(seconds / 86400);
    const h = Math.floor(seconds % 86400 / 3600);
    const m = Math.floor(seconds % 3600 / 60);
    if (d) return `${d} gün ${h} saat`;
    if (h) return `${h} saat ${m} dk`;
    return `${m} dk`;
}

// Durum harfinden rozet rengi (CSS sınıfı)
function stateClass(state) {
    return { R: 'running', S: 'sleeping', I: 'sleeping', D: 'waiting', T: 'stopped', t: 'stopped', Z: 'zombie' }[state] || 'sleeping';
}

// ------------------------------------------------------------------
// CPU / RAM kartları
// ------------------------------------------------------------------

function drawGraph(lineEl, history) {
    if (!lineEl) return;
    const step = 300 / (MAX_POINTS - 1);
    const offset = (MAX_POINTS - history.length) * step;
    const points = history
        .map((v, i) => `${offset + i * step},${60 - v * 0.6}`)
        .join(' ');
    lineEl.setAttribute('points', points);
}

if (cpuCard && corePanel) {
    cpuCard.addEventListener('click', () => corePanel.classList.toggle('open'));
}

async function updateSystemStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        setText('cpu-percent', '%' + data.cpu.percent);
        setText('cpu-model', (data.cpu.model || 'İşlemci') + (data.cpu.cores ? ' (' + data.cpu.cores + ' Çekirdek)' : ''));
        setText('ram-percent', '%' + data.ram.percent);
        setText('ram-usage', data.ram.used_gb + ' GB / ' + data.ram.total_gb + ' GB');

        cpuHistory.push(data.cpu.percent);
        if (cpuHistory.length > MAX_POINTS) cpuHistory.shift();
        drawGraph(document.getElementById('cpu-line'), cpuHistory);

        ramHistory.push(data.ram.percent);
        if (ramHistory.length > MAX_POINTS) ramHistory.shift();
        drawGraph(document.getElementById('ram-line'), ramHistory);

        if (corePanel) {
            corePanel.innerHTML = data.cpu.per_core.map((p, i) => `
                <div>
                    <div class="core-head"><span>CPU ${i}</span><span>%${p}</span></div>
                    <div class="core-bar"><div class="core-fill" style="width:${p}%"></div></div>
                </div>`).join('');
        }
    } catch (error) {
        console.error('Sistem metrikleri alınırken hata oluştu:', error);
    }
}

async function updateSystemInfo() {
    try {
        const response = await fetch('/api/system');
        const data = await response.json();
        setText('version', data.os + ' · çalışma süresi ' + data.uptime);
    } catch (error) {
        console.error('Sistem bilgisi alınamadı:', error);
    }
}

// ------------------------------------------------------------------
// Süreç tablosu
// ------------------------------------------------------------------

let processes = [];
let sortKey = 'cpu';
let sortAsc = false;
let searchText = '';

async function updateProcesses() {
    try {
        const response = await fetch('/api/processes');
        processes = await response.json();
        renderProcesses();
    } catch (error) {
        console.error('Süreç listesi alınamadı:', error);
    }
}

function renderProcesses() {
    const body = document.getElementById('process-table-body');
    if (!body) return;

    const q = searchText.toLowerCase();
    const rows = processes.filter(p =>
        !q || String(p.pid).includes(q) || p.name.toLowerCase().includes(q) || p.user.toLowerCase().includes(q));

    rows.sort((a, b) => {
        let x = a[sortKey], y = b[sortKey];
        if (x === null) x = -1;          // "erişim yok" en sona/başa
        if (y === null) y = -1;
        if (typeof x === 'string') { x = x.toLowerCase(); y = y.toLowerCase(); }
        if (x < y) return sortAsc ? -1 : 1;
        if (x > y) return sortAsc ? 1 : -1;
        return a.pid - b.pid;
    });

    setText('process-count', `(${rows.length}/${processes.length})`);

    if (rows.length === 0) {
        body.innerHTML = '<tr><td colspan="7" class="empty-row">Eşleşen süreç yok</td></tr>';
        return;
    }

    body.innerHTML = rows.map(p => `
        <tr>
            <td>${p.pid}</td>
            <td><span class="process-name" data-pid="${p.pid}">${escapeHtml(p.name)}</span></td>
            <td>${escapeHtml(p.user)}</td>
            <td><span class="state-dot ${stateClass(p.state)}" title="${p.state_name}">${p.state}</span></td>
            <td>%${p.cpu}</td>
            <td>%${p.mem}</td>
            <td>${p.open_files === null ? '<span class="muted" title="Erişim yok">—</span>' : p.open_files}</td>
        </tr>`).join('');

    document.querySelectorAll('th.sortable').forEach(th => {
        th.classList.toggle('sorted', th.dataset.key === sortKey);
        th.classList.toggle('asc', th.dataset.key === sortKey && sortAsc);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const body = document.getElementById('process-table-body');
    if (!body) return;

    // Satırlar her güncellemede yeniden çizildiği için tıklamayı tbody'de yakalıyoruz
    body.addEventListener('click', (event) => {
        const el = event.target.closest('.process-name');
        if (el) openModal(Number(el.dataset.pid));
    });

    document.querySelectorAll('th.sortable').forEach(th => {
        th.addEventListener('click', () => {
            if (sortKey === th.dataset.key) {
                sortAsc = !sortAsc;
            } else {
                sortKey = th.dataset.key;
                sortAsc = (sortKey === 'name' || sortKey === 'user' || sortKey === 'pid');
            }
            renderProcesses();
        });
    });

    const search = document.getElementById('process-search');
    if (search) {
        search.addEventListener('input', () => {
            searchText = search.value.trim();
            renderProcesses();
        });
    }

    updateProcesses();
    setInterval(updateProcesses, 3000);
});

// ------------------------------------------------------------------
// Süreç detayı (modal) ve kontrol
// ------------------------------------------------------------------

let currentPid = null;

async function loadProcessDetail(pid) {
    const response = await fetch('/api/process/' + pid);
    if (!response.ok) {
        showControlMessage('Süreç artık çalışmıyor.', false);
        setText('modal-process-status', 'kapandı');
        document.getElementById('modal-process-status').className = 'badge zombie';
        return;
    }
    const d = await response.json();

    setText('modal-process-title', d.name);
    setText('modal-process-pid', 'PID: ' + d.pid);
    const badge = document.getElementById('modal-process-status');
    badge.textContent = d.state_name;
    badge.className = 'badge ' + stateClass(d.state);

    setText('modal-exe', d.exe || '(erişim yok veya çekirdek thread\'i)');
    setText('modal-cmdline', d.cmdline || '-');
    setText('modal-user', d.user);
    setText('modal-ppid', d.ppid);
    setText('modal-nice', d.nice === null ? '-' : d.nice);
    setText('modal-cpu', '%' + d.cpu);

    const start = new Date(d.start_time * 1000);
    setText('modal-uptime', start.toLocaleString('tr-TR') + ' (' + formatDuration(Date.now() / 1000 - d.start_time) + ' aktif)');

    setText('modal-threads', d.threads);
    setText('modal-rss', formatBytes(d.rss));
    setText('modal-vms', formatBytes(d.vms));

    const niceInput = document.getElementById('nice-input');
    if (niceInput && document.activeElement !== niceInput) niceInput.value = d.nice ?? 0;

    const filesBody = document.getElementById('modal-files-body');
    if (d.files === null) {
        setText('modal-file-count', 'erişim yok');
        filesBody.innerHTML = '<tr><td colspan="3">Bu sürecin açık dosyalarını görmek için yetki yok.</td></tr>';
    } else {
        setText('modal-file-count', d.files.length);
        filesBody.innerHTML = d.files.length === 0
            ? '<tr><td colspan="3">Açık dosya yok</td></tr>'
            : d.files.map(f => `
                <tr>
                    <td>${f.fd}</td>
                    <td><span class="fd-type ${f.type}">${f.type}</span></td>
                    <td>${escapeHtml(f.path)}</td>
                </tr>`).join('');
    }
}

function showControlMessage(text, ok) {
    const el = document.getElementById('control-message');
    if (!el) return;
    el.textContent = text;
    el.className = 'control-message ' + (ok ? 'ok' : 'error');
}

async function controlProcess(action) {
    if (currentPid === null) return;

    const name = document.getElementById('modal-process-title').textContent;
    if ((action === 'terminate' || action === 'kill') &&
        !confirm(`${name} (PID ${currentPid}) ${action === 'kill' ? 'zorla kapatılsın' : 'sonlandırılsın'} mı?`)) {
        return;
    }

    const body = { action };
    if (action === 'nice') body.nice = Number(document.getElementById('nice-input').value);

    try {
        const response = await fetch(`/api/process/${currentPid}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const result = await response.json();
        showControlMessage(result.message, result.ok);
    } catch (error) {
        showControlMessage('İstek gönderilemedi.', false);
    }

    // Çekirdeğin sinyali işlemesi için kısa bir süre bekleyip güncel durumu gösteriyoruz
    setTimeout(() => { loadProcessDetail(currentPid); updateProcesses(); }, 300);
}

async function openModal(pid) {
    currentPid = pid;
    showControlMessage('', true);
    modalOverlay.classList.add('active');
    await loadProcessDetail(pid);
}

function closeModal() {
    currentPid = null;
    modalOverlay.classList.remove('active');
}

document.addEventListener('DOMContentLoaded', () => {
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (event) => {
            if (event.target === modalOverlay) closeModal();
        });
        modalOverlay.querySelectorAll('.ctrl-btn').forEach(btn => {
            btn.addEventListener('click', () => controlProcess(btn.dataset.action));
        });
    }

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') closeModal();
    });
});

// ------------------------------------------------------------------
// Genel başlatma ve tema
// ------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    updateSystemStats();
    updateSystemInfo();
    setInterval(updateSystemStats, 2000);
    setInterval(updateSystemInfo, 60000);

    if (localStorage.getItem('theme') === 'light') {
        document.body.classList.add('light-theme');
    }
    if (themeBtn) themeBtn.checked = document.body.classList.contains('light-theme');

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            localStorage.setItem('theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
        });
    }
});
