function openModal(pid, name) {
    const modalOverlay = document.getElementById('process-modal');
    modalOverlay.classList.add('active');
}

function closeModal() {
    const modalOverlay = document.getElementById('process-modal');
    modalOverlay.classList.remove('active');
}