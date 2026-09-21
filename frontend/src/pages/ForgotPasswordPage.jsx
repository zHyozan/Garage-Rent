import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      const { data } = await api.post('/auth/password-reset/', { email })
      setMessage(data.detail)
    } catch {
      setMessage('Não foi possível solicitar o link. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return <main className="auth-shell"><form className="auth-card" onSubmit={submit}>
    <h1>Recuperar senha</h1>
    <p>Enviaremos um link para o e-mail cadastrado. Ele vale por 1 hora.</p>
    <label>E-mail<input required type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
    {message && <div className="alert alert-info" role="status">{message}</div>}
    <button className="button button-primary button-full" disabled={loading}>{loading ? 'Enviando...' : 'Enviar link'}</button>
    <Link to="/entrar">Voltar ao login</Link>
  </form></main>
}
