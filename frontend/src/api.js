const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export function getToken() {
  return localStorage.getItem('parmenia_token')
}

export function setSession(auth) {
  localStorage.setItem('parmenia_token', auth.access_token)
  localStorage.setItem('parmenia_user', JSON.stringify(auth.user))
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
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!response.ok) {
    const detail = data?.detail || data?.message || data || `HTTP ${response.status}`
    throw new Error(Array.isArray(detail) ? JSON.stringify(detail) : detail)
  }

  return data
}

export const authApi = {
  login: (body) => apiRequest('/auth/login', { method: 'POST', body }),
  register: (body) => apiRequest('/auth/register', { method: 'POST', body }),
  google: (credential) => apiRequest('/auth/oauth/google', { method: 'POST', body: { credential } }),
  me: () => apiRequest('/auth/me'),
}
