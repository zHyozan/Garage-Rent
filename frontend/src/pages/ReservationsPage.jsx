import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import ReviewForm from '../components/ReviewForm'
import { apiError } from '../api/errors'

const labels = { pending: 'Pendente', confirmed: 'Confirmada', rejected: 'Recusada', cancelled: 'Cancelada', completed: 'Concluída' }

export default function ReservationsPage() {
  const { user } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [actingId, setActingId] = useState(null)
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)

  const load = async (nextPage = page) => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get('/reservations/', { params: { page: nextPage } })
      setItems(data.results || data)
      setPage(nextPage); setHasNext(Boolean(data.next))
      return true
    } catch (error) {
      setError(apiError(error))
      return false
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const act = async (id, action) => {
    setActingId(id)
    setError('')
    setMessage('')
    try {
      await api.post(`/reservations/${id}/${action}/`)
      if (await load()) setMessage('Reserva atualizada com sucesso.')
    } catch (error) {
      setError(error.response?.data?.detail || 'Não foi possível atualizar a reserva. Tente novamente.')
    } finally {
      setActingId(null)
    }
  }

  return (
    <main className="container section">
      <div className="section-heading"><div><span className="eyebrow">Locações</span><h1>Reservas</h1></div></div>
      {error && <div className="alert alert-error" role="alert">{error} <button type="button" onClick={() => load()}>Tentar novamente</button></div>}
      {message && <div className="alert alert-info" role="status">{message}</div>}
      {loading ? <div className="empty-state">Carregando...</div> : items.length ? (
        <div className="management-list">
          {items.map((item) => {
            const ownerView = item.space_summary.owner_id === user.id
            return (
              <article className="management-card reservation-card" key={item.id}>
                <div>
                  <span className={`status status-${item.status}`}>{labels[item.status]}</span>
                  <h3>{item.space_summary.title}</h3>
                  <p>{item.space_summary.public_location}</p>
                  <p><strong>{new Date(item.start_at).toLocaleString('pt-BR')}</strong> até <strong>{new Date(item.end_at).toLocaleString('pt-BR')}</strong></p>
                  <p>Total: {Number(item.total_amount).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</p>
                  <small>{ownerView ? `Solicitado por @${item.renter.username}` : 'Sua solicitação'}</small>
                  <p><small>{item.cancellation_policy}</small></p>
                  {item.review && <p>Sua locação recebeu nota {item.review.score}/5: {item.review.comment}</p>}
                  {!ownerView && item.status === 'completed' && !item.review && <ReviewForm reservationId={item.id} onSaved={load} />}
                </div>
                <div className="row-actions">
                  {item.status === 'confirmed' && new Date(item.end_at) <= new Date() && <button disabled={actingId !== null} className="button button-primary" onClick={() => act(item.id, 'complete')}>Concluir locação</button>}
                  {ownerView && item.status === 'pending' && <>
                    <button disabled={actingId !== null} className="button button-primary button-small" onClick={() => act(item.id, 'confirm')}>Confirmar</button>
                    <button disabled={actingId !== null} className="button button-danger button-small" onClick={() => act(item.id, 'reject')}>Recusar</button>
                  </>}
                  {!ownerView && ['pending', 'confirmed'].includes(item.status) && new Date(item.start_at) > new Date() && <button disabled={actingId !== null} className="button button-danger button-small" onClick={() => act(item.id, 'cancel')}>Cancelar</button>}
                </div>
              </article>
            )
          })}
        </div>
      ) : !error && <div className="empty-state">Nenhuma reserva encontrada.</div>}
      <div className="pagination"><button className="button button-secondary" disabled={loading || page === 1} onClick={() => load(page - 1)}>Anterior</button><span>Página {page}</span><button className="button button-secondary" disabled={loading || !hasNext} onClick={() => load(page + 1)}>Próxima</button></div>
    </main>
  )
}
