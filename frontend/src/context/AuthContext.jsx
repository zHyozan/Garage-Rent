import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadUser = async (throwOnError = false) => {
    if (!localStorage.getItem('garage_access')) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const { data } = await api.get('/auth/users/me/')
      setUser(data)
    } catch (error) {
      setUser(null)
      if (throwOnError) throw error
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUser()
    const logoutListener = () => setUser(null)
    window.addEventListener('garage:logout', logoutListener)
    return () => window.removeEventListener('garage:logout', logoutListener)
  }, [])

  const login = async (email, password) => {
    const { data } = await api.post('/auth/jwt/create/', { email, password })
    localStorage.setItem('garage_access', data.access)
    localStorage.setItem('garage_refresh', data.refresh)
    await loadUser(true)
  }

  const register = async (payload) => {
    await api.post('/auth/users/', payload)
    await login(payload.email, payload.password)
  }

  const logout = () => {
    localStorage.removeItem('garage_access')
    localStorage.removeItem('garage_refresh')
    setUser(null)
  }

  const value = useMemo(() => ({ user, loading, login, register, logout, refreshUser: loadUser }), [user, loading])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
