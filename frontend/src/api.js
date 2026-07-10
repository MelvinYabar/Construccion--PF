const API_URL = import.meta.env.VITE_API_URL
  || (import.meta.env.PROD ? 'https://parmenia-api-r0oi.onrender.com' : 'http://127.0.0.1:8000')

export function getToken() { return localStorage.getItem('parmenia_token') }

export function setSession(token, user) {
  localStorage.setItem('parmenia_token', token)
  localStorage.setItem('parmenia_user', JSON.stringify(user))
}

export function clearSession() {
  localStorage.removeItem('parmenia_token')
  localStorage.removeItem('parmenia_user')
}

export function getStoredUser() {
  const raw = localStorage.getItem('parmenia_user')
  return raw ? JSON.parse(raw) : null
}

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    body: options.body && !(options.body instanceof FormData) ? JSON.stringify(options.body) : options.body,
  })
  const text = await response.text()
  let data = null
  if (text) { try { data = JSON.parse(text) } catch { data = text } }
  if (!response.ok) {
    const detail = data?.detail || data?.message || data || `HTTP ${response.status}`
    throw new Error(Array.isArray(detail) ? JSON.stringify(detail) : detail)
  }
  return data
}

export const authApi = {
  login: (email, password) => apiRequest('/auth/login', { method: 'POST', body: { email, password } }),
  register: (body) => apiRequest('/auth/register', { method: 'POST', body }),
  googleLogin: (credential) => apiRequest('/auth/oauth/google', { method: 'POST', body: { credential } }),
  me: () => apiRequest('/auth/me'),
}

export const notificationsApi = {
  list: (unreadOnly = false) => apiRequest(`/notifications/?unread_only=${unreadOnly}`),
  unreadCount: () => apiRequest('/notifications/unread-count'),
  markRead: (id) => apiRequest(`/notifications/${id}/read`, { method: 'PUT' }),
  markAllRead: () => apiRequest('/notifications/read-all', { method: 'PUT' }),
}

export const commentsApi = {
  list: (deliverableId) => apiRequest(`/deliverables/${deliverableId}/comments`),
  create: (deliverableId, content) => apiRequest(`/deliverables/${deliverableId}/comments`, { method: 'POST', body: { content } }),
  delete: (commentId) => apiRequest(`/comments/${commentId}`, { method: 'DELETE' }),
}

export const uploadApi = {
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiRequest('/upload/file', { method: 'POST', body: formData })
  },
}

export const mentorshipsApi = {
  list: () => apiRequest('/integrations/mentorships'),
  create: (data) => apiRequest('/integrations/google-calendar/mentorships', { method: 'POST', body: data }),
}

export const projectsApi = {
  publicDetail: (id) => apiRequest(`/projects/${id}/public-detail`),
  changePhase: (projectId, phaseId) => apiRequest(`/projects/${projectId}/phase?phase_id=${phaseId}`, { method: 'PUT' }),
  myStats: () => apiRequest('/projects/my-stats'),
}
