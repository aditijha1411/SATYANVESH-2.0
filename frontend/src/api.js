import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const casesAPI = {
  getAll: () => api.get('/cases/'),
  get: (caseId) => api.get(`/cases/${caseId}`),
  create: (data) => api.post('/cases/', data),
  updateStatus: (caseId, status) => api.patch(`/cases/${caseId}/status?status=${status}`),
  delete: (caseId) => api.delete(`/cases/${caseId}`)
};

export const evidenceAPI = {
  upload: (caseId, formData) => api.post('/evidence/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getByCase: (caseId) => api.get(`/evidence/case/${caseId}`),
  get: (evidenceId) => api.get(`/evidence/${evidenceId}`),
  parse: (evidenceId) => api.post(`/evidence/${evidenceId}/parse`),
  delete: (evidenceId) => api.delete(`/evidence/${evidenceId}`)
};

export const graphAPI = {
  correlate: (caseId) => api.post(`/graph/correlate/${caseId}`),
  getEntities: (caseId) => api.get(`/graph/entities/${caseId}`),
  getRelationships: (caseId) => api.get(`/graph/relationships/${caseId}`),
  getEvents: (caseId) => api.get(`/graph/events/${caseId}`)
};

export const timelineAPI = {
  getFullTimeline: (caseId) => api.get(`/timeline/${caseId}`),
  getEntityTimeline: (caseId, entity) => api.get(`/timeline/${caseId}/entity/${entity}`),
  getPatterns: (caseId) => api.get(`/timeline/${caseId}/patterns`)
};

export const aiAPI = {
  analyze: (caseId) => api.post(`/ai/analyze/${caseId}`),
  getLeads: (caseId) => api.post(`/ai/leads/${caseId}`),
  getPatterns: (caseId) => api.post(`/ai/patterns/${caseId}`)
};

export const reportsAPI = {
  getSummary: (caseId) => api.get(`/reports/${caseId}/summary`),
  getEntities: (caseId) => api.get(`/reports/${caseId}/entities`),
  getRelationships: (caseId) => api.get(`/reports/${caseId}/relationships`),
  getTimeline: (caseId) => api.get(`/reports/${caseId}/timeline`)
};

export const notebookAPI = {
  create: (caseId, data) => api.post(`/notebook/${caseId}/entry`, data),
  getAll: (caseId) => api.get(`/notebook/${caseId}/entries`),
  get: (caseId, entryId) => api.get(`/notebook/${caseId}/entry/${entryId}`),
  update: (caseId, entryId, data) => api.patch(`/notebook/${caseId}/entry/${entryId}`, data),
  delete: (caseId, entryId) => api.delete(`/notebook/${caseId}/entry/${entryId}`),
  pin: (caseId, entryId) => api.post(`/notebook/${caseId}/entry/${entryId}/pin`),
  getPinned: (caseId) => api.get(`/notebook/${caseId}/pinned`)
};

export default api;