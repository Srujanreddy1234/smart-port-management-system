const API_BASE_URL = '/api/v1';

const ROLE_PERMISSIONS = {
  'Super Admin': ['all'],
  'Admin': [
    'users.read', 'users.write', 'users.delete',
    'roles.read', 'roles.write', 'roles.delete',
    'ships.read', 'ships.write', 'ships.delete',
    'containers.read', 'containers.write', 'containers.delete',
    'trucks.read', 'trucks.write', 'trucks.delete',
    'berths.read', 'berths.write', 'berths.delete',
    'dashboard.read', 'dashboard.write',
    'reports.read', 'reports.write', 'reports.delete',
    'maintenance.read', 'maintenance.write', 'maintenance.delete',
    'security.read', 'security.write', 'security.delete',
    'environment.read', 'environment.write', 'environment.delete',
    'audit.read', 'settings.read', 'settings.write',
    'gates.read', 'gates.book', 'gates.manage',
  ],
  'Port Supervisor': [
    'ships.read', 'ships.write',
    'containers.read', 'containers.write',
    'trucks.read', 'trucks.write',
    'berths.read', 'berths.write',
    'dashboard.read', 'reports.read', 'reports.write',
    'maintenance.read', 'maintenance.write',
    'security.read', 'security.write',
    'environment.read', 'audit.read',
    'gates.read', 'gates.book', 'gates.manage',
  ],
  'Port Staff': [
    'ships.read', 'ships.write',
    'containers.read', 'containers.write',
    'trucks.read', 'trucks.write',
    'berths.read',
    'dashboard.read', 'reports.read',
    'maintenance.read', 'maintenance.write',
    'security.read',
    'gates.read', 'gates.book', 'gates.manage',
  ],
  'Customs Officer': [
    'containers.read', 'containers.write',
    'trucks.read', 'ships.read',
    'dashboard.read', 'reports.read', 'security.read',
    'gates.read', 'gates.book',
  ],
  'Shipping Company': [
    'ships.read', 'containers.read', 'containers.write',
    'trucks.read', 'dashboard.read', 'reports.read', 'berths.read',
    'gates.read', 'gates.book',
  ],
  'Truck Operator': [
    'trucks.read', 'trucks.write',
    'containers.read', 'ships.read',
    'dashboard.read', 'reports.read',
    'gates.read', 'gates.book',
  ],
  'Customer': [
    'containers.read', 'ships.read',
    'dashboard.read', 'reports.read',
    'gates.read',
  ],
  'Public': [
    'ships.read', 'dashboard.read', 'gates.read',
  ],
};

const ROLE_DASHBOARDS = {
  'Super Admin': 'dashboard.html',
  'Admin': 'dashboard.html',
  'Port Supervisor': 'dashboard.html',
  'Port Staff': 'dashboard.html',
  'Customs Officer': 'dashboard.html',
  'Shipping Company': 'dashboard.html',
  'Truck Operator': 'dashboard.html',
  'Customer': 'dashboard.html',
  'Public': 'dashboard.html',
};

