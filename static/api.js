/**
 * Shared API helpers — attaches auth headers when a session exists.
 * Server-side require_auth is not enforced yet; this prepares the frontend.
 */

function getAuthHeaders(extraHeaders = {}) {
    const headers = { ...extraHeaders };
    const token = localStorage.getItem('access_token');
    const userId = localStorage.getItem('user_id');
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    if (userId) {
        headers['X-User-ID'] = userId;
    }
    return headers;
}

async function apiFetch(url, options = {}) {
    const headers = getAuthHeaders(options.headers || {});
    if (
        options.body &&
        typeof options.body === 'string' &&
        !headers['Content-Type']
    ) {
        headers['Content-Type'] = 'application/json';
    }
    return fetch(url, { ...options, headers });
}
