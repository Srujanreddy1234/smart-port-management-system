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
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const btn = loginForm.querySelector('.btn-login');
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
      btn.disabled = true;
      setTimeout(() => {
        window.location.href = 'dashboard.html';
      }, 1200);
    });
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
