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

      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
      btn.disabled = true;

      try {
        const result = await Api.login(email, password);
        Api.setSession(result.data);
        window.location.href = 'dashboard.html';
      } catch (err) {
        btn.innerHTML = originalLabel;
        btn.disabled = false;
        let errorEl = loginForm.querySelector('.login-error');
        if (!errorEl) {
          errorEl = document.createElement('div');
          errorEl.className = 'login-error';
          errorEl.style.cssText = 'color:#ea868f;font-size:0.875rem;margin-bottom:1rem;';
          loginForm.insertBefore(errorEl, loginForm.querySelector('.btn-login'));
        }
        errorEl.textContent = err.message || 'Login failed';
      }
    });
  }

  const googleBtn = document.getElementById('googleLoginBtn');
  if (googleBtn) {
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
      account_inactive: 'This account is not active.'
    };
    let errorEl = document.createElement('div');
    errorEl.style.cssText = 'color:#ea868f;font-size:0.875rem;margin-bottom:1rem;';
    errorEl.textContent = errorMessages[oauthError] || 'Sign-in failed.';
    loginForm.insertBefore(errorEl, loginForm.querySelector('.btn-login'));
  }

  document.querySelectorAll('.demo-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const role = btn.dataset.role;
      const emailInput = document.getElementById('email');
      const passInput = document.getElementById('password');
      if (role === 'admin') {
        if (emailInput) emailInput.value = 'admin@smartport.gov.in';
        if (passInput) passInput.value = 'admin123';
      } else if (role === 'operator') {
        if (emailInput) emailInput.value = 'operator@smartport.gov.in';
        if (passInput) passInput.value = 'operator123';
      } else if (role === 'viewer') {
        if (emailInput) emailInput.value = 'viewer@smartport.gov.in';
        if (passInput) passInput.value = 'viewer123';
      }
    });
  });
});
