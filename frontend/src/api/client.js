import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('garage_access')
  if (token && !config.url.startsWith('/auth/')) config.headers.Authorization = `Bearer ${token}`
  if (token && ['/auth/users/me/', '/auth/verify-email/'].includes(config.url)) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const refresh = localStorage.getItem('garage_refresh')

    if (error.response?.status === 401 && refresh && original && !original._retry && !['/auth/jwt/create/', '/auth/users/'].includes(original.url)) {
      original._retry = true
      try {
        refreshing ||= axios.post(`${API_URL}/auth/jwt/refresh/`, { refresh }, { timeout: 15000 })
        const { data } = await refreshing
        refreshing = null
        localStorage.setItem('garage_access', data.access)
        if (data.refresh) localStorage.setItem('garage_refresh', data.refresh)
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch (refreshError) {
        refreshing = null
        localStorage.removeItem('garage_access')
        localStorage.removeItem('garage_refresh')
        window.dispatchEvent(new Event('garage:logout'))
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  },
)

export default api
