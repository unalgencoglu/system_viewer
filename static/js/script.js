const modalOverlay = document.getElementById('process-modal');
const titleElement = document.getElementById('modal-process-title');
const pidElement = document.getElementById('modal-process-pid');
const procName = document.getElementById('modal-exe');
const themeBtn = document.getElementById('theme-toggle');

async function updateCpuStats() {
    try {
        const response = await fetch('/api/cpu');
        const data = await response.json();

        const percentEl = document.getElementById('cpu-percent');
        const modelEl = document.getElementById('cpu-model');

        if (percentEl) {
            percentEl.textContent = "%" + data.percent;
        }
        if (modelEl) {
            const modelText = (data.model || "İşlemci") + (data.cores ? " (" + data.cores + " Çekirdek)" : "");
            modelEl.textContent = modelText;
        }
    } catch (error) {
        console.error("CPU verisi çekilirken hata oluştu:", error);
    }
    
}

document.addEventListener('DOMContentLoaded', () => {
    updateCpuStats();
    setInterval(updateCpuStats, 3000);
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