const ROLE_NAV_ITEMS = {
  'Super Admin': [
    { section: 'Main', items: [{ href: 'dashboard.html', icon: 'fa-th-large', label: 'Dashboard' }] },
    { section: 'Operations', items: [
      { href: 'ships.html', icon: 'fa-ship', label: 'Ship Management' },
      { href: 'containers.html', icon: 'fa-boxes-stacked', label: 'Container Ops' },
      { href: 'trucks.html', icon: 'fa-truck', label: 'Truck Operations' },
      { href: 'berths.html', icon: 'fa-anchor', label: 'Berth Management' },
      { href: 'gates.html', icon: 'fa-route', label: 'Gate Routing' },
    ]},
    { section: 'Management', items: [
      { href: 'security.html', icon: 'fa-shield-halved', label: 'Security Center' },
      { href: 'maintenance.html', icon: 'fa-wrench', label: 'Equipment Maint.' },
      { href: 'environment.html', icon: 'fa-leaf', label: 'Environmental' },
    ]},
    { section: 'Analytics', items: [
      { href: 'reports.html', icon: 'fa-chart-line', label: 'Reports & Analytics' },
    ]},
    { section: 'Billing', items: [
      { href: 'billing.html', icon: 'fa-file-invoice-dollar', label: 'Billing & Invoices' },
    ]},
    { section: 'Administration', items: [
      { href: 'admin.html', icon: 'fa-user-shield', label: 'Admin Panel' },
      { href: 'profile.html', icon: 'fa-user-circle', label: 'User Profile' },
    ]},
  ],
  'Admin': [
    { section: 'Main', items: [{ href: 'dashboard.html', icon: 'fa-th-large', label: 'Dashboard' }] },
    { section: 'Operations', items: [
      { href: 'ships.html', icon: 'fa-ship', label: 'Ship Management' },
      { href: 'containers.html', icon: 'fa-boxes-stacked', label: 'Container Ops' },
      { href: 'trucks.html', icon: 'fa-truck', label: 'Truck Operations' },
      { href: 'berths.html', icon: 'fa-anchor', label: 'Berth Management' },
      { href: 'gates.html', icon: 'fa-route', label: 'Gate Routing' },
    ]},
    { section: 'Management', items: [
      { href: 'security.html', icon: 'fa-shield-halved', label: 'Security Center' },
      { href: 'maintenance.html', icon: 'fa-wrench', label: 'Equipment Maint.' },
      { href: 'environment.html', icon: 'fa-leaf', label: 'Environmental' },
    ]},
    { section: 'Analytics', items: [
      { href: 'reports.html', icon: 'fa-chart-line', label: 'Reports & Analytics' },
    ]},
    { section: 'Billing', items: [
      { href: 'billing.html', icon: 'fa-file-invoice-dollar', label: 'Billing & Invoices' },
    ]},
    { section: 'Administration', items: [
      { href: 'admin.html', icon: 'fa-user-shield', label: 'Admin Panel' },
      { href: 'profile.html', icon: 'fa-user-circle', label: 'User Profile' },
    ]},
  ],
  'Port Supervisor': [
    { section: 'Main', items: [{ href: 'dashboard.html', icon: 'fa-th-large', label: 'Dashboard' }] },
    { section: 'Operations', items: [
      { href: 'ships.html', icon: 'fa-ship', label: 'Ship Management' },
      { href: 'containers.html', icon: 'fa-boxes-stacked', label: 'Container Ops' },
      { href: 'trucks.html', icon: 'fa-truck', label: 'Truck Operations' },
      { href: 'berths.html', icon: 'fa-anchor', label: 'Berth Management' },
      { href: 'gates.html', icon: 'fa-route', label: 'Gate Routing' },
    ]},
    { section: 'Management', items: [
      { href: 'security.html', icon: 'fa-shield-halved', label: 'Security Center' },
      { href: 'maintenance.html', icon: 'fa-wrench', label: 'Equipment Maint.' },
    ]},
    { section: 'Analytics', items: [
      { href: 'reports.html', icon: 'fa-chart-line', label: 'Reports' },
    ]},
    { section: 'Billing', items: [
      { href: 'billing.html', icon: 'fa-file-invoice-dollar', label: 'Billing & Invoices' },
    ]},
    { section: 'Account', items: [
      { href: 'profile.html', icon: 'fa-user-circle', label: 'Profile' },
    ]},
  ],
  'Port Staff': [
    { section: 'Main', items: [{ href: 'dashboard.html', icon: 'fa-th-large', label: 'Dashboard' }] },
    { section: 'Operations', items: [
      { href: 'ships.html', icon: 'fa-ship', label: 'Ships' },
      { href: 'containers.html', icon: 'fa-boxes-stacked', label: 'Containers' },
      { href: 'trucks.html', icon: 'fa-truck', label: 'Trucks' },
      { href: 'berths.html', icon: 'fa-anchor', label: 'Berths' },
      { href: 'gates.html', icon: 'fa-route', label: 'Gate Routing' },
    ]},
    { section: 'Management', items: [
      { href: 'maintenance.html', icon: 'fa-wrench', label: 'Maintenance' },
    ]},
    { section: 'Account', items: [
      { href: 'profile.html', icon: 'fa-user-circle', label: 'Profile' },
    ]},
  ],
  'Customs Officer': [
    { section: 'Main', items: [{ href: 'dashboard.html', icon: 'fa-th-large', label: 'Dashboard' }] },
    { section: 'Customs', items: [
      { href: 'containers.html', icon: 'fa-boxes-stacked', label: 'Containers' },
      { href: 'ships.html', icon: 'fa-ship', label: 'Ships' },
      { href: 'trucks.html', icon: 'fa-truck', label: 'Trucks' },
      { href: 'gates.html', icon: 'fa-route', label: 'Gate Routing' },
    ]},
    { section: 'Account', items: [
      { href: 'profile.html', icon: 'fa-user-circle', label: 'Profile' },
    ]},
  ],
  'Shipping Company': [
    { section: 'Main', items: [{ href: 'dashboard.html', icon: 'fa-th-large', label: 'Dashboard' }] },
    { section: 'My Operations', items: [
      { href: 'ships.html', icon: 'fa-ship', label: 'My Ships' },
      { href: 'containers.html', icon: 'fa-boxes-stacked', label: 'My Containers' },
      { href: 'berths.html', icon: 'fa-anchor', label: 'Berth Status' },
      { href: 'gates.html', icon: 'fa-route', label: 'Gate Routing' },
    ]},
    { section: 'Account', items: [
      { href: 'profile.html', icon: 'fa-user-circle', label: 'Profile' },
    ]},
  ],
  'Truck Operator': [
    { section: 'Main', items: [{ href: 'dashboard.html', icon: 'fa-th-large', label: 'Dashboard' }] },
    { section: 'My Operations', items: [
      { href: 'gates.html', icon: 'fa-route', label: 'Gate Routing & Slots' },
      { href: 'trucks.html', icon: 'fa-truck', label: 'My Trucks' },
      { href: 'containers.html', icon: 'fa-boxes-stacked', label: 'Containers' },
      { href: 'ships.html', icon: 'fa-ship', label: 'Vessels' },
    ]},
    { section: 'Account', items: [
      { href: 'profile.html', icon: 'fa-user-circle', label: 'Profile' },
    ]},
  ],
  'Customer': [
    { section: 'Main', items: [{ href: 'dashboard.html', icon: 'fa-th-large', label: 'Dashboard' }] },
    { section: 'My Shipments', items: [
      { href: 'containers.html', icon: 'fa-boxes-stacked', label: 'Containers' },
      { href: 'ships.html', icon: 'fa-ship', label: 'Vessels' },
      { href: 'gates.html', icon: 'fa-route', label: 'Gate Routing' },
    ]},
    { section: 'Account', items: [
      { href: 'profile.html', icon: 'fa-user-circle', label: 'Profile' },
    ]},
  ],
  'Public': [
    { section: 'Main', items: [
      { href: 'dashboard.html', icon: 'fa-th-large', label: 'Dashboard' },
      { href: 'ships.html', icon: 'fa-ship', label: 'Ship Tracker' },
      { href: 'gates.html', icon: 'fa-route', label: 'Gate Routing' },
    ]},
  ],
};

