const App = {
  init() {
    this.initSidebar();
    this.initTopbar();
    this.initNotifications();
    this.initSearch();
    this.initTheme();
    this.updateClock();
    setInterval(() => this.updateClock(), 1000);
  },

  initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.querySelector('.sidebar-toggle');
    const overlay = document.querySelector('.sidebar-overlay');
    if (toggle && sidebar) {
      toggle.addEventListener('click', () => {
        if (window.innerWidth <= 991) {
          sidebar.classList.toggle('mobile-open');
          overlay?.classList.toggle('show');
        } else {
          sidebar.classList.toggle('collapsed');
        }
      });
    }
    if (overlay) {
      overlay.addEventListener('click', () => {
        sidebar?.classList.remove('mobile-open');
        overlay.classList.remove('show');
      });
    }
    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 991) {
          sidebar?.classList.remove('mobile-open');
          overlay?.classList.remove('show');
        }
      });
    });
  },

  initTopbar() {
    const notifBtn = document.querySelector('#notifBtn');
    const notifDrop = document.querySelector('#notifDropdown');
    if (notifBtn && notifDrop) {
      notifBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        notifDrop.classList.toggle('show');
      });
      document.addEventListener('click', () => notifDrop.classList.remove('show'));
    }
  },

  initNotifications() {
    const markRead = document.querySelector('#markAllRead');
    if (markRead) {
      markRead.addEventListener('click', () => {
        document.querySelectorAll('.notification-item.unread').forEach(item => {
          item.classList.remove('unread');
        });
        const badge = document.querySelector('.topbar-btn .badge-count');
        if (badge) badge.style.display = 'none';
      });
    }
  },

  initSearch() {
    const searchInput = document.querySelector('.search-box input');
    if (searchInput) {
      document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
          e.preventDefault();
          searchInput.focus();
        }
        if (e.key === 'Escape') searchInput.blur();
      });
    }
  },

  initTheme() {
    document.documentElement.setAttribute('data-theme', 'dark');
  },

  updateClock() {
    const clock = document.getElementById('liveClock');
    if (clock) {
      const now = new Date();
      clock.textContent = now.toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
      });
    }
    const dateEl = document.getElementById('liveDate');
    if (dateEl) {
      const now = new Date();
      dateEl.textContent = now.toLocaleDateString('en-US', {
        weekday: 'short', month: 'short', day: 'numeric', year: 'numeric'
      });
    }
  },

  showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer') || this.createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `
      <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
      <span>${message}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = 'position:fixed;top:80px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:8px;';
    document.body.appendChild(container);
    return container;
  }
};

document.addEventListener('DOMContentLoaded', () => App.init());
