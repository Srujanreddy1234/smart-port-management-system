document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('loginForm');
  const togglePassword = document.querySelector('.toggle-password');

  if (togglePassword) {
    togglePassword.addEventListener('click', () => {
      const input = togglePassword.closest('.input-icon-group').querySelector('input');
      const icon = togglePassword.querySelector('i');
      if (input.type === 'password') {
        input.type = 'text';
        icon.classList.replace('fa-eye', 'fa-eye-slash');
      } else {
        input.type = 'password';
        icon.classList.replace('fa-eye-slash', 'fa-eye');
      }
    });
  }

  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = loginForm.querySelector('.btn-login');
      const originalLabel = btn.innerHTML;
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;

      if (!email || !password) {
        showError(loginForm, 'Please enter email and password');
        return;
      }

      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
      btn.disabled = true;

      try {
        const result = await Api.login(email, password);
        Api.setSession(result.data);
        const user = result.data.user;
        const redirect = ROLE_DASHBOARDS[user.role] || 'dashboard.html';
        window.location.href = redirect;
      } catch (err) {
        btn.innerHTML = originalLabel;
        btn.disabled = false;
        showError(loginForm, err.message || 'Login failed');
      }
    });
  }

  document.querySelectorAll('.demo-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const email = btn.dataset.email;
      const pass = btn.dataset.password;
      const emailInput = document.getElementById('email');
      const passInput = document.getElementById('password');
      if (emailInput) emailInput.value = email;
      if (passInput) passInput.value = pass;
    });
  });

  const googleBtn = document.getElementById('googleSignInBtn');
  if (googleBtn) {
    fetch(`${API_BASE_URL}/auth/google/status`)
      .then(res => res.json())
      .then(body => {
        if (body?.data?.configured) {
          googleBtn.style.display = '';
        }
      })
      .catch(() => {});
    googleBtn.addEventListener('click', () => {
      window.location.href = `${API_BASE_URL}/auth/google/login`;
    });
  }

  const params = new URLSearchParams(window.location.search);
  const oauthError = params.get('error');
  if (oauthError) {
    const errorMessages = {
      oauth_failed: 'Google sign-in failed. Please try again.',
      oauth_no_email: 'Google account has no email address.',
      account_inactive: 'This account is not active.',
      oauth_not_configured: 'Google sign-in is not available yet.'
    };
    const form = document.getElementById('loginForm');
    if (form) showError(form, errorMessages[oauthError] || 'Sign-in failed.');
  }
});

function showError(form, message) {
  let errorEl = form.querySelector('.login-error');
  if (!errorEl) {
    errorEl = document.createElement('div');
    errorEl.className = 'login-error';
    errorEl.style.cssText = 'color:#ea868f;font-size:0.875rem;margin-bottom:1rem;padding:8px 12px;background:rgba(220,53,69,0.1);border-radius:6px;border:1px solid rgba(220,53,69,0.2);';
    form.insertBefore(errorEl, form.querySelector('.btn-login'));
  }
  errorEl.textContent = message;
  errorEl.style.display = 'block';
}
