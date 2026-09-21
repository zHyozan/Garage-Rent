import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

const labels = { pending: 'Pendente', confirmed: 'Confirmada', rejected: 'Recusada', cancelled: 'Cancelada', completed: 'Concluída' }

export default function ReservationsPage() {
  const { user } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    const { data } = await api.get('/reservations/')
    setItems(data.results || data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const act = async (id, action) => {
    await api.post(`/reservations/${id}/${action}/`)
    await load()
  }

  return (
    <main className="container section">
      <div className="section-heading"><div><span className="eyebrow">Locações</span><h1>Reservas</h1></div></div>
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
                </div>
                <div className="row-actions">
                  {ownerView && item.status === 'pending' && <>
                    <button className="button button-primary button-small" onClick={() => act(item.id, 'confirm')}>Confirmar</button>
                    <button className="button button-danger button-small" onClick={() => act(item.id, 'reject')}>Recusar</button>
                  </>}
                  {!ownerView && ['pending', 'confirmed'].includes(item.status) && <button className="button button-danger button-small" onClick={() => act(item.id, 'cancel')}>Cancelar</button>}
                </div>
              </article>
            )
          })}
        </div>
      ) : <div className="empty-state">Nenhuma reserva encontrada.</div>}
    </main>
  )
}
