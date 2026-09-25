import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { apiError } from '../api/errors'
import { useAuth } from '../context/AuthContext'

export const availabilityLabels = { available: 'Disponível', negotiating: 'Em negociação', rented: 'Alugado' }

export default function ContactPanel({ space }) {
  const { user } = useAuth()
  const [message, setMessage] = useState('')
  const [phone, setPhone] = useState('')
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)
  const track = (kind) => { api.post(`/portal/${space.id}/event/`, { kind }).catch(() => {}) }
  const send = async (event) => {
    event.preventDefault()
    setBusy(true); setStatus('')
    try {
      const { data } = await api.post(`/portal/${space.id}/inquiries/`, { message, reply_phone: phone })
      setStatus(data.detail); setMessage('')
    } catch (error) { setStatus(apiError(error)) } finally { setBusy(false) }
  }
  return <div className="stack-form">
    <span className="status">{availabilityLabels[space.availability_status]}</span>
    <small>Disponibilidade revisada em {new Date(space.availability_checked_at).toLocaleDateString('pt-BR')}.</small>
    <h2>Fale com o anunciante</h2>
    <p>Combine visita, condições e pagamento diretamente com o proprietário. O Garage Rent não recebe o aluguel nem garante a contratação.</p>
    {space.availability_status === 'rented' ? <p role="status">Este espaço já foi alugado. <Link to="/">Explore outras ofertas</Link>.</p> : <>
      {space.contact_phone && <>
        {space.whatsapp_enabled && <a className="button button-primary button-full" target="_blank" rel="noopener noreferrer" href={`https://wa.me/${space.contact_phone}?text=${encodeURIComponent(`Olá! Tenho interesse no anúncio ${space.title}: ${window.location.origin}/espacos/${space.id}`)}`} onClick={() => track('whatsapp')}>Conversar no WhatsApp ↗</a>}
        <a className="button button-secondary button-full" href={`tel:+${space.contact_phone}`} onClick={() => track('phone')}>Ligar: +{space.contact_phone}</a>
      </>}
      {user ? <form className="stack-form" onSubmit={send}>
        <label>Sua mensagem<textarea required maxLength="2000" rows="4" value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Olá! O espaço está disponível? Gostaria de combinar uma visita." /></label>
        <label>Telefone para resposta (opcional)<input type="tel" maxLength="24" placeholder="55 + DDD + número" value={phone} onChange={(e) => setPhone(e.target.value)} /></label>
        <small>Ao enviar, seu nome, e-mail e telefone informado serão compartilhados com este anunciante para responder ao contato.</small>
        <button disabled={busy} className="button button-primary">{busy ? 'Enviando...' : 'Enviar mensagem'}</button>
      </form> : <Link className="button button-secondary" to="/entrar" state={{ from: `/espacos/${space.id}` }}>Entrar para enviar mensagem</Link>}
    </>}
    {status && <p className="alert alert-info" role="status">{status}</p>}
    <small>O endereço completo é compartilhado pelo proprietário durante a negociação. E-mail verificado confirma apenas acesso ao e-mail.</small>
  </div>
}
