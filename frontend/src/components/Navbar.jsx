import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useState } from 'react'

export default function Navbar() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)

  return (
    <header className="navbar">
      <div className="container nav-inner">
        <Link to="/" className="brand">
          <span className="brand-mark">GR</span>
          <span>Garage Rent</span>
        </Link>

        <button className="menu-toggle button button-secondary" aria-expanded={open} aria-controls="main-navigation" onClick={() => setOpen(!open)}>Menu</button>
        <nav id="main-navigation" aria-label="Navegação principal" className={`nav-links ${open ? 'is-open' : ''}`} onClick={() => setOpen(false)}>
          <NavLink to="/">Explorar</NavLink>
          {user && <NavLink to="/meus-anuncios">Meus anúncios</NavLink>}
          {user && <NavLink to="/alertas">Meus alertas</NavLink>}
          {user && <NavLink to="/favoritos">Favoritos</NavLink>}
        </nav>

        <div className="nav-actions">
          {user ? (
            <>
              <Link className="button button-primary button-small" to="/anunciar">Anunciar grátis</Link>
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
