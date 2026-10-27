const modalOverlay = document.getElementById('process-modal');
const titleElement = document.getElementById('modal-process-title');
const pidElement = document.getElementById('modal-process-pid');
const procName = document.getElementById('modal-exe');
const themeBtn = document.getElementById('theme-toggle');
const cpuCard = document.getElementById('cpu-card');
const corePanel = document.getElementById('core-panel');
const cpuHistory = [];
const ramHistory = [];
const MAX_POINTS = 30;

// grafikleri çizen fonksiyon
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

// cpu modelini ve kullanım yüzdesini isteyen asyncron function
// ram kapasitesini ve kullanım yüzdesini isteyen asyncron function
async function updateSystemStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        const percentEl = document.getElementById('cpu-percent');
        const modelEl = document.getElementById('cpu-model');

        if (percentEl) {
            percentEl.textContent = "%" + data.cpu.percent;
        }
        if (modelEl) {
            const modelText = (data.cpu.model || "İşlemci") + (data.cpu.cores ? " (" + data.cpu.cores + " Çekirdek)" : "");
            modelEl.textContent = modelText;
        }

        const ramPercentEL = document.getElementById('ram-percent');
        const ramUsageEl = document.getElementById('ram-usage');

        if (ramPercentEL) {
            ramPercentEL.textContent = "%" + data.ram.percent;
        }
        if (ramUsageEl) {
            ramUsageEl.textContent = data.ram.used_gb + " GB / " + data.ram.total_gb + "GB";
        }
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
        console.error("Sistem metrikleri alınırken hata oluştu:", error);
    }   
}

// sunucu tarafından gelen veriyi alıp ekrana yazdıran asyncron function
async function updateSystemInfo() {
    try {
        const response = await fetch('/api/system');
        const data = await response.json();
        
        const osEl = document.getElementById('version');

        if (osEl) {
            osEl.textContent = data.os + " · çalışma süresi " + data.uptime;
        }
    } catch (error) {
        console.error("Sistem bilgisi alınamadı:", error);
    }
}


// fonksiyonların belli aralıklarla yenilenmesi, sürekli bir olay
document.addEventListener('DOMContentLoaded', () => {
    updateSystemStats();
    updateSystemInfo();
    setInterval(updateSystemStats, 2000);
    setInterval(updateSystemInfo, 60000);
});

// modal pop-up açma, pid ve isim özelliklerini alma
function openModal(pid, name,) {
    if (titleElement) {
        titleElement.textContent = name;
    }
    if (pidElement) {
        pidElement.textContent = 'PID: ' + pid;
    }
    if (procName) {
        procName.textContent = 'usr/bin/' + name;
    }

    modalOverlay.classList.add('active');
}

function closeModal() {
    modalOverlay.classList.remove('active');
}


// modal pop-up dışa tıklanınca ve esc'ye basınca kapanması
document.addEventListener('DOMContentLoaded', () => {
    if(modalOverlay) {
        modalOverlay.addEventListener('click', (event) => {
            if (event.target === modalOverlay) {
                closeModal();
            }
        });
    }

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeModal();
        }
    });
});


// acık - koyu tema
document.addEventListener('DOMContentLoaded', () => {
    const currentTheme = localStorage.getItem('theme');

    if (currentTheme === 'light') {
        document.body.classList.add('light-theme');
    }

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');

            if (document.body.classList.contains('light-theme')) {
                localStorage.setItem('theme', 'light');
            } else {
                localStorage.setItem('theme', 'dark');
            }
        });
    }
});