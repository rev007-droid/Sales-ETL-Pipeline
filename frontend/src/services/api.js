// define api base
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

// token localstorage key
const ACCESS_TOKEN_KEY = 'salespulse_access_token';
const REFRESH_TOKEN_KEY = 'salespulse_refresh_token';
const USER_KEY = 'salespulse_user';

// get stored token
export const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY);
// get stored refresh
export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);
// get stored user
export const getStoredUser = () => {
  try {
    const u = localStorage.getItem(USER_KEY);
    return u ? JSON.parse(u) : null;
  } catch (e) {
    return null;
  }
};

// set auth session
export const setAuthSession = (tokenData) => {
  if (tokenData?.access_token) localStorage.setItem(ACCESS_TOKEN_KEY, tokenData.access_token);
  if (tokenData?.refresh_token) localStorage.setItem(REFRESH_TOKEN_KEY, tokenData.refresh_token);
  if (tokenData?.user) localStorage.setItem(USER_KEY, JSON.stringify(tokenData.user));
};

// clear auth session
export const clearAuthSession = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

// authenticated fetch helper
const authFetch = async (url, options = {}) => {
  const token = getAccessToken(); // get token
  const headers = {
    ...(options.headers || {}) // copy existing
  };

  // attach bearer header
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // execute fetch call
  let res = await fetch(url, { ...options, headers });

  // handle 401 token refresh
  if (res.status === 401 && getRefreshToken()) {
    try {
      const refRes = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: getRefreshToken() })
      });
      if (refRes.ok) {
        const newData = await refRes.json();
        setAuthSession(newData); // update session
        headers['Authorization'] = `Bearer ${newData.access_token}`;
        res = await fetch(url, { ...options, headers }); // retry request
      } else {
        clearAuthSession(); // clear invalid
      }
    } catch (e) {
      clearAuthSession(); // clear on error
    }
  }

  return res;
};

// helper query string
const buildQuery = (params) => {
  if (!params) return ''; // no params
  const clean = Object.entries(params) // iterate entries
    .filter(([_, v]) => v !== undefined && v !== null && v !== '' && v !== 'all') // drop empty
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`) // encode pairs
    .join('&'); // join ampersand
  return clean ? `?${clean}` : ''; // append query
};

// api service methods
export const api = {
  // register user account
  async register(data) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }
    const tokenData = await res.json();
    setAuthSession(tokenData);
    return tokenData;
  },

  // login user credentials
  async login(credentials) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }
    const tokenData = await res.json();
    setAuthSession(tokenData);
    return tokenData;
  },

  // logout current user
  async logout() {
    try {
      await authFetch(`${API_BASE}/auth/logout`, { method: 'POST' });
    } finally {
      clearAuthSession();
    }
  },

  // get current user profile
  async getMe() {
    const res = await authFetch(`${API_BASE}/auth/me`);
    if (!res.ok) throw new Error('Failed to fetch profile');
    return res.json();
  },

  // get health status
  async getHealth() {
    const res = await authFetch(`${API_BASE}/health`); // call health
    if (!res.ok) throw new Error('Health check failed'); // check error
    return res.json(); // return json
  },

  // get dashboard summary
  async getDashboardSummary(params = {}) {
    const qs = buildQuery(params); // build qs
    const res = await authFetch(`${API_BASE}/dashboard/summary${qs}`); // call summary
    if (!res.ok) throw new Error('Failed to load dashboard summary'); // check error
    return res.json(); // return json
  },

  // get sales trend
  async getSalesTrend(params = {}) {
    const qs = buildQuery(params); // build qs
    const res = await authFetch(`${API_BASE}/dashboard/sales-trend${qs}`); // call trend
    if (!res.ok) throw new Error('Failed to load sales trend'); // check error
    return res.json(); // return json
  },

  // get region performance
  async getRegionPerformance(params = {}) {
    const qs = buildQuery(params); // build qs
    const res = await authFetch(`${API_BASE}/dashboard/region-performance${qs}`); // call regions
    if (!res.ok) throw new Error('Failed to load regional performance'); // check error
    return res.json(); // return json
  },

  // get category performance
  async getCategoryPerformance(params = {}) {
    const qs = buildQuery(params); // build qs
    const res = await authFetch(`${API_BASE}/dashboard/category-performance${qs}`); // call categories
    if (!res.ok) throw new Error('Failed to load category performance'); // check error
    return res.json(); // return json
  },

  // get top products
  async getTopProducts(params = {}) {
    const qs = buildQuery(params); // build qs
    const res = await authFetch(`${API_BASE}/dashboard/top-products${qs}`); // call top products
    if (!res.ok) throw new Error('Failed to load top products'); // check error
    return res.json(); // return json
  },

  // get paginated sales
  async getSales(params = {}) {
    const qs = buildQuery(params); // build qs
    const res = await authFetch(`${API_BASE}/sales${qs}`); // call sales
    if (!res.ok) throw new Error('Failed to load sales transactions'); // check error
    return res.json(); // return json
  },

  // get sales preview
  async getSalesPreview(limit = 10) {
    const res = await authFetch(`${API_BASE}/sales/preview?limit=${limit}`); // call preview
    if (!res.ok) throw new Error('Failed to load preview'); // check error
    return res.json(); // return json
  },

  // upload sales dataset
  async uploadFile(file) {
    const formData = new FormData(); // create formdata
    formData.append('file', file); // attach file
    const res = await authFetch(`${API_BASE}/upload`, {
      method: 'POST', // post method
      body: formData // send file
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({})); // parse json error
      throw new Error(err.detail || 'File upload failed'); // raise error
    }
    return res.json(); // return json
  },

  // trigger etl execution
  async runEtl(payload = {}) {
    const res = await authFetch(`${API_BASE}/etl/run`, {
      method: 'POST', // post request
      headers: { 'Content-Type': 'application/json' }, // json header
      body: JSON.stringify(payload) // send payload
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({})); // parse error
      throw new Error(err.detail || 'ETL execution failed'); // raise error
    }
    return res.json(); // return json
  },

  // get etl jobs
  async getEtlJobs(limit = 20) {
    const res = await authFetch(`${API_BASE}/etl/jobs?limit=${limit}`); // call jobs
    if (!res.ok) throw new Error('Failed to load ETL jobs'); // check error
    return res.json(); // return json
  },

  // get single job
  async getEtlJobDetail(jobId) {
    const res = await authFetch(`${API_BASE}/etl/jobs/${jobId}`); // call job detail
    if (!res.ok) throw new Error(`Failed to load ETL job ${jobId}`); // check error
    return res.json(); // return json
  },

  // get latest results
  async getLatestEtlResults() {
    const res = await authFetch(`${API_BASE}/etl/results`); // call results
    if (!res.ok) throw new Error('Failed to load ETL results'); // check error
    return res.json(); // return json
  },

  // get quality report
  async getDataQualityReport() {
    const res = await authFetch(`${API_BASE}/reports/data-quality`); // call reports
    if (!res.ok) throw new Error('Failed to load data quality report'); // check error
    return res.json(); // return json
  },

  // get clean export url
  getCleanExportUrl(format = 'csv') {
    return `${API_BASE}/exports/clean-sales?format=${format}`; // download url
  },

  // get rejected export url
  getRejectedExportUrl(format = 'csv', jobId = '') {
    const jobParam = jobId ? `&job_id=${encodeURIComponent(jobId)}` : ''; // optional job
    return `${API_BASE}/exports/rejected-sales?format=${format}${jobParam}`; // download url
  }
};
