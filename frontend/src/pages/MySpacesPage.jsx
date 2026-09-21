import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'

export default function MySpacesPage() {
  const [spaces, setSpaces] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    const { data } = await api.get('/spaces/mine/')
    setSpaces(data.results || data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const remove = async (id) => {
    if (!window.confirm('Excluir este anúncio?')) return
    await api.delete(`/spaces/${id}/`)
    await load()
  }

  const toggleActive = async (space) => {
    await api.patch(`/spaces/${space.id}/`, { is_active: !space.is_active })
    await load()
  }

  return (
    <main className="container section">
      <div className="section-heading"><div><span className="eyebrow">Painel do proprietário</span><h1>Meus anúncios</h1></div><Link className="button button-primary" to="/anunciar">Novo anúncio</Link></div>
      {loading ? <div className="empty-state">Carregando...</div> : spaces.length ? (
        <div className="management-list">
          {spaces.map((space) => (
            <article className="management-card" key={space.id}>
              <div>
                <span className={`status ${space.is_active ? 'status-confirmed' : 'status-cancelled'}`}>{space.is_active ? 'Ativo' : 'Pausado'}</span>
                <h3>{space.title}</h3>
                <p>{space.public_location}</p>
              </div>
              <div className="row-actions">
                <Link className="button button-secondary button-small" to={`/espacos/${space.id}`}>Ver</Link>
                <button className="button button-secondary button-small" onClick={() => toggleActive(space)}>{space.is_active ? 'Pausar' : 'Ativar'}</button>
                <button className="button button-danger button-small" onClick={() => remove(space.id)}>Excluir</button>
              </div>
            </article>
          ))}
        </div>
      ) : <div className="empty-state">Você ainda não publicou nenhum espaço.</div>}
    </main>
  )
}
