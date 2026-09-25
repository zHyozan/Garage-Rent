import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { apiError } from '../api/errors'
import { useAuth } from '../context/AuthContext'

export default function ListingTrust({ space }) {
  const { user } = useAuth()
  const [reviews, setReviews] = useState([])
  const [page, setPage] = useState(1)
  const [next, setNext] = useState(false)
  const [score, setScore] = useState('5')
  const [comment, setComment] = useState('')
  const [reason, setReason] = useState('fraud')
  const [details, setDetails] = useState('')
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)
  const load = async (number = 1) => {
    try { const { data } = await api.get(`/portal/${space.id}/feedback/`, { params: { page: number } }); setReviews(data.results); setPage(number); setNext(Boolean(data.next)) }
    catch (error) { setStatus(apiError(error)) }
  }
  useEffect(() => { load() }, [space.id])
  const submit = async (event, action, payload) => {
    event.preventDefault(); setBusy(true); setStatus('')
    try { const { data } = await api.post(`/portal/${space.id}/${action}/`, payload); setStatus(data.detail); if (action === 'feedback') { setComment(''); await load() } else setDetails('') }
    catch (error) { setStatus(apiError(error)) } finally { setBusy(false) }
  }
  return <section className="trust-section">
    <h2>Avaliações de atendimento</h2>
    <p className="muted">Opiniões de usuários que enviaram uma mensagem pelo site. Não comprovam visita, pagamento ou locação. As avaliações do antigo fluxo de reservas não compõem esta nota.</p>
    {reviews.length ? reviews.map((review) => <article className="form-card" key={review.id}><strong>★ {review.score} · {review.author_name}</strong><p>{review.comment}</p><small>{new Date(review.created_at).toLocaleDateString('pt-BR')}</small></article>) : <p>Ainda não há avaliações de atendimento.</p>}
    {(next || page > 1) && <div className="row-actions"><button disabled={page === 1} onClick={() => load(page - 1)}>Anterior</button><span>Página {page}</span><button disabled={!next} onClick={() => load(page + 1)}>Próxima</button></div>}
    {user && !space.is_owner && <>
      <details><summary>Avaliar atendimento</summary><form className="stack-form" onSubmit={(e) => submit(e, 'feedback', { score: Number(score), comment })}>
        <p>Disponível após enviar uma mensagem pelo formulário de contato deste anúncio.</p>
        <label>Nota<select value={score} onChange={(e) => setScore(e.target.value)}>{[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{n} estrela(s)</option>)}</select></label>
        <label>Como foi o atendimento?<textarea required maxLength="1000" value={comment} onChange={(e) => setComment(e.target.value)} /></label>
        <button className="button button-secondary" disabled={busy}>Publicar avaliação</button>
      </form></details>
      <details><summary>Denunciar anúncio</summary><form className="stack-form" onSubmit={(e) => submit(e, 'report', { reason, details })}>
        <label>Motivo<select value={reason} onChange={(e) => setReason(e.target.value)}><option value="fraud">Suspeita de fraude</option><option value="duplicate">Anúncio duplicado</option><option value="unavailable">Espaço indisponível</option><option value="other">Outro</option></select></label>
        <label>Detalhes<textarea required maxLength="1000" value={details} onChange={(e) => setDetails(e.target.value)} /></label>
        <button className="button button-secondary" disabled={busy}>Enviar denúncia</button>
      </form></details>
    </>}
    {!user && <p><Link to="/entrar" state={{ from: `/espacos/${space.id}` }}>Entre para avaliar o atendimento ou denunciar este anúncio.</Link></p>}
    {status && <p className="alert alert-info" role="status">{status}</p>}
  </section>
}
