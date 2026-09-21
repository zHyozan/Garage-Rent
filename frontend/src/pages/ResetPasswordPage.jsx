import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import api from '../api/client'

export default function ResetPasswordPage() {
  const [params] = useSearchParams()
  const [form, setForm] = useState({ password: '', re_password: '' })
  const [message, setMessage] = useState('')
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)
  const uid = params.get('uid')
  const token = params.get('token')

  const submit = async (event) => {
    event.preventDefault()
    setMessage('')
    if (form.password !== form.re_password) return setMessage('As senhas não coincidem.')
    setLoading(true)
    try {
      await api.post('/auth/password-reset/confirm/', { uid, token, ...form })
      setDone(true)
      setMessage('Senha alterada com sucesso.')
    } catch (error) {
      const data = error.response?.data
      setMessage(data?.password?.[0] || data?.token?.[0] || data?.re_password?.[0] || 'Não foi possível alterar a senha. Solicite um novo link.')
    } finally {
      setLoading(false)
    }
  }

  return <main className="auth-shell"><form className="auth-card" onSubmit={submit}>
    <h1>Nova senha</h1>
    {!uid || !token ? <div className="alert alert-error">Link inválido. Solicite uma nova recuperação.</div> : !done && <>
      <label>Nova senha<input required type="password" minLength="8" autoComplete="new-password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></label>
      <div className="password-rules">No mínimo 8 caracteres, uma letra maiúscula, um número e um símbolo.</div>
      <label>Repita a senha<input required type="password" autoComplete="new-password" value={form.re_password} onChange={(event) => setForm({ ...form, re_password: event.target.value })} /></label>
      <button className="button button-primary button-full" disabled={loading}>{loading ? 'Salvando...' : 'Alterar senha'}</button>
    </>}
    {message && <div className={done ? 'alert alert-info' : 'alert alert-error'} role="status">{message}</div>}
    <Link to={done ? '/entrar' : '/esqueci-senha'}>{done ? 'Entrar' : 'Solicitar novo link'}</Link>
  </form></main>
}
