const modalOverlay = document.getElementById('process-modal');
const titleElement = document.getElementById('modal-process-title');
const pidElement = document.getElementById('modal-process-pid');
const procName = document.getElementById('modal-exe');

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