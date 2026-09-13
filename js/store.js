const Store = {
  _prefix: 'spm_',

  _get(key) {
    if (ApiStore && ApiStore._cache && ApiStore._cache[key]) {
      return ApiStore._cache[key];
    }
    try {
      const raw = localStorage.getItem(this._prefix + key);
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  },

  _set(key, value) {
    localStorage.setItem(this._prefix + key, JSON.stringify(value));
  },

  get(key) {
    if (ApiStore && ApiStore._cache && ApiStore._cache[key]) {
      return ApiStore._cache[key];
    }
    const fallback = this._get(key);
    return fallback || [];
  },

  set(key, value) {
    if (ApiStore) {
      ApiStore.set(key, value);
    } else {
      this._set(key, value);
    }
  },

  add(key, item) {
    const arr = this.get(key);
    item.id = item.id || Date.now();
    item.created_at = item.created_at || new Date().toISOString();
    arr.push(item);
    this.set(key, arr);
    if (ApiStore && ApiStore.add) {
      ApiStore.add(key, item).catch(() => {});
    }
    return item;
  },

  update(key, id, updates) {
    const arr = this.get(key);
    const idx = arr.findIndex(item => item.id == id);
    if (idx === -1) return null;
    arr[idx] = { ...arr[idx], ...updates, updated_at: new Date().toISOString() };
    this.set(key, arr);
    if (ApiStore && ApiStore.update) {
      ApiStore.update(key, id, updates).catch(() => {});
    }
    return arr[idx];
  },

  remove(key, id) {
    const arr = this.get(key);
    const filtered = arr.filter(item => item.id != id);
    this.set(key, filtered);
    if (ApiStore && ApiStore.remove) {
      ApiStore.remove(key, id).catch(() => {});
    }
    return filtered;
  },

  getById(key, id) {
    return this.get(key).find(item => item.id == id) || null;
  },

  init() {
    if (ApiStore && ApiStore.init) {
      return ApiStore.init();
    }
    if (!this._get('initialized')) {
      this._seed();
      this._set('initialized', true);
    }
  },

  _seed() {
    this._set('user', {
      id: 1, first_name: 'Super', last_name: 'Admin', email: 'superadmin@smartport.gov.in',
      role: 'Super Admin', role_raw: 'SUPER_ADMIN', department: 'IT', designation: 'Super Administrator',
      employee_id: 'ADMIN001', phone: '+1-555-0100', avatar_url: null, status: 'active',
      created_at: new Date().toISOString()
    });
    this._set('ships', []);
    this._set('containers', []);
    this._set('trucks', []);
    this._set('berths', []);
    this._set('invoices', []);
    this._set('billing_lines', []);
    this._set('users', []);
    this._set('alerts', []);
    this._set('activity_log', []);
    this._set('env_readings', {});
  },

  getShipStats() {
    if (ApiStore && ApiStore.getShipStats) return ApiStore.getShipStats();
    const ships = this.get('ships');
    const byStatus = {};
    ships.forEach(s => { byStatus[s.status] = (byStatus[s.status] || 0) + 1; });
    return { total: ships.length, by_status: byStatus };
  },

  getContainerStats() {
    if (ApiStore && ApiStore.getContainerStats) return ApiStore.getContainerStats();
    const containers = this.get('containers');
    const byStatus = {};
    const byType = {};
    containers.forEach(c => {
      byStatus[c.status] = (byStatus[c.status] || 0) + 1;
      byType[c.type_category || c.type] = (byType[c.type_category || c.type] || 0) + 1;
    });
    return { total: containers.length, by_status: byStatus, by_type: byType, loaded: byStatus['Delivered'] || 0 };
  },

  getTruckStats() {
    if (ApiStore && ApiStore.getTruckStats) return ApiStore.getTruckStats();
    const trucks = this.get('trucks');
    const byStatus = {};
    trucks.forEach(t => { byStatus[t.status] = (byStatus[t.status] || 0) + 1; });
    return { total: trucks.length, by_status: byStatus };
  },

  getBerthStats() {
    if (ApiStore && ApiStore.getBerthStats) return ApiStore.getBerthStats();
    const berths = this.get('berths');
    const byStatus = {};
    berths.forEach(b => { byStatus[b.status] = (byStatus[b.status] || 0) + 1; });
    const occupied = byStatus['Occupied'] || 0;
    return { total: berths.length, occupied, available: byStatus['Available'] || 0, maintenance: byStatus['Maintenance'] || 0, occupancy_rate: berths.length ? Math.round((occupied / berths.length) * 100 * 10) / 10 : 0 };
  },

  getUser() { return Api.getUser(); },
  setUser(user) { Api.setUser(user); },

  clearAll() {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(this._prefix));
    keys.forEach(k => localStorage.removeItem(k));
  }
};

if (!ApiStore || !ApiStore._cache) {
  Store.init();
}
