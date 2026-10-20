const modalOverlay = document.getElementById('process-modal');
const titleElement = document.getElementById('modal-process-title');
const pidElement = document.getElementById('modal-process-pid');
const procName = document.getElementById('modal-exe');
const themeBtn = document.getElementById('theme-toggle');

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
            const modelText = (data.cpu.model || "İşlemci") + (data.cpu.cores ? " (" + data.cores + " Çekirdek)" : "");
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
    } catch (error) {
        console.error("Sistem metrikleri alınırken hata oluştu:", error);
    }   
}

document.addEventListener('DOMContentLoaded', () => {
    updateSystemStats();
    setInterval(updateSystemStats, 2000);
})

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