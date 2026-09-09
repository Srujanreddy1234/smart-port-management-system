const API_BASE_URL = '/api/v1';

const MOCK_USERS = {
  'admin@smartport.gov.in': { password: 'admin123', role: 'Super Admin', role_raw: 'SUPER_ADMIN', first_name: 'Super', last_name: 'Admin', email: 'admin@smartport.gov.in', department: 'IT', designation: 'Super Administrator', employee_id: 'ADMIN001', phone: '+1-555-0100', id: 1 },
  'admin2@smartport.gov.in': { password: 'admin123', role: 'Admin', role_raw: 'ADMIN', first_name: 'Admin', last_name: 'User', email: 'admin2@smartport.gov.in', department: 'Operations', designation: 'Operations Manager', employee_id: 'OPS001', phone: '+1-555-0101', id: 2 },
  'supervisor@smartport.gov.in': { password: 'admin123', role: 'Port Supervisor', role_raw: 'PORT_SUPERVISOR', first_name: 'Port', last_name: 'Supervisor', email: 'supervisor@smartport.gov.in', department: 'Operations', designation: 'Port Supervisor', employee_id: 'SUP001', phone: '+1-555-0102', id: 3 },
  'staff@smartport.gov.in': { password: 'admin123', role: 'Port Staff', role_raw: 'PORT_STAFF', first_name: 'Port', last_name: 'Staff', email: 'staff@smartport.gov.in', department: 'Operations', designation: 'Operations Officer', employee_id: 'OPS002', phone: '+1-555-0103', id: 4 },
  'customs@smartport.gov.in': { password: 'admin123', role: 'Customs Officer', role_raw: 'CUSTOMS_OFFICER', first_name: 'Customs', last_name: 'Officer', email: 'customs@smartport.gov.in', department: 'Customs', designation: 'Customs Officer', employee_id: 'CUS001', phone: '+1-555-0104', id: 5 },
  'shipping@smartport.gov.in': { password: 'admin123', role: 'Shipping Company', role_raw: 'SHIPPING_COMPANY', first_name: 'Shipping', last_name: 'Agent', email: 'shipping@smartport.gov.in', department: 'Operations', designation: 'Shipping Agent', employee_id: 'SHA001', phone: '+1-555-0105', id: 6 },
  'truck@smartport.gov.in': { password: 'admin123', role: 'Truck Operator', role_raw: 'TRUCK_OPERATOR', first_name: 'Truck', last_name: 'Driver', email: 'truck@smartport.gov.in', department: 'Logistics', designation: 'Truck Driver', employee_id: 'TRK001', phone: '+1-555-0106', id: 7 },
  'customer@smartport.gov.in': { password: 'admin123', role: 'Customer', role_raw: 'CUSTOMER', first_name: 'Customer', last_name: 'User', email: 'customer@smartport.gov.in', department: 'Sales', designation: 'Account Manager', employee_id: 'CUS002', phone: '+1-555-0107', id: 8 },
};

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
  ],
  'Port Staff': [
    'ships.read', 'ships.write',
    'containers.read', 'containers.write',
    'trucks.read', 'trucks.write',
    'berths.read',
    'dashboard.read', 'reports.read',
    'maintenance.read', 'maintenance.write',
    'security.read',
  ],
  'Customs Officer': [
    'containers.read', 'containers.write',
    'trucks.read', 'ships.read',
    'dashboard.read', 'reports.read', 'security.read',
  ],
  'Shipping Company': [
    'ships.read', 'containers.read', 'containers.write',
    'trucks.read', 'dashboard.read', 'reports.read', 'berths.read',
  ],
  'Truck Operator': [
    'trucks.read', 'trucks.write',
    'containers.read', 'ships.read',
    'dashboard.read', 'reports.read',
  ],
  'Customer': [
    'containers.read', 'ships.read',
    'dashboard.read', 'reports.read',
  ],
  'Public': [
    'ships.read', 'dashboard.read',
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
  'super Admin': [
    { section: 'Main', items: [{ href: 'dashboard.html', icon: 'fa-th-large', label: 'Dashboard' }] },
    { section: 'Operations', items: [
      { href: 'ships.html', icon: 'fa-ship', label: 'Ship Management' },
      { href: 'containers.html', icon: 'fa-boxes-stacked', label: 'Container Ops' },
      { href: 'trucks.html', icon: 'fa-truck', label: 'Truck Operations' },
      { href: 'berths.html', icon: 'fa-anchor', label: 'Berth Management' },
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
    ]},
    { section: 'Account', items: [
      { href: 'profile.html', icon: 'fa-user-circle', label: 'Profile' },
    ]},
  ],
  'Truck Operator': [
    { section: 'Main', items: [{ href: 'dashboard.html', icon: 'fa-th-large', label: 'Dashboard' }] },
    { section: 'My Operations', items: [
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
    ]},
    { section: 'Account', items: [
      { href: 'profile.html', icon: 'fa-user-circle', label: 'Profile' },
    ]},
  ],
  'Public': [
    { section: 'Main', items: [
      { href: 'dashboard.html', icon: 'fa-th-large', label: 'Dashboard' },
      { href: 'ships.html', icon: 'fa-ship', label: 'Ship Tracker' },
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

  async request(path, options = {}) {
    const token = this.getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    };

    try {
      const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
      const body = await response.json().catch(() => ({}));

      if (response.status === 401) {
        this.clearSession();
        window.location.href = 'login.html';
        throw new Error(body.message || 'Session expired');
      }

      if (!response.ok) {
        throw new Error(body.message || 'Request failed');
      }

      return body;
    } catch (err) {
      if (err.message === 'Failed to fetch') {
        throw new Error('Server unreachable. Please check your connection.');
      }
      throw err;
    }
  },

  login(email, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    }).catch(err => {
      const mockUser = MOCK_USERS[email];
      if (mockUser && mockUser.password === password) {
        const token = 'mock_' + btoa(JSON.stringify({ email, role: mockUser.role, exp: Date.now() + 7200000 }));
        return {
          data: {
            access_token: token,
            refresh_token: 'mock_refresh',
            user: { ...mockUser, full_name: mockUser.first_name + ' ' + mockUser.last_name, must_change_password: false, two_factor_enabled: false, email_verified: true }
          }
        };
      }
      throw err;
    });
  },

  register(payload) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload)
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
const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
if (!NO_AUTH_PAGES.some(p => currentPage.endsWith(p))) {
  Api.requireAuth();
}
