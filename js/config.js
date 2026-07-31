const API_BASE_URL = 'http://127.0.0.1:5000/api/v1';

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

  async request(path, options = {}) {
    const token = this.getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    };

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

  requireAuth() {
    if (!this.getToken()) {
      window.location.href = 'login.html';
    }
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
if (!NO_AUTH_PAGES.some(p => window.location.pathname.endsWith(p))) {
  Api.requireAuth();
}

