const App = {
  init() {
    if (!Api.requireAuth()) return;
    Store.init();
    this.buildSidebar();
    this.initSidebar();
    this.initTopbar();
    this.initNotifications();
    this.initSearch();
    this.initTheme();
    this.initUserDisplay();
    this.updateClock();
    this.initSSE();
    setInterval(() => this.updateClock(), 1000);
  },

  buildSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    const nav = sidebar.querySelector('.sidebar-nav');
    if (!nav) return;

    const navItems = Api.getRoleNavItems();
    const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';

    nav.innerHTML = navItems.map(section => `
      <div class="nav-section">${section.section}</div>
      ${section.items.map(item => `
        <div class="nav-item">
          <a href="${item.href}" class="nav-link ${currentPage === item.href ? 'active' : ''}">
            <i class="fas ${item.icon}"></i>
            <span>${item.label}</span>
          </a>
        </div>
      `).join('')}
    `).join('');
  },

  initUserDisplay() {
    if (typeof Api === 'undefined') return;
    const user = Api.getUser();
    if (!user) return;
    const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email;
    const initials = Utils && Utils.getInitials ? Utils.getInitials(fullName) : fullName.slice(0, 2).toUpperCase();
    const roleLabel = (user.role || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

    document.querySelectorAll('.sidebar-user-info h6').forEach(el => el.textContent = fullName);
    document.querySelectorAll('.sidebar-user-info small').forEach(el => el.textContent = roleLabel);
    document.querySelectorAll('.sidebar-user-avatar').forEach(el => el.textContent = initials);

    document.querySelectorAll('.topbar-right .avatar').forEach(el => {
      el.textContent = initials;
    });
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

      searchInput.addEventListener('input', Utils.debounce(async (e) => {
        const query = e.target.value.trim();
        if (query.length < 2) return;
        try {
          const res = await Api.request(`/search?q=${encodeURIComponent(query)}`);
          this.showSearchResults(res.data);
        } catch (err) {
          // Search endpoint not yet implemented
        }
      }, 400));
    }
  },

  showSearchResults(results) {
    const existing = document.querySelector('.search-results-dropdown');
    if (existing) existing.remove();
    if (!results || Object.values(results).every(v => !v || v.length === 0)) return;

    const dropdown = document.createElement('div');
    dropdown.className = 'search-results-dropdown';
    dropdown.style.cssText = 'position:absolute;top:100%;left:0;right:0;background:var(--card-bg);border:1px solid var(--border-color);border-radius:8px;margin-top:4px;max-height:400px;overflow-y:auto;z-index:1000;box-shadow:0 4px 12px rgba(0,0,0,0.15);';

    const sections = [
      { key: 'ships', label: 'Ships', icon: 'fa-ship', link: 'ships.html' },
      { key: 'containers', label: 'Containers', icon: 'fa-boxes-stacked', link: 'containers.html' },
      { key: 'trucks', label: 'Trucks', icon: 'fa-truck', link: 'trucks.html' },
      { key: 'users', label: 'Users', icon: 'fa-users', link: 'admin.html' },
    ];

    let html = '';
    sections.forEach(s => {
      const items = results[s.key] || [];
      if (items.length > 0) {
        html += `<div style="padding:8px 12px;font-size:0.75rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;">${s.label}</div>`;
        items.slice(0, 5).forEach(item => {
          const name = item.name || item.full_name || item.container_id || item.truck_number || '';
          html += `<a href="${s.link}" style="display:flex;align-items:center;gap:8px;padding:8px 12px;text-decoration:none;color:var(--text-primary);font-size:0.85rem;"><i class="fas ${s.icon}" style="color:var(--primary-light);width:20px;"></i>${name}</a>`;
        });
      }
    });

    if (html) {
      dropdown.innerHTML = html;
      document.querySelector('.search-box').appendChild(dropdown);
    }
  },

  initTheme() {
    document.documentElement.setAttribute('data-theme', 'dark');
  },

  initSSE() {
    if (this._sseConnection) return;
    const token = Api.getToken();
    if (!token) return;
    try {
      this._sseConnection = new EventSource(`${API_BASE_URL}/events/stream`);
      this._sseConnection.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data);
          this.handleRealtimeEvent(event);
        } catch (err) {}
      };
      this._sseConnection.onerror = () => {
        this._sseConnection.close();
        this._sseConnection = null;
        setTimeout(() => this.initSSE(), 30000);
      };
    } catch (e) {}
  },

  handleRealtimeEvent(event) {
    if (event.severity === 'Critical') {
      this.showToast(event.title, 'danger');
    } else if (event.severity === 'Warning') {
      this.showToast(event.title, 'warning');
    }
    document.dispatchEvent(new CustomEvent('port-event', { detail: event }));
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

  editProfile() {
    const user = Store.getUser();
    if (!user) return;
    const modal = App.createModal({
      id: 'editProfileModal', title: 'Edit Profile', width: '500px',
      body: `<form id="editProfileForm" class="modal-form">
        <div class="form-group"><label>Full Name</label><input type="text" id="epFirstName" class="form-control" value="${user.first_name || ''}"></div>
        <div class="form-group"><label>Email</label><input type="email" id="epEmail" class="form-control" value="${user.email || ''}" readonly></div>
        <div class="form-group"><label>Phone</label><input type="tel" id="epPhone" class="form-control" value="${user.phone || ''}"></div>
        <div class="form-group"><label>Department</label><input type="text" id="epDepartment" class="form-control" value="${user.department || ''}"></div>
        <div class="form-group"><label>Designation</label><input type="text" id="epDesignation" class="form-control" value="${user.designation || ''}"></div>
        <div class="form-group"><label>Employee ID</label><input type="text" id="epEmployeeId" class="form-control" value="${user.employee_id || ''}"></div>
      </form>`,
      footer: `<button class="btn btn-secondary" onclick="document.getElementById('editProfileModal').remove()">Cancel</button><button class="btn btn-primary" onclick="App.saveProfile()">Save Changes</button>`
    });
  },

  saveProfile() {
    const user = Store.getUser();
    if (!user) return;
    const updated = {
      ...user,
      first_name: document.getElementById('epFirstName')?.value || user.first_name,
      phone: document.getElementById('epPhone')?.value || user.phone,
      department: document.getElementById('epDepartment')?.value || user.department,
      designation: document.getElementById('epDesignation')?.value || user.designation,
      employee_id: document.getElementById('epEmployeeId')?.value || user.employee_id,
    };
    Store.setUser(updated);
    Store.set('user', updated);
    document.getElementById('editProfileModal').remove();
    App.initUserDisplay();
    App.showToast('Profile updated successfully', 'success');
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
  },

  createModal(config) {
    const existing = document.getElementById(config.id);
    if (existing) existing.remove();

    const modal = document.createElement('div');
    modal.id = config.id;
    modal.className = 'modal-overlay';
    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:10000;display:none;align-items:center;justify-content:center;';
    modal.innerHTML = `
      <div class="modal-content" style="background:var(--card-bg);border-radius:12px;max-width:${config.width || '600px'};width:90%;max-height:90vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,0.3);">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px;border-bottom:1px solid var(--border-color);">
          <h5 style="margin:0;font-weight:600;">${config.title}</h5>
          <button onclick="this.closest('.modal-overlay').remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1.2rem;"><i class="fas fa-times"></i></button>
        </div>
        <div style="padding:24px;">${config.body}</div>
        ${config.footer ? `<div style="padding:16px 24px;border-top:1px solid var(--border-color);display:flex;justify-content:flex-end;gap:8px;">${config.footer}</div>` : ''}
      </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
    return modal;
  },

  async exportCSV(data, filename) {
    if (!data || data.length === 0) {
      this.showToast('No data to export', 'warning');
      return;
    }
    const headers = Object.keys(data[0]);
    const csv = [
      headers.join(','),
      ...data.map(row => headers.map(h => `"${String(row[h] || '').replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'export.csv';
    a.click();
    URL.revokeObjectURL(url);
    this.showToast('Export complete', 'success');
  },

  exportTrucks() { App.exportCSV(Store.get('trucks'), 'trucks-export.csv'); App.showToast('Trucks exported', 'success'); },
  exportSecurity() { App.exportCSV(Store.get('alerts'), 'security-alerts-export.csv'); App.showToast('Security alerts exported', 'success'); },
  exportBerths() { App.exportCSV(Store.get('berths'), 'berths-export.csv'); App.showToast('Berths exported', 'success'); },

  showAddTruckModal() {
    App.createModal({
      id: 'addTruckModal', title: 'Add New Truck', width: '500px',
      body: `<form id="addTruckForm" class="modal-form">
        <div class="form-group"><label>Truck Number *</label><input type="text" id="atTruckNumber" class="form-control" placeholder="TN-2001" required></div>
        <div class="form-row"><div class="form-group"><label>Driver Name</label><input type="text" id="atDriver" class="form-control" placeholder="Driver name"></div><div class="form-group"><label>Phone</label><input type="tel" id="atPhone" class="form-control" placeholder="+1-555-0300"></div></div>
        <div class="form-row"><div class="form-group"><label>Type</label><select id="atType" class="form-select"><option>Heavy</option><option>Medium</option><option>Light</option></select></div><div class="form-group"><label>Status</label><select id="atStatus" class="form-select"><option>Available</option><option>At Gate</option><option>Loading</option><option>In Transit</option></select></div></div>
      </form>`,
      footer: `<button class="btn btn-secondary" onclick="document.getElementById('addTruckModal').remove()">Cancel</button><button class="btn btn-primary" onclick="App.submitAddTruck()">Add Truck</button>`
    });
  },

  submitAddTruck() {
    const truckNumber = document.getElementById('atTruckNumber')?.value.trim();
    if (!truckNumber) { App.showToast('Truck number is required', 'danger'); return; }
    Store.add('trucks', {
      truck_number: truckNumber, driver_name: document.getElementById('atDriver')?.value || '',
      driver_phone: document.getElementById('atPhone')?.value || '', type: document.getElementById('atType')?.value || 'Heavy',
      status: document.getElementById('atStatus')?.value || 'Available', current_location: 'Yard',
      assigned_container_id: null, gate_in_time: null, gate_out_time: null, created_at: new Date().toISOString()
    });
    document.getElementById('addTruckModal').remove();
    App.showToast(`Truck ${truckNumber} added`, 'success');
  },

  showAddAlertModal() {
    App.createModal({
      id: 'addAlertModal', title: 'New Security Alert', width: '500px',
      body: `<form id="addAlertForm" class="modal-form">
        <div class="form-group"><label>Title *</label><input type="text" id="aaTitle" class="form-control" placeholder="Alert title" required></div>
        <div class="form-group"><label>Description</label><textarea id="aaDesc" class="form-control" rows="3" placeholder="Alert details"></textarea></div>
        <div class="form-row"><div class="form-group"><label>Type</label><select id="aaType" class="form-select"><option>Security</option><option>Environmental</option><option>Maintenance</option><option>Operational</option></select></div><div class="form-group"><label>Severity</label><select id="aaSeverity" class="form-select"><option>Critical</option><option>Warning</option><option>Info</option></select></div></div>
      </form>`,
      footer: `<button class="btn btn-secondary" onclick="document.getElementById('addAlertModal').remove()">Cancel</button><button class="btn btn-primary" onclick="App.submitAddAlert()">Create Alert</button>`
    });
  },

  submitAddAlert() {
    const title = document.getElementById('aaTitle')?.value.trim();
    if (!title) { App.showToast('Title is required', 'danger'); return; }
    Store.add('alerts', {
      title, description: document.getElementById('aaDesc')?.value || '', type: document.getElementById('aaType')?.value || 'Security',
      severity: document.getElementById('aaSeverity')?.value || 'Info', status: 'Active', detected_at: new Date().toISOString(),
      resolved_at: null, detected_by: 'Manual Entry', zone: 'General', acknowledged: false
    });
    document.getElementById('addAlertModal').remove();
    App.showToast(`Alert "${title}" created`, 'success');
  },

  showAddScheduleModal() {
    App.createModal({
      id: 'addScheduleModal', title: 'New Maintenance Schedule', width: '500px',
      body: `<form id="addScheduleForm" class="modal-form">
        <div class="form-group"><label>Equipment *</label><input type="text" id="asEquipment" class="form-control" placeholder="Equipment name" required></div>
        <div class="form-row"><div class="form-group"><label>Type</label><select id="asType" class="form-select"><option>Preventive</option><option>Corrective</option><option>Inspection</option></select></div><div class="form-group"><label>Priority</label><select id="asPriority" class="form-select"><option>High</option><option>Medium</option><option>Low</option></select></div></div>
        <div class="form-group"><label>Scheduled Date</label><input type="datetime-local" id="asDate" class="form-control"></div>
      </form>`,
      footer: `<button class="btn btn-secondary" onclick="document.getElementById('addScheduleModal').remove()">Cancel</button><button class="btn btn-primary" onclick="App.submitAddSchedule()">Create Schedule</button>`
    });
  },

  submitAddSchedule() {
    const equipment = document.getElementById('asEquipment')?.value.trim();
    if (!equipment) { App.showToast('Equipment name is required', 'danger'); return; }
    Store.add('maintenance_schedules', {
      equipment, type: document.getElementById('asType')?.value || 'Preventive',
      priority: document.getElementById('asPriority')?.value || 'Medium',
      scheduled_date: document.getElementById('asDate')?.value || null,
      status: 'Scheduled', created_at: new Date().toISOString()
    });
    document.getElementById('addScheduleModal').remove();
    App.showToast(`Schedule for "${equipment}" created`, 'success');
  },
};

document.addEventListener('DOMContentLoaded', () => App.init());
