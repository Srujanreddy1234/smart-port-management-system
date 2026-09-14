const ApiStore = {
  _cache: {},
  _cacheTimestamps: {},
  _cacheTTL: 5 * 60 * 1000,

  _headers() {
    const token = Api.getToken();
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    };
  },

  async _apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { ...this._headers(), ...(options.headers || {}) }
    });
    if (response.status === 401) {
      Api.clearSession();
      window.location.href = 'login.html';
      throw new Error('Session expired');
    }
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.message || 'Request failed');
    }
    return await response.json();
  },

  _isCacheValid(key) {
    const ts = this._cacheTimestamps[key];
    if (!ts) return false;
    return Date.now() - ts < this._cacheTTL;
  },

  _hydrateFromSession(key) {
    if (this._cache[key] !== undefined) return;
    try {
      const raw = sessionStorage.getItem('spm_cache_' + key);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed.ts === 'number') {
        this._cache[key] = parsed.data;
        this._cacheTimestamps[key] = parsed.ts;
      }
    } catch { /* sessionStorage unavailable or corrupt entry -- ignore, will re-fetch */ }
  },

  _persistToSession(key) {
    try {
      sessionStorage.setItem('spm_cache_' + key, JSON.stringify({ data: this._cache[key], ts: this._cacheTimestamps[key] }));
    } catch { /* storage full or unavailable -- in-memory cache still works for this page load */ }
  },

  async get(key) {
    if (key === 'user') {
      const user = Api.getUser();
      if (user) return user;
    }
    this._hydrateFromSession(key);
    if (this._isCacheValid(key) && this._cache[key]) {
      return this._cache[key];
    }
    const endpoints = {
      ships: '/ships?page=1&per_page=100',
      containers: '/containers?page=1&per_page=100',
      trucks: '/trucks?page=1&per_page=100',
      berths: '/berths?page=1&per_page=100',
      alerts: '/security/alerts?page=1&per_page=100',
      invoices: '/billing/invoices?page=1&per_page=100',
      users: '/users?page=1&per_page=100',
      activity_log: '/dashboard/recent-activity?limit=50',
      env_readings: '/environment/readings?limit=1',
    };
    const endpoint = endpoints[key];
    if (!endpoint) return this._cache[key] || [];
    try {
      const res = await this._apiRequest(endpoint);
      const items = res.data?.items || res.data || [];
      this._cache[key] = items;
      this._cacheTimestamps[key] = Date.now();
      this._persistToSession(key);
      return items;
    } catch {
      return this._cache[key] || [];
    }
  },

  set(key, value) {
    this._cache[key] = value;
    this._cacheTimestamps[key] = Date.now();
    this._persistToSession(key);
  },

  async add(key, item) {
    const endpoints = {
      ships: '/ships',
      containers: '/containers',
      trucks: '/trucks',
      berths: '/berths',
      alerts: '/security/alerts',
      invoices: '/billing/invoices',
    };
    const endpoint = endpoints[key];
    if (!endpoint) {
      const arr = this._cache[key] || [];
      item.id = item.id || Date.now();
      item.created_at = item.created_at || new Date().toISOString();
      arr.push(item);
      this.set(key, arr);
      return item;
    }
    try {
      const res = await this._apiRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(item)
      });
      const created = res.data;
      const arr = this._cache[key] || [];
      arr.push(created);
      this.set(key, arr);
      return created;
    } catch (err) {
      throw err;
    }
  },

  async update(key, id, updates) {
    const endpoints = {
      ships: `/ships/${id}`,
      containers: `/containers/${id}`,
      trucks: `/trucks/${id}`,
      berths: `/berths/${id}`,
      alerts: `/security/alerts/${id}`,
      invoices: `/billing/invoices/${id}`,
    };
    const endpoint = endpoints[key];
    if (!endpoint) {
      const arr = this._cache[key] || [];
      const idx = arr.findIndex(item => item.id == id);
      if (idx === -1) return null;
      arr[idx] = { ...arr[idx], ...updates, updated_at: new Date().toISOString() };
      this.set(key, arr);
      return arr[idx];
    }
    const res = await this._apiRequest(endpoint, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
    const updated = res.data;
    const arr = this._cache[key] || [];
    const idx = arr.findIndex(item => item.id == id);
    if (idx !== -1) {
      arr[idx] = updated;
      this.set(key, arr);
    }
    return updated;
  },

  async remove(key, id) {
    const endpoints = {
      ships: `/ships/${id}`,
      containers: `/containers/${id}`,
      trucks: `/trucks/${id}`,
      berths: `/berths/${id}`,
      alerts: `/security/alerts/${id}`,
      invoices: `/billing/invoices/${id}`,
    };
    const endpoint = endpoints[key];
    if (endpoint) {
      await this._apiRequest(endpoint, { method: 'DELETE' });
    }
    const arr = this._cache[key] || [];
    const filtered = arr.filter(item => item.id != id);
    this.set(key, filtered);
    return filtered;
  },

  getById(key, id) {
    const arr = this._cache[key] || [];
    return arr.find(item => item.id == id) || null;
  },

  getUser() { return Api.getUser(); },
  setUser(user) { Api.setUser(user); },

  async init() {
    await Promise.all([
      this.get('ships'),
      this.get('containers'),
      this.get('trucks'),
      this.get('berths'),
      this.get('alerts'),
      this.get('users'),
      this.get('activity_log'),
      this.get('env_readings'),
    ]);
  },

  getShipStats() {
    const ships = this._cache['ships'] || [];
    const byStatus = {};
    ships.forEach(s => { byStatus[s.status] = (byStatus[s.status] || 0) + 1; });
    return { total: ships.length, by_status: byStatus };
  },

  getContainerStats() {
    const containers = this._cache['containers'] || [];
    const byStatus = {};
    const byType = {};
    containers.forEach(c => {
      byStatus[c.status] = (byStatus[c.status] || 0) + 1;
      byType[c.container_type] = (byType[c.container_type] || 0) + 1;
    });
    return { total: containers.length, by_status: byStatus, by_type: byType, loaded: byStatus['Loaded'] || 0 };
  },

  getTruckStats() {
    const trucks = this._cache['trucks'] || [];
    const byStatus = {};
    trucks.forEach(t => { byStatus[t.status] = (byStatus[t.status] || 0) + 1; });
    return { total: trucks.length, by_status: byStatus };
  },

  getBerthStats() {
    const berths = this._cache['berths'] || [];
    const byStatus = {};
    berths.forEach(b => { byStatus[b.status] = (byStatus[b.status] || 0) + 1; });
    const occupied = byStatus['Occupied'] || 0;
    return { total: berths.length, occupied, available: byStatus['Available'] || 0, maintenance: byStatus['Maintenance'] || 0, occupancy_rate: berths.length ? Math.round((occupied / berths.length) * 100 * 10) / 10 : 0 };
  },

  async invalidate(key) {
    delete this._cache[key];
    delete this._cacheTimestamps[key];
  },

  async invalidateAll() {
    this._cache = {};
    this._cacheTimestamps = {};
  }
};
