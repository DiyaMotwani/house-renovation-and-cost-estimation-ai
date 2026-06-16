const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, options);
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(data?.msg || `Request failed: ${res.status}`);
  }
  if (data && typeof data === 'object' && data.success === false) {
    throw new Error(data?.msg || 'Request failed');
  }
  return data;
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
      body: form,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.msg || 'Mask upload failed');
    return data;
  },

  getTaskStatus: (taskId) => request(`/api/v1/tasks/${taskId}/status`),

  getZones: (projectId) => request(`/api/v1/projects/${projectId}/zones/`),
  getProjectAnalysis: (projectId) => request(`/api/v1/projects/${projectId}/analysis`),

  getCatalog: (category) => {
    const params = category ? `?category=${encodeURIComponent(category)}` : '';
    return request(`/api/v1/catalog/materials/${params}`);
  },

  assignMaterials: (projectId, assignments) =>
    request(`/api/v1/projects/${projectId}/zones/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assignments }),
    }),

  setScaleAnchor: (projectId, userFrontWidthFt) =>
    request(`/api/v1/projects/${projectId}/scale-anchor`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_front_width_ft: userFrontWidthFt }),
    }),

  updateZone: (projectId, zoneId, estimatedSqft) =>
    request(`/api/v1/projects/${projectId}/zones/${zoneId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estimated_sqft: estimatedSqft }),
    }),

  triggerGeneration: (projectId, payload = {}) =>
    request(`/api/v1/projects/${projectId}/generate/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  getGenerationStatus: (projectId) =>
    request(`/api/v1/projects/${projectId}/generate/status`),

  getImages: (projectId) => request(`/api/v1/projects/${projectId}/images/`),

  getEstimation: (projectId) =>
    request(`/api/v1/projects/${projectId}/estimation/`),

  runEstimation: (projectId) =>
    request(`/api/v1/projects/${projectId}/estimation/run`, { method: 'POST' }),

  recalculateEstimation: (projectId, overrides) =>
    request(`/api/v1/projects/${projectId}/estimation/recalculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ overrides }),
    }),

  generateReport: (projectId) =>
    request(`/api/v1/projects/${projectId}/report/generate`, { method: 'POST' }),

  reportDownloadUrl: (projectId) =>
    `${BASE_URL}/api/v1/projects/${projectId}/report/download`,
};
