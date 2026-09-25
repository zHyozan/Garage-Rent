import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../api/client'
import { apiError } from '../api/errors'

const money = (value) => Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const statuses = { pending: 'Aguardando confirmação do pagamento externo', active: 'Destaque ativo', expired: 'Destaque encerrado', cancelled: 'Solicitação cancelada' }

export default function ListingResultsPage() {
  const { id } = useParams()
  const [space, setSpace] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [inquiries, setInquiries] = useState([])
  const [page, setPage] = useState(1)
  const [next, setNext] = useState(false)
  const [packages, setPackages] = useState([])
  const [promotions, setPromotions] = useState([])
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const load = async () => {
    try {
      const [s, m, p, offers] = await Promise.all([api.get(`/spaces/${id}/`), api.get(`/portal/${id}/metrics/`), api.get(`/portal/${id}/promotions/`), api.get('/portal/packages/')])
      setSpace(s.data); setMetrics(m.data); setPromotions(p.data); setPackages(offers.data)
    } catch (error) { setMessage(apiError(error)) }
  }
  const loadInquiries = async (number = 1) => {
    try { const { data } = await api.get(`/portal/${id}/inquiries/`, { params: { page: number } }); setInquiries(data.results); setNext(Boolean(data.next)); setPage(number) }
    catch (error) { setMessage(apiError(error)) }
  }
  useEffect(() => { load(); loadInquiries() }, [id])
  const request = async (action, payload = {}) => {
    setBusy(true); setMessage('')
    try { await api.post(`/portal/${id}/${action}/`, payload); await load(); setMessage(action === 'promotions' ? 'Pedido registrado. Veja as instruções abaixo. O destaque começa após a confirmação administrativa.' : 'Solicitação cancelada.') }
    catch (error) { setMessage(apiError(error)) } finally { setBusy(false) }
  }
  return <main className="container section">
    <Link to="/meus-anuncios">← Meus anúncios</Link><h1>Resultados e destaque</h1>
    {message && <p className="alert alert-info" role="status">{message}</p>}
    {space && metrics && <>
      <h2>{space.title}</h2><p>Últimos 30 dias. Cliques indicam intenção de contato, não locações. Visualizações e cliques são limitados a um registro por visitante, canal e dia; suas próprias visitas não contam.</p>
      <div className="metrics-grid">{[['Visualizações', metrics.views], ['Cliques no WhatsApp', metrics.whatsapp_clicks], ['Cliques no telefone', metrics.phone_clicks], ['Mensagens recebidas', metrics.inquiries]].map(([label, value]) => <article className="metric-card" key={label}><strong>{value}</strong><span>{label}</span></article>)}</div>
      <section className="form-card"><span className="eyebrow">Publicação gratuita · destaque opcional</span><h2>Dê mais visibilidade ao seu espaço</h2><p>Seu anúncio aparece como Patrocinado antes dos anúncios comuns que atendem aos filtros da busca. Sem promessa de contatos ou locação. Anúncios pausados, alugados ou ocultos deixam de aparecer; o prazo do destaque continua correndo.</p>
        {!packages.length && <p>Nenhum pacote disponível no momento. A publicação gratuita continua disponível.</p>}
        {packages.map((offer) => <div className="promotion-offer" key={offer.id}><h3>{offer.name}</h3><p><strong>{money(offer.price)}</strong> por {offer.days} dias, contados da ativação.</p><p>Pagamento fora do site e confirmação manual. Sem renovação automática.</p><p className="preserve-lines">{offer.instructions}</p><button className="button button-primary" disabled={busy || promotions.some((p) => ['pending', 'active'].includes(p.status)) || !space.is_active || space.moderated || space.availability_status === 'rented'} onClick={() => request('promotions', { package: offer.id })}>Solicitar destaque</button></div>)}
        {promotions.map((p) => <article className="promotion-order" key={p.id}><h3>Pedido #{p.id} · {statuses[p.status]}</h3><p>{money(p.price)} · {p.days} dias</p>{p.status === 'pending' && <><p className="preserve-lines">{p.instructions}</p><p>Consulte esta página para acompanhar instruções e confirmação. O pedido por si só não ativa o destaque.</p><button disabled={busy} className="button button-secondary" onClick={() => request('cancel_promotion')}>Cancelar solicitação</button></>}{p.ends_at && <p>Período contratado: {new Date(p.starts_at).toLocaleString('pt-BR')} até {new Date(p.ends_at).toLocaleString('pt-BR')}.</p>}</article>)}
      </section>
      <section><h2>Contatos recebidos</h2><p>Responda diretamente pelo e-mail ou telefone fornecido. Use os dados apenas para atender à solicitação.</p>
        {inquiries.length ? inquiries.map((item) => <article className="form-card" key={item.id}><strong>{item.sender_name}</strong><p className="preserve-lines">{item.message}</p><div className="row-actions">{item.sender_email && <a href={`mailto:${item.sender_email}`}>Responder por e-mail</a>}{item.reply_phone && <a href={`tel:+${item.reply_phone}`}>Ligar: +{item.reply_phone}</a>}</div><small>{new Date(item.created_at).toLocaleString('pt-BR')}</small></article>) : <p>Nenhuma mensagem recebida.</p>}
        {(next || page > 1) && <div className="row-actions"><button disabled={page === 1} onClick={() => loadInquiries(page - 1)}>Anterior</button><span>Página {page}</span><button disabled={!next} onClick={() => loadInquiries(page + 1)}>Próxima</button></div>}
      </section>
    </>}
  </main>
}