const Api = {
  getToken() {
    return localStorage.getItem('access_token');
  },

  setSession(data) {
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
  },

  clearSession() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  getUser() {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  },

  setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
  },

  async updateProfile(payload) {
    const res = await this.request('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
    if (res.data) {
      this.setUser(res.data);
    }
    return res;
  },

  getUserRole() {
    const user = this.getUser();
    return user ? user.role : null;
  },

  hasPermission(permission) {
    const role = this.getUserRole();
    if (!role) return false;
    const permissions = ROLE_PERMISSIONS[role] || [];
    if (permissions.includes('all')) return true;
    return permissions.includes(permission);
  },

  hasAnyPermission(permissions) {
    return permissions.some(p => this.hasPermission(p));
  },

  canAccessModule(module) {
    return this.hasPermission(`${module}.read`);
  },

  getRoleNavItems() {
    const role = this.getUserRole();
    return ROLE_NAV_ITEMS[role] || ROLE_NAV_ITEMS['Public'];
  },

  async request(path, options = {}, _isRetry = false) {
    const token = this.getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    };

    let response;
    try {
      response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
    } catch (err) {
      // Network-level failure (server unreachable, DNS, offline, or the
      // brief window a free-tier instance is mid-restart). One silent
      // retry after a short pause covers that transient case instead of
      // pages permanently showing blank data on a single hiccup.
      if (!_isRetry) {
        await new Promise(r => setTimeout(r, 1200));
        return this.request(path, options, true);
      }
      if (typeof App !== 'undefined' && App.showToast) {
        App.showToast('Connection issue reaching the server. Please try again.', 'danger');
      }
      throw new Error('Server unreachable. Please check your connection.');
    }

    // 502/503/504 from the platform proxy (e.g. a transient restart) --
    // same one-time-retry treatment as a network failure.
    if ([502, 503, 504].includes(response.status) && !_isRetry) {
      await new Promise(r => setTimeout(r, 1200));
      return this.request(path, options, true);
    }

    const body = await response.json().catch(() => ({}));

    if (response.status === 401) {
      this.clearSession();
      window.location.href = 'login.html';
      throw new Error(body.message || 'Session expired');
    }

    if (!response.ok) {
      if ([502, 503, 504].includes(response.status) && typeof App !== 'undefined' && App.showToast) {
        App.showToast('The server was briefly unavailable -- some data may be incomplete. Try refreshing.', 'warning');
      }
      const error = new Error(body.message || 'Request failed');
      // Carry the backend's per-field validation messages (either shape
      // it uses -- {errors:{field:[...]}} or {details:{field:[...]}})
      // so callers can highlight the exact invalid field instead of only
      // showing a generic toast.
      error.fieldErrors = body.errors || body.details || null;
      error.status = response.status;
      throw error;
    }

    return body;
  },

  login(email, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  },

  register(payload) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  forgotPassword(email) {
    return this.request('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email })
    });
  },

  resetPassword(token, password, confirmPassword) {
    return this.request('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, password, confirm_password: confirmPassword })
    });
  },

  requireAuth() {
    if (!this.getToken()) {
      window.location.href = 'login.html';
      return false;
    }
    return true;
  },

  requirePermission(permission) {
    if (!this.hasPermission(permission)) {
      if (typeof App !== 'undefined' && App.showToast) {
        App.showToast('You do not have permission to access this page', 'danger');
      }
      window.location.href = 'dashboard.html';
      return false;
    }
    return true;
  },

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } catch (e) {
      // ignore, clearing local session regardless
    }
    this.clearSession();
    window.location.href = 'login.html';
  }
};

const NO_AUTH_PAGES = ['login.html', 'oauth-callback.html', 'signup.html'];
(function () {
  // Scoped to this IIFE rather than a bare top-level const: several pages
  // (ships/containers/trucks/security/maintenance) declare their own
  // page-local `currentPage` for pagination state in a separate <script>
  // tag. Classic <script> tags share one global lexical scope, so a
  // top-level `const currentPage` here previously collided with those and
  // threw "Identifier 'currentPage' has already been declared" -- a
  // SyntaxError that silently killed each of those pages' entire inline
  // script (no listeners wired, no data ever rendered).
  const currentPageFile = window.location.pathname.split('/').pop() || 'dashboard.html';
  if (!NO_AUTH_PAGES.some(p => currentPageFile.endsWith(p))) {
    Api.requireAuth();
  }
})();
