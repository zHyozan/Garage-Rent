import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { availabilityLabels } from '../components/ContactPanel'
import { apiError } from '../api/errors'

export default function MySpacesPage() {
  const [spaces, setSpaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [busy, setBusy] = useState(false)

  const load = async (number = 1) => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get('/spaces/mine/', { params: { page: number } })
      setSpaces(data.results || data)
      setPage(number); setHasNext(Boolean(data.next))
    } catch {
      setError('Não foi possível carregar seus anúncios.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const remove = async (id) => {
    if (!window.confirm('Excluir este anúncio?')) return
    try {
      await api.delete(`/spaces/${id}/`)
      await load()
    } catch {
      setError('Não foi possível excluir o anúncio.')
    }
  }

  const toggleActive = async (space) => {
    try {
      await api.patch(`/spaces/${space.id}/`, { is_active: !space.is_active })
      await load()
    } catch {
      setError(`Não foi possível ${space.is_active ? 'pausar' : 'ativar'} o anúncio.`)
    }
  }

  const availability = async (space, value) => {
    setBusy(true); setError('')
    try {
      if (value) await api.patch(`/spaces/${space.id}/`, { availability_status: value })
      else await api.post(`/portal/${space.id}/refresh/`)
      await load(page)
    } catch (err) { setError(apiError(err)) } finally { setBusy(false) }
  }

  return (
    <main className="container section">
      <div className="section-heading"><div><span className="eyebrow">Painel do proprietário</span><h1>Meus anúncios</h1></div><Link className="button button-primary" to="/anunciar">Anunciar grátis</Link></div>
      <p>Publicação gratuita, sem comissão sobre o aluguel. Acompanhe contatos e solicite destaque opcional em “Resultados e destaque”.</p>
      {error && <div className="alert alert-error">{error}</div>}
      {loading ? <div className="empty-state">Carregando...</div> : spaces.length ? (
        <div className="management-list">
          {spaces.map((space) => (
            <article className="management-card" key={space.id}>
              <div>
                <span className={`status ${space.is_active ? 'status-confirmed' : 'status-cancelled'}`}>{space.is_active ? 'Ativo' : 'Pausado'}</span>
                <h3>{space.title}</h3>
                <p>{space.public_location}</p>
                {space.moderated && <p className="alert alert-error">Oculto pela moderação. Consulte a administração.</p>}
                {space.is_promoted && <span className="sponsored-label">Patrocinado</span>}
                <label>Disponibilidade<select disabled={busy} value={space.availability_status} onChange={(e) => availability(space, e.target.value)}>{Object.entries(availabilityLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
                {Date.now() - new Date(space.availability_checked_at).getTime() > 30 * 86400000 && <p className="alert alert-info">Há mais de 30 dias sem revisão. Confira a disponibilidade.</p>}
                <button disabled={busy} className="link-button" onClick={() => availability(space)}>Confirmar que a disponibilidade está atualizada</button>
              </div>
              <div className="row-actions">
                <Link className="button button-primary button-small" to={`/meus-anuncios/${space.id}/resultados`}>Resultados e destaque</Link>
                <Link className="button button-secondary button-small" to={`/espacos/${space.id}`}>Ver</Link>
                <Link className="button button-secondary button-small" to={`/meus-anuncios/${space.id}/editar`}>Editar</Link>
                <button className="button button-secondary button-small" onClick={() => toggleActive(space)}>{space.is_active ? 'Pausar' : 'Ativar'}</button>
                <button className="button button-danger button-small" onClick={() => remove(space.id)}>Excluir</button>
              </div>
            </article>
          ))}
        </div>
      ) : <div className="empty-state">Você ainda não publicou nenhum espaço.</div>}
      {(hasNext || page > 1) && <div className="pagination"><button disabled={loading || page === 1} onClick={() => load(page - 1)}>Anterior</button><span>Página {page}</span><button disabled={loading || !hasNext} onClick={() => load(page + 1)}>Próxima</button></div>}
    </main>
  )
}
