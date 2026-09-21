import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <div className="page-center">Carregando...</div>
  if (!user) return <Navigate to="/entrar" replace state={{ from: location.pathname }} />
  return children
}
