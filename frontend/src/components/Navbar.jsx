import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()

  return (
    <header className="navbar">
      <div className="container nav-inner">
        <Link to="/" className="brand">
          <span className="brand-mark">GR</span>
          <span>Garage Rent</span>
        </Link>

        <nav className="nav-links">
          <NavLink to="/">Explorar</NavLink>
          {user && <NavLink to="/meus-anuncios">Meus anúncios</NavLink>}
          {user && <NavLink to="/reservas">Reservas</NavLink>}
          {user && <NavLink to="/favoritos">Favoritos</NavLink>}
        </nav>

        <div className="nav-actions">
          {user ? (
            <>
              <Link className="button button-primary button-small" to="/anunciar">Anunciar espaço</Link>
              <button className="link-button" onClick={logout}>Sair</button>
            </>
          ) : (
            <>
              <Link className="link-button" to="/entrar">Entrar</Link>
              <Link className="button button-primary button-small" to="/cadastro">Criar conta</Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
