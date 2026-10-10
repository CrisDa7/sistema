// API client for Active Gym backend
const API_BASE = '/api';

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

let csrfToken = null;

async function getCsrfToken() {
  try {
    const response = await fetch(`${API_BASE}/auth/csrf`, {
      credentials: 'include',
    });
    if (!response.ok) {
      throw new ApiError('Failed to get CSRF token', response.status);
    }
    const data = await response.json();
    csrfToken = data.csrf_token;
    return csrfToken;
  } catch (error) {
    console.error('Error getting CSRF token:', error);
    throw error;
  }
}

function buildUrl(url, params = {}) {
  const queryString = new URLSearchParams(params).toString();
  return queryString ? `${url}?${queryString}` : url;
}

async function request(url, options = {}) {
  const { method = 'GET', body, headers = {}, params = {}, ...rest } = options;

  const fullUrl = buildUrl(url, params);

  const config = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    credentials: 'include',
    ...rest,
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  // Add CSRF token for write operations
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    if (!csrfToken) {
      await getCsrfToken();
    }
    config.headers['X-CSRF-Token'] = csrfToken;
    if (body) {
      const parsedBody = JSON.parse(config.body);
      parsedBody.csrf_token = csrfToken;
      config.body = JSON.stringify(parsedBody);
    }
  }

  try {
    const response = await fetch(`${API_BASE}${fullUrl}`, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      // 403 CSRF error - clear token but don't retry automatically
      if (response.status === 403) {
        csrfToken = null;
        throw new ApiError(
          errorData.message || 'CSRF token invalid or expired',
          response.status,
          errorData
        );
      }

      throw new ApiError(
        errorData.message || 'Request failed',
        response.status,
        errorData
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    console.error('Network error:', error);
    throw new ApiError('Network error', 0);
  }
}

// Auth endpoints
export const auth = {
  login: async (username, password) => {
    return request('/auth/login', {
      method: 'POST',
      body: { username, password },
    });
  },

  logout: async () => {
    return request('/auth/logout', {
      method: 'POST',
    });
  },

  getSession: async () => {
    return request('/auth/session');
  },
};

// Other endpoints (for future use)
export const api = {
  clients: {
    list: (params = {}) => request('/clients', { params }),
    create: (data) => request('/clients', { method: 'POST', body: data }),
    get: (id) => request(`/clients/${id}`),
    update: (id, data) => request(`/clients/${id}`, { method: 'PATCH', body: data }),
  },
  areas: {
    list: () => request('/areas'),
    create: (data) => request('/areas', { method: 'POST', body: data }),
    get: (id) => request(`/areas/${id}`),
    update: (id, data) => request(`/areas/${id}`, { method: 'PATCH', body: data }),
  },
  plans: {
    list: () => request('/plans'),
    create: (data) => request('/plans', { method: 'POST', body: data }),
    get: (id) => request(`/plans/${id}`),
    update: (id, data) => request(`/plans/${id}`, { method: 'PATCH', body: data }),
  },
  memberships: {
    list: () => request('/memberships'),
    create: (data) => request('/memberships', { method: 'POST', body: data }),
    get: (id) => request(`/memberships/${id}`),
    renew: (id, data) => request(`/memberships/${id}/renew`, { method: 'POST', body: data }),
  },
  payments: {
    create: (membershipId, data) =>
      request(`/memberships/${membershipId}/payments`, { method: 'POST', body: data }),
    list: (membershipId) => request(`/memberships/${membershipId}/payments`),
    get: (id) => request(`/payments/${id}`),
  },
  health: () => request('/health'),
};

export { getCsrfToken };
