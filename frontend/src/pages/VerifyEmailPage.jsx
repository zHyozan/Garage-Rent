import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import api from '../api/client'
import { apiError } from '../api/errors'
import { useAuth } from '../context/AuthContext'

export default function VerifyEmailPage() {
  const [params] = useSearchParams()
  const [message, setMessage] = useState('')
  const [done, setDone] = useState(false)
  const [busy, setBusy] = useState(false)
  const { refreshUser } = useAuth()
  const confirm = async () => {
    setBusy(true)
    try { const { data } = await api.post('/auth/verify-email/confirm/', { token: params.get('token') }); setDone(true); setMessage(data.detail); await refreshUser() }
    catch (error) { setMessage(apiError(error)) }
    finally { setBusy(false) }
  }
  return <main className="auth-shell"><section className="auth-card"><h1>Confirmar e-mail</h1><p>Confirme o endereço de e-mail vinculado a este link.</p>{message && <p role="status">{message}</p>}<button className="button button-primary" disabled={busy || done || !params.get('token')} onClick={confirm}>{done ? 'E-mail confirmado' : busy ? 'Confirmando...' : 'Confirmar meu e-mail'}</button><Link to="/">Voltar ao site</Link></section></main>
}
