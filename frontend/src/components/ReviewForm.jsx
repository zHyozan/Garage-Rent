import { useState } from 'react'
import api from '../api/client'
import { apiError } from '../api/errors'

export default function ReviewForm({ reservationId, onSaved }) {
  const [score, setScore] = useState('5')
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async (event) => {
    event.preventDefault(); setBusy(true); setError('')
    try { await api.post(`/reservations/${reservationId}/review/`, { score: Number(score), comment }); await onSaved() }
    catch (err) { setError(apiError(err)) }
    finally { setBusy(false) }
  }
  return <form className="stack-form review-form" onSubmit={submit}><h3>Avaliar esta locação</h3><label>Nota<select value={score} onChange={(e) => setScore(e.target.value)}>{[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{n} de 5</option>)}</select></label><label>Comentário<textarea maxLength={2000} value={comment} onChange={(e) => setComment(e.target.value)} /></label>{error && <p role="alert">{error}</p>}<button className="button button-primary" disabled={busy}>{busy ? 'Enviando...' : 'Publicar avaliação'}</button></form>
}
