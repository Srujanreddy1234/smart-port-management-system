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

  const forgotLink = document.getElementById('forgotPasswordLink');
  const forgotModalEl = document.getElementById('forgotPasswordModal');
  const forgotEmailInput = document.getElementById('forgotPasswordEmail');
  const forgotMsgEl = document.getElementById('forgotPasswordMessage');
  const forgotSubmitBtn = document.getElementById('forgotPasswordSubmit');
  let forgotModal = null;

  if (forgotLink && forgotModalEl) {
    forgotLink.addEventListener('click', (e) => {
      e.preventDefault();
      forgotEmailInput.value = document.getElementById('email').value.trim();
      forgotMsgEl.style.display = 'none';
      forgotModal = forgotModal || new bootstrap.Modal(forgotModalEl);
      forgotModal.show();
    });
  }

  if (forgotSubmitBtn) {
    forgotSubmitBtn.addEventListener('click', async () => {
      const email = forgotEmailInput.value.trim();
      if (!email) {
        forgotMsgEl.style.display = 'block';
        forgotMsgEl.style.background = '#fee2e2';
        forgotMsgEl.style.color = '#991b1b';
        forgotMsgEl.textContent = 'Please enter your email address.';
        return;
      }
      const original = forgotSubmitBtn.innerHTML;
      forgotSubmitBtn.disabled = true;
      forgotSubmitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
      try {
        await Api.forgotPassword(email);
        forgotMsgEl.style.display = 'block';
        forgotMsgEl.style.background = '#dcfce7';
        forgotMsgEl.style.color = '#166534';
        forgotMsgEl.textContent = 'If that email exists, a reset link has been sent.';
      } catch (err) {
        forgotMsgEl.style.display = 'block';
        forgotMsgEl.style.background = '#fee2e2';
        forgotMsgEl.style.color = '#991b1b';
        forgotMsgEl.textContent = err.message || 'Something went wrong. Please try again.';
      } finally {
        forgotSubmitBtn.disabled = false;
        forgotSubmitBtn.innerHTML = original;
      }
    });
  }

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
    errorEl.style.cssText = 'color:#991b1b;font-size:0.875rem;margin-bottom:1rem;padding:8px 12px;background:#fee2e2;border-radius:6px;border:1px solid rgba(220,38,38,0.2);';
    form.insertBefore(errorEl, form.querySelector('.btn-login'));
  }
  errorEl.textContent = message;
  errorEl.style.display = 'block';
}
