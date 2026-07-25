const Utils = {
  formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
  },

  formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric'
    });
  },

  formatDateTime(date) {
    return new Date(date).toLocaleString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  },

  timeAgo(date) {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);
    const intervals = [
      { label: 'year', seconds: 31536000 },
      { label: 'month', seconds: 2592000 },
      { label: 'week', seconds: 604800 },
      { label: 'day', seconds: 86400 },
      { label: 'hour', seconds: 3600 },
      { label: 'minute', seconds: 60 }
    ];
    for (const interval of intervals) {
      const count = Math.floor(seconds / interval.seconds);
      if (count > 0) return `${count} ${interval.label}${count !== 1 ? 's' : ''} ago`;
    }
    return 'Just now';
  },

  generateId() {
    return 'id_' + Math.random().toString(36).substr(2, 9);
  },

  debounce(fn, delay = 300) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  },

  paginate(array, page, perPage = 10) {
    const start = (page - 1) * perPage;
    return {
      data: array.slice(start, start + perPage),
      total: array.length,
      totalPages: Math.ceil(array.length / perPage),
      page,
      perPage
    };
  },

  searchFilter(array, query, keys) {
    if (!query) return array;
    const lower = query.toLowerCase();
    return array.filter(item =>
      keys.some(key => String(item[key]).toLowerCase().includes(lower))
    );
  },

  sortArray(array, key, direction = 'asc') {
    return [...array].sort((a, b) => {
      if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
      if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
      return 0;
    });
  },

  getStatusColor(status) {
    const map = {
      active: 'success', online: 'success', completed: 'success',
      inactive: 'secondary', offline: 'secondary',
      pending: 'warning', in_transit: 'warning', maintenance: 'warning',
      error: 'danger', alert: 'danger', critical: 'danger', overdue: 'danger',
      info: 'info', scheduled: 'info'
    };
    return map[status?.toLowerCase()] || 'secondary';
  },

  getAvatarColor(name) {
    const colors = [
      'linear-gradient(135deg, #0d6efd, #6610f2)',
      'linear-gradient(135deg, #198754, #20c997)',
      'linear-gradient(135deg, #dc3545, #e83e8c)',
      'linear-gradient(135deg, #ffc107, #fd7e14)',
      'linear-gradient(135deg, #0dcaf0, #6610f2)',
      'linear-gradient(135deg, #6f42c1, #d63384)'
    ];
    let hash = 0;
    for (let i = 0; i < (name || '').length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
    return colors[Math.abs(hash) % colors.length];
  },

  getInitials(name) {
    return (name || '').split(' ').map(n => n[0]).join('').toUpperCase().substr(0, 2);
  },

  animateCounter(element, target, duration = 1000) {
    const start = parseInt(element.textContent.replace(/[^0-9]/g, '')) || 0;
    const increment = (target - start) / (duration / 16);
    let current = start;
    const timer = setInterval(() => {
      current += increment;
      if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
        current = target;
        clearInterval(timer);
      }
      element.textContent = Math.floor(current).toLocaleString();
    }, 16);
  },

  showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('show');
  },

  hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('show');
  }
};

document.querySelectorAll('[data-dismiss="modal"]').forEach(btn => {
  btn.addEventListener('click', () => {
    const modal = btn.closest('.modal-overlay');
    if (modal) modal.classList.remove('show');
  });
});

document.querySelectorAll('.modal-overlay').forEach(modal => {
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('show');
  });
});
