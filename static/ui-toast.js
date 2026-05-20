/**
 * Shared toast notifications (chat + psychologist dashboard).
 */
function showToast(message, type = 'success') {
    const colors = {
        success: '#16a34a',
        error: '#dc2626',
        info: '#7c3aed',
        warning: '#d97706',
    };
    const bg = colors[type] || colors.success;

    const notification = document.createElement('div');
    notification.className = `empathia-toast empathia-toast--${type}`;
    notification.setAttribute('role', 'status');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        max-width: min(360px, calc(100vw - 40px));
        padding: 14px 20px;
        background: ${bg};
        color: white;
        border-radius: 10px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.18);
        z-index: 10050;
        font-size: 14px;
        line-height: 1.4;
        animation: empathiaToastIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'empathiaToastOut 0.3s ease forwards';
        setTimeout(() => notification.remove(), 300);
    }, 3200);
}
