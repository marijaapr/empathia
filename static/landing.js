/**
 * Landing page — auth redirect and How it works modal
 */

(function redirectIfAuthenticated() {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const role = localStorage.getItem('role');
    if (role === 'psychologist') {
        window.location.replace('/psychologist/dashboard');
    } else {
        window.location.replace('/chat');
    }
})();

document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('howItWorksModal');
    const learnMoreBtn = document.getElementById('learnMoreBtn');
    const closeBtn = document.getElementById('modalCloseBtn');
    const dialog = modal.querySelector('.modal-dialog');

    if (!modal || !learnMoreBtn) return;

    function openModal() {
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('modal-open');
        closeBtn.focus();
    }

    function closeModal() {
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('modal-open');
        learnMoreBtn.focus();
    }

    learnMoreBtn.addEventListener('click', openModal);

    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    if (dialog) {
        dialog.addEventListener('click', (e) => e.stopPropagation());
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('is-open')) {
            closeModal();
        }
    });
});
