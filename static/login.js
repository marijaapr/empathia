/**
 * Login & signup page
 */

function switchTab(tab, event) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    event.target.classList.add('active');

    document.querySelectorAll('.tab-content').forEach(form => {
        form.classList.remove('active');
    });

    const loginContainer = document.querySelector('.login-container');

    if (tab === 'login') {
        document.getElementById('loginForm').classList.add('active');
        loginContainer?.classList.remove('signup-active');
    } else {
        document.getElementById('signupForm').classList.add('active');
        loginContainer?.classList.add('signup-active');
    }

    document.getElementById('loginError').classList.remove('show');
    document.getElementById('signupError').classList.remove('show');
}

function setPsychologistFieldsRequired(isPsychologist) {
    const bio = document.getElementById('signup-bio');
    const specializations = document.getElementById('signup-specializations');
    const supervision = document.getElementById('signup-supervision');

    if (bio) bio.required = isPsychologist;
    if (specializations) specializations.required = isPsychologist;
    if (supervision) supervision.required = isPsychologist;
}

function updatePsychologistFieldsVisibility() {
    const roleSelect = document.getElementById('signup-role');
    const psychologistFields = document.getElementById('psychologistFields');
    const isPsychologist = roleSelect?.value === 'psychologist';

    psychologistFields.style.display = isPsychologist ? 'block' : 'none';
    setPsychologistFieldsRequired(isPsychologist);

    if (!isPsychologist) {
        document.getElementById('signupError').classList.remove('show');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const roleSelect = document.getElementById('signup-role');

    CustomSelect.init(roleSelect);
    roleSelect?.addEventListener('change', updatePsychologistFieldsVisibility);

    const params = new URLSearchParams(window.location.search);
    if (params.get('role') === 'psychologist') {
        CustomSelect.setValue(roleSelect, 'psychologist');
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-btn')[1]?.classList.add('active');
        document.querySelectorAll('.tab-content').forEach(form => form.classList.remove('active'));
        document.getElementById('signupForm').classList.add('active');
        document.getElementById('loginForm').classList.remove('active');
        document.querySelector('.login-container')?.classList.add('signup-active');
    }

    updatePsychologistFieldsVisibility();
});

async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('loginError');
    const btn = document.getElementById('loginBtn');

    errorEl.classList.remove('show');
    btn.disabled = true;
    btn.textContent = 'Logging in...';

    try {
        const response = await apiFetch('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Login failed');
        }

        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user_id', data.user_id);
        localStorage.setItem('email', data.email);
        localStorage.setItem('role', data.role || 'user');
        if (data.full_name) {
            localStorage.setItem('user_name', data.full_name);
        }

        if (data.role === 'psychologist') {
            window.location.href = '/psychologist/dashboard';
        } else {
            window.location.href = '/chat';
        }
    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.classList.add('show');
        btn.disabled = false;
        btn.textContent = 'Login';
    }
}

async function handleSignup(event) {
    event.preventDefault();

    const role = document.getElementById('signup-role').value;
    const email = document.getElementById('signup-email').value.trim();
    const username = document.getElementById('signup-username').value.trim();
    const password = document.getElementById('signup-password').value;
    const passwordConfirm = document.getElementById('signup-password-confirm').value;
    const bio = document.getElementById('signup-bio').value.trim();
    const specializations = document.getElementById('signup-specializations').value.trim();
    const supervisionAccepted = document.getElementById('signup-supervision').checked;

    const errorEl = document.getElementById('signupError');
    const successEl = document.getElementById('signupSuccess');
    const btn = document.getElementById('signupBtn');

    errorEl.classList.remove('show');
    successEl.classList.remove('show');

    if (!username || username.length < 2) {
        errorEl.textContent = 'Full name is required (at least 2 characters)';
        errorEl.classList.add('show');
        return;
    }

    if (!email) {
        errorEl.textContent = 'Email is required';
        errorEl.classList.add('show');
        return;
    }

    if (password !== passwordConfirm) {
        errorEl.textContent = 'Passwords do not match';
        errorEl.classList.add('show');
        return;
    }

    if (password.length < 6) {
        errorEl.textContent = 'Password must be at least 6 characters';
        errorEl.classList.add('show');
        return;
    }

    if (role === 'psychologist') {
        if (!bio || !specializations) {
            errorEl.textContent = 'About you and areas of interest are required for psychology students';
            errorEl.classList.add('show');
            return;
        }
        if (!supervisionAccepted) {
            errorEl.textContent = 'Please confirm you understand the supervised trainee role';
            errorEl.classList.add('show');
            return;
        }
    }

    btn.disabled = true;
    btn.textContent = 'Creating account...';

    const payload = {
        role,
        email,
        username,
        password,
        bio: role === 'psychologist' ? bio : undefined,
        specializations: role === 'psychologist' ? specializations : undefined
    };

    try {
        const response = await apiFetch('/api/auth/signup', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Signup failed');
        }

        localStorage.setItem('user_name', data.full_name || username);

        if (role === 'psychologist') {
            successEl.textContent =
                (data.message || 'Signup successful!') +
                ' Log in to open your dashboard and complete your profile before going online.';
        } else {
            successEl.textContent = (data.message || 'Signup successful!') + ' You can now log in.';
        }

        successEl.classList.add('show');
        document.getElementById('signupForm').reset();
        CustomSelect.setValue(document.getElementById('signup-role'), 'user');
        document.getElementById('psychologistFields').style.display = 'none';
        setPsychologistFieldsRequired(false);

        setTimeout(() => {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelector('.tab-btn').classList.add('active');
            document.querySelectorAll('.tab-content').forEach(form => form.classList.remove('active'));
            document.getElementById('loginForm').classList.add('active');
            document.querySelector('.login-container')?.classList.remove('signup-active');
            document.getElementById('login-email').value = email;
            document.getElementById('login-password').value = password;
        }, 2000);
    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.classList.add('show');
        btn.disabled = false;
        btn.textContent = 'Create Account';
    }
}
