import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../api/client'
import { apiError } from '../api/errors'

const types = { garage: 'Garagem', parking: 'Vaga', warehouse: 'Galpão' }
const periods = { hour: 'Hora', day: 'Dia', month: 'Mês' }

export default function AlertsPage() {
  const [params] = useSearchParams()
  const [form, setForm] = useState({ location: params.get('location') || '', space_type: params.get('space_type') || '', billing_period: params.get('billing_period') || '', min_price: params.get('min_price') || '', max_price: params.get('max_price') || '', consent: false })
  const [alerts, setAlerts] = useState([])
  const [page, setPage] = useState(1)
  const [next, setNext] = useState(false)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const load = async (number = 1) => {
    try { const { data } = await api.get('/alerts/', { params: { page: number } }); setAlerts(data.results); setPage(number); setNext(Boolean(data.next)) }
    catch (error) { setMessage(apiError(error)) }
  }
  useEffect(() => { load() }, [])
  const save = async (event) => {
    event.preventDefault(); setBusy(true); setMessage('')
    try { await api.post('/alerts/', { ...form, min_price: form.min_price || null, max_price: form.max_price || null }); await load(); setMessage('Alerta salvo. Confirme seu e-mail para receber novas ofertas.'); setForm({ ...form, consent: false }) }
    catch (error) { setMessage(apiError(error)) } finally { setBusy(false) }
  }
  const change = async (alert, remove = false) => {
    setBusy(true); setMessage('')
    try { if (remove) await api.delete(`/alerts/${alert.id}/`); else await api.patch(`/alerts/${alert.id}/`, { is_active: !alert.is_active }); await load() }
    catch (error) { setMessage(apiError(error)) } finally { setBusy(false) }
  }
  const input = (key, value) => setForm({ ...form, [key]: value })
  return <main className="container section narrow"><h1>Meus alertas</h1><p>Salve uma região e receba por e-mail novos anúncios que atendam à sua busca. Você pode pausar ou excluir cada alerta a qualquer momento.</p>
    <form className="form-card stack-form" onSubmit={save}>
      <label>Cidade ou bairro<input required maxLength="100" value={form.location} onChange={(e) => input('location', e.target.value)} /></label>
      <div className="form-grid two"><label>Tipo<select value={form.space_type} onChange={(e) => input('space_type', e.target.value)}><option value="">Todos</option>{Object.entries(types).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label><label>Período<select value={form.billing_period} onChange={(e) => input('billing_period', e.target.value)}><option value="">Todos</option>{Object.entries(periods).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label></div>
      <div className="form-grid two"><label>Preço mínimo (R$)<input type="number" min="0" step="0.01" value={form.min_price} onChange={(e) => input('min_price', e.target.value)} /></label><label>Preço máximo (R$)<input type="number" min="0" step="0.01" value={form.max_price} onChange={(e) => input('max_price', e.target.value)} /></label></div>
      <label className="check"><input required type="checkbox" checked={form.consent} onChange={(e) => input('consent', e.target.checked)} />Autorizo o envio de novas ofertas desta busca ao e-mail da minha conta.</label>
      <button className="button button-primary" disabled={busy}>Criar alerta gratuito</button>
    </form>
    {message && <p className="alert alert-info" role="status">{message}</p>}
    <h2>Buscas salvas</h2>{alerts.length ? alerts.map((a) => <article className="form-card" key={a.id}><strong>{a.location} · {a.is_active ? 'Ativo' : 'Pausado'}</strong><p>{types[a.space_type] || 'Todos os tipos'} · {periods[a.billing_period] || 'Todos os períodos'} · R$ {a.min_price ?? '0'} até {a.max_price ? `R$ ${a.max_price}` : 'sem limite'}</p><div className="row-actions"><button className="button button-secondary" disabled={busy} onClick={() => change(a)}>{a.is_active ? 'Pausar' : 'Reativar'}</button><button className="button button-danger" disabled={busy} onClick={() => change(a, true)}>Excluir</button></div></article>) : <p>Nenhum alerta salvo.</p>}
    {(next || page > 1) && <div className="row-actions"><button disabled={page === 1} onClick={() => load(page - 1)}>Anterior</button><span>Página {page}</span><button disabled={!next} onClick={() => load(page + 1)}>Próxima</button></div>}
  </main>
}
