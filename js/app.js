const App = {
  async init() {
    if (!Api.requireAuth()) return;
    await ApiStore.init();
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

    const fullscreenBtn = document.querySelector('.topbar-btn .fa-expand');
    if (fullscreenBtn) {
      const btn = fullscreenBtn.closest('.topbar-btn');
      if (btn) {
        btn.addEventListener('click', () => {
          if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(() => {});
          } else {
            document.exitFullscreen().catch(() => {});
          }
        });
      }
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
      this._sseConnection = new EventSource(`${API_BASE_URL}/events/stream?token=${encodeURIComponent(token)}`);
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
        <div class="form-group"><label>Employee ID</label><input type="text" id="epEmployeeId" class="form-control" value="${user.employee_id || ''}" readonly title="Employee ID is managed by an administrator"></div>
      </form>`,
      footer: `<button class="btn btn-secondary" onclick="document.getElementById('editProfileModal').remove()">Cancel</button><button class="btn btn-primary" onclick="App.saveProfile()">Save Changes</button>`
    });
  },

  async saveProfile() {
    const user = Store.getUser();
    if (!user) return;
    const payload = {
      first_name: document.getElementById('epFirstName')?.value || user.first_name,
      phone: document.getElementById('epPhone')?.value || user.phone,
      department: document.getElementById('epDepartment')?.value || user.department,
      designation: document.getElementById('epDesignation')?.value || user.designation,
    };
    try {
      await Api.updateProfile(payload);
      document.getElementById('editProfileModal').remove();
      App.initUserDisplay();
      App.showToast('Profile updated successfully', 'success');
    } catch (err) {
      App.showToast(err.message || 'Failed to update profile', 'danger');
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
  },

  // Marks a single form field as invalid: red border on the input plus
  // an inline message right under it, instead of only a toast the user
  // has to connect back to which field caused it.
  showFieldError(inputId, message) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.classList.add('is-invalid');
    let feedback = input.nextElementSibling;
    if (!feedback || !feedback.classList.contains('field-invalid-feedback')) {
      feedback = document.createElement('div');
      feedback.className = 'field-invalid-feedback';
      input.insertAdjacentElement('afterend', feedback);
    }
    feedback.innerHTML = `<i class="fas fa-circle-exclamation"></i> ${message}`;
    feedback.classList.add('show');
  },

  clearFieldError(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.classList.remove('is-invalid');
    const feedback = input.nextElementSibling;
    if (feedback && feedback.classList.contains('field-invalid-feedback')) {
      feedback.classList.remove('show');
    }
  },

  clearFormErrors(formEl) {
    if (!formEl) return;
    formEl.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    formEl.querySelectorAll('.field-invalid-feedback.show').forEach(el => el.classList.remove('show'));
  },

  // Maps a backend { success:false, message, errors|details: { field: [...] } }
  // validation response onto the matching input(s) by id, falling back to
  // a toast for anything that isn't a per-field message (e.g. a plain
  // "Ship ID already exists" conflict, or a field the form doesn't render).
  applyFieldErrors(formEl, err, fieldIdMap) {
    const fieldErrors = (err && (err.fieldErrors || err.errors || err.details)) || null;
    if (!fieldErrors || typeof fieldErrors !== 'object') {
      App.showToast((err && err.message) || 'Please check the form and try again', 'danger');
      return;
    }
    let anyMapped = false;
    for (const [field, messages] of Object.entries(fieldErrors)) {
      const inputId = (fieldIdMap && fieldIdMap[field]) || field;
      const input = document.getElementById(inputId);
      const message = Array.isArray(messages) ? messages[0] : String(messages);
      if (input) {
        App.showFieldError(inputId, message);
        anyMapped = true;
      }
    }
    if (!anyMapped) {
      App.showToast((err && err.message) || 'Please check the form and try again', 'danger');
    }
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
  exportShips() { App.exportCSV(Store.get('ships'), 'ships-export.csv'); App.showToast('Ships exported', 'success'); },
  exportContainers() { App.exportCSV(Store.get('containers'), 'containers-export.csv'); App.showToast('Containers exported', 'success'); },
  exportBerths() { App.exportCSV(Store.get('berths'), 'berths-export.csv'); App.showToast('Berths exported', 'success'); },
  exportInvoices() { App.exportCSV(Store.get('invoices'), 'invoices-export.csv'); App.showToast('Invoices exported', 'success'); },
  exportAlerts() { App.exportCSV(Store.get('alerts'), 'alerts-export.csv'); App.showToast('Alerts exported', 'success'); },
  exportUsers() { App.exportCSV(Store.get('users'), 'users-export.csv'); App.showToast('Users exported', 'success'); },
  exportMaintenance() { App.exportCSV(Store.get('maintenance_schedules'), 'maintenance-export.csv'); App.showToast('Maintenance exported', 'success'); },
  exportEnvironment() { App.exportCSV(Store.get('env_readings') || [], 'environment-export.csv'); App.showToast('Environment data exported', 'success'); },
  exportReports() { App.exportCSV(Store.get('reports'), 'reports-export.csv'); App.showToast('Reports exported', 'success'); },
  exportActivity() { App.exportCSV(Store.get('activity_log'), 'activity-export.csv'); App.showToast('Activity log exported', 'success'); },

  showAddTruckModal() {
    App.createModal({
      id: 'addTruckModal', title: 'Add New Truck', width: '500px',
      body: `<form id="addTruckForm" class="modal-form">
        <div class="form-group"><label>Truck Number *</label><input type="text" id="atTruckNumber" class="form-control" placeholder="TN-2001" style="text-transform:uppercase;" oninput="this.value = this.value.toUpperCase(); App.clearFieldError('atTruckNumber');" required></div>
        <div class="form-row"><div class="form-group"><label>Driver Name</label><input type="text" id="atDriver" class="form-control" placeholder="Driver name"></div><div class="form-group"><label>Phone</label><input type="tel" id="atPhone" class="form-control" placeholder="+91 98765 43210" oninput="App.clearFieldError('atPhone');"></div></div>
        <div class="form-row"><div class="form-group"><label>Type</label><select id="atType" class="form-select"><option value="Prime Mover">Prime Mover</option><option value="Trailer">Trailer</option><option value="Chassis">Chassis</option><option value="Reach Stacker">Reach Stacker</option><option value="Forklift">Forklift</option><option value="Empty Handler">Empty Handler</option><option value="Other">Other</option></select></div><div class="form-group"><label>Status</label><select id="atStatus" class="form-select"><option value="Available">Available</option><option value="At Gate">At Gate</option><option value="Loading">Loading</option><option value="Unloading">Unloading</option><option value="In Transit">In Transit</option><option value="Waiting">Waiting</option><option value="Maintenance">Maintenance</option></select></div></div>
      </form>`,
      footer: `<button class="btn btn-secondary" onclick="document.getElementById('addTruckModal').remove()">Cancel</button><button class="btn btn-primary" onclick="App.submitAddTruck()">Add Truck</button>`
    });
  },

  async submitAddTruck() {
    const form = document.getElementById('addTruckForm');
    App.clearFormErrors(form);
    const truckNumber = document.getElementById('atTruckNumber')?.value.trim().toUpperCase();
    const driverPhone = document.getElementById('atPhone')?.value.trim();
    if (!truckNumber) { App.showFieldError('atTruckNumber', 'Truck number is required'); return; }
    if (!/^[A-Z][A-Z0-9-]{2,49}$/.test(truckNumber)) {
      App.showFieldError('atTruckNumber', 'Uppercase letters, numbers, and hyphens only, e.g. TN-2001');
      return;
    }
    if (driverPhone && !/^\+?[\d\s-]{7,20}$/.test(driverPhone)) {
      App.showFieldError('atPhone', 'Enter a valid phone number');
      return;
    }
    const payload = {
      truck_number: truckNumber,
      truck_type: document.getElementById('atType')?.value || 'Other',
      status: document.getElementById('atStatus')?.value || 'Available',
      current_location: 'Yard',
    };
    const driverName = document.getElementById('atDriver')?.value.trim();
    if (driverName) payload.driver_name = driverName;
    if (driverPhone) payload.driver_phone = driverPhone;

    try {
      await Api.request('/trucks', { method: 'POST', body: JSON.stringify(payload) });
      document.getElementById('addTruckModal').remove();
      App.showToast(`Truck ${truckNumber} added`, 'success');
      if (typeof loadTrucks === 'function') loadTrucks();
      if (typeof loadTruckKpis === 'function') loadTruckKpis();
    } catch (err) {
      if (/truck number.*already exists/i.test(err.message || '')) {
        App.showFieldError('atTruckNumber', err.message);
        return;
      }
      if (/license plate.*already exists/i.test(err.message || '')) {
        App.showToast(err.message, 'danger');
        return;
      }
      App.applyFieldErrors(form, err, {
        truck_number: 'atTruckNumber', driver_name: 'atDriver', driver_phone: 'atPhone',
        truck_type: 'atType', status: 'atStatus',
      });
    }
  },

  showReportIncidentModal() {
    App.createModal({
      id: 'addAlertModal', title: 'Report Security Incident', width: '500px',
      body: `<form id="addAlertForm" class="modal-form">
        <div class="form-group"><label>Title *</label><input type="text" id="aaTitle" class="form-control" placeholder="Incident title" oninput="App.clearFieldError('aaTitle');" required></div>
        <div class="form-group"><label>Description</label><textarea id="aaDesc" class="form-control" rows="3" placeholder="Incident details"></textarea></div>
        <div class="form-row"><div class="form-group"><label>Type</label><select id="aaType" class="form-select"><option value="Intrusion">Intrusion</option><option value="Perimeter Breach">Perimeter Breach</option><option value="Access Denied">Access Denied</option><option value="Suspicious Activity">Suspicious Activity</option><option value="Violation">Violation</option><option value="Theft">Theft</option><option value="Vandalism">Vandalism</option><option value="Fire">Fire</option><option value="Hazmat Incident">Hazmat Incident</option><option value="Other">Other</option></select></div><div class="form-group"><label>Severity</label><select id="aaSeverity" class="form-select"><option value="Medium">Medium</option><option value="Low">Low</option><option value="High">High</option><option value="Critical">Critical</option></select></div></div>
        <div class="form-group"><label>Zone *</label><select id="aaZone" class="form-select"><option value="Zone A - Berth 1-3">Zone A - Berth 1-3</option><option value="Zone B - Berth 4-6">Zone B - Berth 4-6</option><option value="Zone C - Gate 1-2">Zone C - Gate 1-2</option><option value="Zone D - Warehouse Row">Zone D - Warehouse Row</option><option value="Zone E - Tank Farm">Zone E - Tank Farm</option><option value="Zone F - Admin Area">Zone F - Admin Area</option><option value="Zone G - Cold Storage">Zone G - Cold Storage</option><option value="Zone H - Container Yard">Zone H - Container Yard</option></select></div>
      </form>`,
      footer: `<button class="btn btn-secondary" onclick="document.getElementById('addAlertModal').remove()">Cancel</button><button class="btn btn-primary" onclick="App.submitReportIncident()">Report Incident</button>`
    });
  },

  async submitReportIncident() {
    const form = document.getElementById('addAlertForm');
    App.clearFormErrors(form);
    const title = document.getElementById('aaTitle')?.value.trim();
    if (!title) { App.showFieldError('aaTitle', 'Title is required'); return; }
    const description = document.getElementById('aaDesc')?.value.trim();
    const payload = {
      incident_id: `INC-${Date.now()}`,
      title,
      incident_type: document.getElementById('aaType')?.value || 'Other',
      severity: document.getElementById('aaSeverity')?.value || 'Medium',
      zone: document.getElementById('aaZone')?.value || 'Zone A - Berth 1-3',
      status: 'Active',
    };
    if (description) payload.description = description;

    try {
      await Api.request('/security', { method: 'POST', body: JSON.stringify(payload) });
      document.getElementById('addAlertModal').remove();
      App.showToast(`Incident "${title}" reported`, 'success');
      if (typeof loadIncidents === 'function') loadIncidents();
    } catch (err) {
      App.applyFieldErrors(form, err, {
        title: 'aaTitle', description: 'aaDesc', incident_type: 'aaType',
        severity: 'aaSeverity', zone: 'aaZone',
      });
    }
  },

  async showAddScheduleModal() {
    App.createModal({
      id: 'addScheduleModal', title: 'New Maintenance Schedule', width: '500px',
      body: `<form id="addScheduleForm" class="modal-form">
        <div class="form-group"><label>Title *</label><input type="text" id="asTitle" class="form-control" placeholder="e.g. Quarterly crane inspection" required></div>
        <div class="form-group"><label>Equipment *</label><select id="asEquipment" class="form-select" required><option value="">Loading equipment...</option></select></div>
        <div class="form-row"><div class="form-group"><label>Type</label><select id="asType" class="form-select"><option value="Preventive">Preventive</option><option value="Corrective">Corrective</option><option value="Predictive">Predictive</option><option value="Emergency">Emergency</option><option value="Overhaul">Overhaul</option><option value="Inspection">Inspection</option><option value="Calibration">Calibration</option></select></div><div class="form-group"><label>Priority</label><select id="asPriority" class="form-select"><option value="Medium">Medium</option><option value="Low">Low</option><option value="High">High</option><option value="Critical">Critical</option></select></div></div>
        <div class="form-group"><label>Scheduled Date *</label><input type="datetime-local" id="asDate" class="form-control" required></div>
      </form>`,
      footer: `<button class="btn btn-secondary" onclick="document.getElementById('addScheduleModal').remove()">Cancel</button><button class="btn btn-primary" onclick="App.submitAddSchedule()">Create Schedule</button>`
    });
    try {
      const res = await Api.request('/maintenance?page=1&per_page=100');
      const equipment = res.data.items || [];
      const select = document.getElementById('asEquipment');
      if (select) {
        select.innerHTML = equipment.length
          ? equipment.map(e => `<option value="${e.id}">${e.name || e.equipment_id}</option>`).join('')
          : '<option value="">No equipment found</option>';
      }
    } catch (err) {
      const select = document.getElementById('asEquipment');
      if (select) select.innerHTML = '<option value="">Failed to load equipment</option>';
    }
  },

  async submitAddSchedule() {
    const form = document.getElementById('addScheduleForm');
    App.clearFormErrors(form);
    const title = document.getElementById('asTitle')?.value.trim();
    const equipmentId = document.getElementById('asEquipment')?.value;
    const scheduledDate = document.getElementById('asDate')?.value;
    let hasError = false;
    if (!title) { App.showFieldError('asTitle', 'Title is required'); hasError = true; }
    if (!equipmentId) { App.showFieldError('asEquipment', 'Equipment is required'); hasError = true; }
    if (!scheduledDate) { App.showFieldError('asDate', 'Scheduled date is required'); hasError = true; }
    if (hasError) return;
    try {
      await Api.request('/maintenance/schedules', {
        method: 'POST',
        body: JSON.stringify({
          title,
          equipment_id: parseInt(equipmentId, 10),
          maintenance_type: document.getElementById('asType')?.value || 'Preventive',
          priority: document.getElementById('asPriority')?.value || 'Medium',
          scheduled_date: new Date(scheduledDate).toISOString(),
          status: 'Scheduled',
        })
      });
      document.getElementById('addScheduleModal').remove();
      App.showToast(`Schedule "${title}" created`, 'success');
      if (typeof loadSchedule === 'function') loadSchedule();
    } catch (err) {
      App.applyFieldErrors(form, err, {
        title: 'asTitle', equipment_id: 'asEquipment', maintenance_type: 'asType',
        priority: 'asPriority', scheduled_date: 'asDate',
      });
    }
  },
};

document.addEventListener('DOMContentLoaded', () => App.init());
