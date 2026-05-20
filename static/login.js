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

    if (tab === 'login') {
        document.getElementById('loginForm').classList.add('active');
    } else {
        document.getElementById('signupForm').classList.add('active');
    }

    document.getElementById('loginError').classList.remove('show');
    document.getElementById('signupError').classList.remove('show');
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('signup-role').addEventListener('change', function () {
        const psychologistFields = document.getElementById('psychologistFields');
        if (this.value === 'psychologist') {
            psychologistFields.style.display = 'block';
            document.getElementById('signupError').classList.remove('show');
        } else {
            psychologistFields.style.display = 'none';
        }
    });
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
    const email = document.getElementById('signup-email').value;
    const username = document.getElementById('signup-username').value;
    const password = document.getElementById('signup-password').value;
    const passwordConfirm = document.getElementById('signup-password-confirm').value;
    const license = document.getElementById('signup-license').value;
    const bio = document.getElementById('signup-bio').value;
    const specializations = document.getElementById('signup-specializations').value;

    const errorEl = document.getElementById('signupError');
    const successEl = document.getElementById('signupSuccess');
    const btn = document.getElementById('signupBtn');

    errorEl.classList.remove('show');
    successEl.classList.remove('show');

    if (password !== passwordConfirm) {
        errorEl.textContent = 'Passwords do not match';
        errorEl.classList.add('show');
        return;
    }

    if (role === 'psychologist') {
        if (!license || !bio || !specializations) {
            errorEl.textContent = 'For psychologists: License, Bio, and Specializations are required';
            errorEl.classList.add('show');
            return;
        }
    }

    btn.disabled = true;
    btn.textContent = 'Creating account...';

    try {
        const response = await apiFetch('/api/auth/signup', {
            method: 'POST',
            body: JSON.stringify({
                role,
                email,
                username,
                password,
                license,
                bio,
                specializations
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Signup failed');
        }

        if (role === 'psychologist') {
            successEl.textContent =
                data.message + ' Log in to open your dashboard. Complete your profile there (rates, languages, photo) before going online.';
        } else {
            successEl.textContent = data.message + ' You can now login.';
        }

        successEl.classList.add('show');
        document.getElementById('signupForm').reset();
        document.getElementById('psychologistFields').style.display = 'none';

        setTimeout(() => {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelector('.tab-btn').classList.add('active');
            document.querySelectorAll('.tab-content').forEach(form => form.classList.remove('active'));
            document.getElementById('loginForm').classList.add('active');
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
