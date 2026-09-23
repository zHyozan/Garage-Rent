import { useState } from 'react'
import api from '../api/client'
import { apiError } from '../api/errors'
import { useAuth } from '../context/AuthContext'

export default function VerificationBanner() {
  const { user } = useAuth()
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  if (!user || user.email_verified) return null
  const send = async () => {
    setBusy(true)
    try { const { data } = await api.post('/auth/verify-email/'); setMessage(data.detail) }
    catch (error) { setMessage(apiError(error)) }
    finally { setBusy(false) }
  }
  return <div className="verification-banner container"><span>Confirme seu e-mail para exibir o selo nos seus anúncios.</span> <button className="link-button" disabled={busy} onClick={send}>{busy ? 'Enviando...' : 'Enviar verificação'}</button>{message && <p role="status">{message}</p>}</div>
}
