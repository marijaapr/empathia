/**
 * Shared logout confirmation modal (chat + psychologist dashboard).
 */
const LOGOUT_UI = {
    en: {
        title: 'Log out?',
        body: 'You will need to sign in again to continue using Empathia.',
        cancel: 'Cancel',
        confirm: 'Log out',
        error: 'Logout failed. Please try again.',
    },
    mk: {
        title: 'Одјава?',
        body: 'Ќе треба повторно да се најавиш за да ја користиш Empathia.',
        cancel: 'Откажи',
        confirm: 'Одјави се',
        error: 'Неуспешна одјава. Обиди се повторно.',
    },
};

function logoutLang() {
    const lang = (localStorage.getItem('language') || 'en').toLowerCase();
    return lang === 'mk' ? 'mk' : 'en';
}

function logoutT(key) {
    return LOGOUT_UI[logoutLang()][key] || LOGOUT_UI.en[key];
}

function applyLogoutModalCopy() {
    const title = document.getElementById('logoutModalTitle');
    const body = document.getElementById('logoutModalBody');
    const cancelBtn = document.getElementById('logoutModalCancelBtn');
    const confirmBtn = document.getElementById('logoutModalConfirmBtn');
    if (title) title.textContent = logoutT('title');
    if (body) body.textContent = logoutT('body');
    if (cancelBtn) cancelBtn.textContent = logoutT('cancel');
    if (confirmBtn) confirmBtn.textContent = logoutT('confirm');
}

function setLogoutFormError(message) {
    const el = document.getElementById('logoutFormError');
    if (!el) return;
    if (message) {
        el.textContent = message;
        el.hidden = false;
    } else {
        el.textContent = '';
        el.hidden = true;
    }
}

function openLogoutModal() {
    const modal = document.getElementById('logoutModal');
    if (!modal) return;
    setLogoutFormError('');
    applyLogoutModalCopy();
    modal.style.display = 'flex';
}

function closeLogoutModal() {
    const modal = document.getElementById('logoutModal');
    if (modal) modal.style.display = 'none';
    setLogoutFormError('');
}

function confirmLogout() {
    setLogoutFormError('');
    const confirmBtn = document.getElementById('logoutModalConfirmBtn');
    if (confirmBtn) confirmBtn.disabled = true;

    const token = localStorage.getItem('access_token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};

    const logoutRequest =
        typeof apiFetch === 'function'
            ? apiFetch('/api/auth/logout', { method: 'POST', headers })
            : fetch('/api/auth/logout', {
                  method: 'POST',
                  headers: { ...headers, 'Content-Type': 'application/json' },
              });

    Promise.resolve(logoutRequest)
        .then(async (response) => {
            if (response && !response.ok) {
                let message = logoutT('error');
                try {
                    const data = await response.json();
                    message = data.error || message;
                } catch (_) {
                    /* use default message */
                }
                throw new Error(message);
            }
            localStorage.clear();
            window.location.href = '/login';
        })
        .catch((error) => {
            console.error('Logout error:', error);
            setLogoutFormError(error.message || logoutT('error'));
            if (confirmBtn) confirmBtn.disabled = false;
        });
}

document.addEventListener('click', (e) => {
    if (e.target.id === 'logoutModal') closeLogoutModal();
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.getElementById('logoutModal')?.style.display === 'flex') {
        closeLogoutModal();
    }
});
