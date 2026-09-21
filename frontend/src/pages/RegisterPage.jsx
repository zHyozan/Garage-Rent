import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const [form, setForm] = useState({ username: '', email: '', password: '', re_password: '' })
  const [errors, setErrors] = useState([])
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const submit = async (event) => {
    event.preventDefault()
    setErrors([])
    setLoading(true)
    try {
      await register(form)
      navigate('/')
    } catch (error) {
      const data = error.response?.data || { detail: 'Não foi possível concluir o cadastro.' }
      const parsed = Object.entries(data).flatMap(([field, value]) => {
        const messages = Array.isArray(value) ? value : [value]
        return messages.map((message) => `${field === 'detail' ? '' : `${field}: `}${message}`)
      })
      setErrors(parsed)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-shell">
      <form className="auth-card" onSubmit={submit}>
        <span className="eyebrow">Comece agora</span>
        <h1>Criar sua conta</h1>
        <label>Usuário<input required value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} /></label>
        <label>E-mail<input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
        <label>Senha<input required type="password" minLength="8" aria-describedby="password-rules" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
        <div id="password-rules" className="password-rules">
          <strong>Requisitos da senha</strong>
          <ul>
            <li>No mínimo 8 caracteres.</li>
            <li>Pelo menos uma letra maiúscula, um número e um símbolo.</li>
            <li>Evite senhas comuns ou parecidas com seus dados.</li>
          </ul>
        </div>
        <label>Repita a senha<input required type="password" value={form.re_password} onChange={(e) => setForm({ ...form, re_password: e.target.value })} /></label>
        {errors.length > 0 && <div className="alert alert-error">{errors.map((item) => <div key={item}>{item}</div>)}</div>}
        <button disabled={loading} className="button button-primary button-full">{loading ? 'Criando...' : 'Criar conta'}</button>
        <p>Já tem conta? <Link to="/entrar">Entrar</Link></p>
      </form>
    </main>
  )
}
