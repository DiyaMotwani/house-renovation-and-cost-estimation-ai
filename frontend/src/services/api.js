const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Anonymous per-browser session token so a user only sees their own projects.
function ownerToken() {
  let token = localStorage.getItem('hra_owner_token');
  if (!token) {
    token = (crypto.randomUUID?.() || `${Date.now()}-${Math.random()}`).replace(/[^a-z0-9-]/gi, '');
    localStorage.setItem('hra_owner_token', token);
  }
  return token;
}

function authHeaders(extra = {}) {
  return { 'X-Owner-Token': ownerToken(), ...extra };
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: authHeaders(options.headers || {}),
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(data?.msg || `Request failed: ${res.status}`);
  }
  if (data && typeof data === 'object' && data.success === false) {
    throw new Error(data?.msg || 'Request failed');
  }
  return data;
}

// JSON body helper.
function jsonRequest(path, method, body) {
  return request(path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// Optional ?variant_id= query string.
function vq(variantId) {
  return variantId ? `?variant_id=${encodeURIComponent(variantId)}` : '';
}

export function imageUrl(filePath) {
  if (!filePath) return '';
  const normalized = filePath.replace(/\\/g, '/');
  const idx = normalized.indexOf('storage/');
  if (idx >= 0) {
    return `${BASE_URL}/${normalized.slice(idx)}`;
  }
  return `${BASE_URL}/${normalized}`;
}

export const api = {
  createProject: (name) =>
    request('/api/v1/projects/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    }),

  uploadImage: async (projectId, file) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE_URL}/api/v1/projects/${projectId}/images/upload`, {
      method: 'POST',
      headers: authHeaders(),
      body: form,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.msg || 'Upload failed');
    return data;
  },

  uploadMask: async (projectId, file) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE_URL}/api/v1/projects/${projectId}/images/mask`, {
      method: 'POST',
      headers: authHeaders(),
      body: form,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.msg || 'Mask upload failed');
    return data;
  },

  getTaskStatus: (taskId) => request(`/api/v1/tasks/${taskId}/status`),

  getZones: (projectId, variantId) => request(`/api/v1/projects/${projectId}/zones/${vq(variantId)}`),
  getProjectAnalysis: (projectId) => request(`/api/v1/projects/${projectId}/analysis`),

  getCatalog: (category) => {
    const params = category ? `?category=${encodeURIComponent(category)}` : '';
    return request(`/api/v1/catalog/materials/${params}`);
  },

  // --- zone correction (5.2) ---
  createZone: (projectId, payload) =>
    jsonRequest(`/api/v1/projects/${projectId}/zones/`, 'POST', payload),
  updateZone: (projectId, zoneId, fields) =>
    jsonRequest(`/api/v1/projects/${projectId}/zones/${zoneId}`, 'PUT', fields),
  deleteZone: (projectId, zoneId) =>
    request(`/api/v1/projects/${projectId}/zones/${zoneId}`, { method: 'DELETE' }),

  assignMaterials: (projectId, assignments, variantId) =>
    jsonRequest(`/api/v1/projects/${projectId}/zones/assign${vq(variantId)}`, 'POST', { assignments }),

  setScaleAnchor: (projectId, userFrontWidthFt) =>
    jsonRequest(`/api/v1/projects/${projectId}/scale-anchor`, 'PUT', { user_front_width_ft: userFrontWidthFt }),

  // --- design variants (5.3) ---
  listVariants: (projectId) => request(`/api/v1/projects/${projectId}/variants/`),
  createVariant: (projectId, name) =>
    jsonRequest(`/api/v1/projects/${projectId}/variants/`, 'POST', { name, copy_from_active: true }),
  activateVariant: (projectId, variantId) =>
    request(`/api/v1/projects/${projectId}/variants/${variantId}/activate`, { method: 'PUT' }),
  renameVariant: (projectId, variantId, name) =>
    jsonRequest(`/api/v1/projects/${projectId}/variants/${variantId}`, 'PUT', { name }),
  deleteVariant: (projectId, variantId) =>
    request(`/api/v1/projects/${projectId}/variants/${variantId}`, { method: 'DELETE' }),
  compareVariants: (projectId) => request(`/api/v1/projects/${projectId}/variants/compare`),

  triggerGeneration: (projectId, payload = {}) =>
    jsonRequest(`/api/v1/projects/${projectId}/generate/`, 'POST', payload),

  getGenerationStatus: (projectId) =>
    request(`/api/v1/projects/${projectId}/generate/status`),

  getImages: (projectId) => request(`/api/v1/projects/${projectId}/images/`),

  getEstimation: (projectId, variantId) =>
    request(`/api/v1/projects/${projectId}/estimation/${vq(variantId)}`),

  runEstimation: (projectId, variantId) =>
    request(`/api/v1/projects/${projectId}/estimation/run${vq(variantId)}`, { method: 'POST' }),

  recalculateEstimation: (projectId, overrides, variantId) =>
    jsonRequest(`/api/v1/projects/${projectId}/estimation/recalculate${vq(variantId)}`, 'POST', { overrides }),

  generateReport: (projectId, variantId) =>
    request(`/api/v1/projects/${projectId}/report/generate${vq(variantId)}`, { method: 'POST' }),

  // Opened directly by the browser, so the owner token rides along as a query
  // param (the X-Owner-Token header can't be set on a plain link/navigation).
  reportDownloadUrl: (projectId) =>
    `${BASE_URL}/api/v1/projects/${projectId}/report/download?token=${encodeURIComponent(ownerToken())}`,
};
