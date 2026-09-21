import { Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import CreateSpacePage from './pages/CreateSpacePage'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import MySpacesPage from './pages/MySpacesPage'
import RegisterPage from './pages/RegisterPage'
import ReservationsPage from './pages/ReservationsPage'
import SpaceDetailPage from './pages/SpaceDetailPage'

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/entrar" element={<LoginPage />} />
        <Route path="/cadastro" element={<RegisterPage />} />
        <Route path="/espacos/:id" element={<SpaceDetailPage />} />
        <Route path="/anunciar" element={<ProtectedRoute><CreateSpacePage /></ProtectedRoute>} />
        <Route path="/meus-anuncios" element={<ProtectedRoute><MySpacesPage /></ProtectedRoute>} />
        <Route path="/reservas" element={<ProtectedRoute><ReservationsPage /></ProtectedRoute>} />
        <Route path="/favoritos" element={<ProtectedRoute><HomePage favoritesOnly /></ProtectedRoute>} />
      </Routes>
    </>
  )
}
