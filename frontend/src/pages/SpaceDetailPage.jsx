import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '../api/client'
import AvailabilityCalendar from '../components/AvailabilityCalendar'
import { useAuth } from '../context/AuthContext'
import { apiError } from '../api/errors'
import RegionMap from '../components/RegionMap'
import Reviews from '../components/Reviews'
import { vehicleLabels } from '../components/SpaceForm'

const labels = { garage: 'Garagem', parking: 'Vaga', warehouse: 'Galpão', hour: 'hora', day: 'dia', month: 'mês' }

export default function SpaceDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [space, setSpace] = useState(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [photoIndex, setPhotoIndex] = useState(0)
  const [reservation, setReservation] = useState({ start_at: '', end_at: '' })
  const [quote, setQuote] = useState(null)
  const [busy, setBusy] = useState(false)
  const [accepted, setAccepted] = useState(false)
  const [availabilityVersion, setAvailabilityVersion] = useState(0)
  const touchStart = useRef(null)
  const changeDates = (value) => { setReservation(value); setQuote(null); setAccepted(false); setMessage('') }

  const load = async () => {
    try {
      const { data } = await api.get(`/spaces/${id}/`)
      setSpace(data)
    } catch (error) {
      setMessage(apiError(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { setPhotoIndex(0); load() }, [id])

  const toggleFavorite = async () => {
    if (!user) return navigate('/entrar', { state: { from: `/espacos/${id}` } })
    if (space.is_favorite) await api.delete(`/spaces/${id}/favorite/`)
    else await api.post(`/spaces/${id}/favorite/`)
    await load()
  }

  const book = async (event) => {
    event.preventDefault()
    setMessage('')
    if (!user) return navigate('/entrar', { state: { from: `/espacos/${id}` } })
    if (busy) return
    if (new Date(reservation.end_at) <= new Date(reservation.start_at)) return setMessage('O fim deve ser posterior ao início.')
    setBusy(true)
    try {
      const payload = { space: Number(id), start_at: new Date(reservation.start_at).toISOString(), end_at: new Date(reservation.end_at).toISOString() }
      if (!quote) {
        const { data } = await api.post('/reservations/quote/', payload)
        setQuote(data)
      } else {
        if (!accepted) return setMessage('Leia e aceite as condições de cancelamento.')
        const { data } = await api.post('/reservations/', { ...payload, expected_total: quote.total_amount })
        setMessage(`Solicitação #${data.id} enviada ao proprietário. Total: ${Number(data.total_amount).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}. Acompanhe em Reservas.`)
        setQuote(null); setAccepted(false); setReservation({ start_at: '', end_at: '' }); setAvailabilityVersion((v) => v + 1)
      }
    } catch (error) {
      setQuote(null); setAccepted(false)
      setMessage(apiError(error, 'Não foi possível solicitar a reserva.'))
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <div className="page-center">Carregando...</div>
  if (!space) return <div className="page-center">{message || 'Anúncio não encontrado.'}</div>
  const photos = space.images?.length ? space.images : (space.cover_image ? [{ url: space.cover_image }] : [])
  const activePhoto = photos[photoIndex] || photos[0]

  return (
    <main className="container section">
      <div className="detail-grid">
        <section>
          {activePhoto ? (
            <div className="photo-gallery">
              <div className="photo-stage" onTouchStart={(e) => { touchStart.current = e.touches[0].clientX }} onTouchEnd={(e) => { if (touchStart.current != null && Math.abs(e.changedTouches[0].clientX - touchStart.current) > 50) setPhotoIndex((photoIndex + (e.changedTouches[0].clientX < touchStart.current ? 1 : -1) + photos.length) % photos.length); touchStart.current = null }}>
                <img className="detail-image" src={activePhoto.url} alt={`${space.title}, foto ${photoIndex + 1} de ${photos.length}`} />
                {photos.length > 1 && <>
                  <button type="button" className="photo-arrow photo-prev" aria-label="Foto anterior" onClick={() => setPhotoIndex((photoIndex - 1 + photos.length) % photos.length)}>‹</button>
                  <button type="button" className="photo-arrow photo-next" aria-label="Próxima foto" onClick={() => setPhotoIndex((photoIndex + 1) % photos.length)}>›</button>
                </>}
              </div>
              {photos.length > 1 && <div className="photo-thumbnails" aria-label="Fotos do anúncio">
                {photos.map((photo, index) => <button type="button" key={photo.id ?? index} className={index === photoIndex ? 'photo-thumbnail active' : 'photo-thumbnail'} aria-label={`Mostrar foto ${index + 1}`} aria-current={index === photoIndex ? 'true' : undefined} onClick={() => setPhotoIndex(index)}><img src={photo.url} alt="" /></button>)}
              </div>}
            </div>
          ) : <div className="detail-image placeholder">Garage Rent</div>}
          <div className="detail-title-row">
            <div>
              <span className="eyebrow">{labels[space.space_type]}</span>
              <h1>{space.title}</h1>
              <p className="muted">{space.public_location}</p>
            </div>
            {!space.is_owner && <button className="button button-secondary" onClick={toggleFavorite}>{space.is_favorite ? '★ Favoritado' : '☆ Favoritar'}</button>}
          </div>
          {space.is_owner && !space.is_active && <div className="alert alert-info">Este anúncio está pausado e não aparece para outros usuários.</div>}
          <p className="detail-description">{space.description}</p>
          <p>Anunciado por <strong>{space.owner.username}</strong> {space.owner.email_verified && <span className="status">E-mail verificado</span>}</p>
          <h2>Veículos aceitos</h2><div className="feature-grid">{space.accepted_vehicles?.length ? space.accepted_vehicles.map((vehicle) => <span key={vehicle}>{vehicleLabels[vehicle]}</span>) : <p className="muted">Não informado pelo proprietário.</p>}</div>

          <h2>Comodidades</h2>
          <div className="feature-grid">
            {space.covered && <span>Coberta</span>}
            {space.electric_gate && <span>Portão elétrico</span>}
            {space.security_camera && <span>Câmeras</span>}
            {space.access_24h && <span>Acesso 24h</span>}
            {space.lighting && <span>Iluminação</span>}
            {space.electricity && <span>Energia</span>}
            {space.restroom && <span>Banheiro</span>}
          </div>

          {(space.length_m || space.width_m || space.height_m) && (
            <div className="dimensions">
              <strong>Dimensões:</strong><p>Comprimento: {space.length_m ? `${space.length_m} m` : 'não informado'} · Largura: {space.width_m ? `${space.width_m} m` : 'não informada'}</p><p>Altura máxima: {space.height_m ? `${space.height_m} m` : 'não informada'}</p>
            </div>
          )}

          {space.exact_address && (
            <div className="alert alert-info"><strong>Endereço completo:</strong> {space.exact_address.address_line} {space.exact_address.postal_code}</div>
          )}
          {space.latitude != null && <section><h2>Região aproximada</h2><RegionMap position={space} /><p className="muted">O mapa mostra apenas a região. O endereço completo é liberado após a confirmação da reserva.</p></section>}
          <Reviews key={id} spaceId={id} />
        </section>

        <aside className="booking-card" id="reservar">
          <div className="space-price big-price">
            <strong>{Number(space.price).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</strong>
            <span>/{labels[space.billing_period]}</span>
          </div>
          {space.is_owner ? (
            <div className="stack-form">
              <p>Este anúncio é seu.</p>
              <Link className="button button-primary button-full" to={`/meus-anuncios/${space.id}/editar`}>Editar anúncio</Link>
              <Link className="button button-secondary button-full" to="/meus-anuncios">Meus anúncios</Link>
            </div>
          ) : (
            <div className="stack-form">
            <AvailabilityCalendar key={availabilityVersion} spaceId={id} />
            <form onSubmit={book} className="stack-form">
              <label>Início<input required disabled={busy} type="datetime-local" value={reservation.start_at} onChange={(e) => changeDates({ ...reservation, start_at: e.target.value })} /></label>
              <label>Fim<input required disabled={busy} type="datetime-local" min={reservation.start_at} value={reservation.end_at} onChange={(e) => changeDates({ ...reservation, end_at: e.target.value })} /></label>
              <p className="muted">Cobrança por {labels[space.billing_period]} iniciado{space.billing_period === 'month' ? ' (blocos de 30 dias)' : ''}. Horários no fuso do seu dispositivo.</p>
              {quote && <div className="quote-summary" role="status"><strong>Total: {Number(quote.total_amount).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</strong><p>{quote.cancellation_policy}</p><small>{quote.detail}</small><label className="check"><input required type="checkbox" checked={accepted} onChange={(e) => setAccepted(e.target.checked)} />Li e aceito as condições de cancelamento.</label></div>}
              <button disabled={busy || (quote && !accepted)} className="button button-primary button-full">{busy ? 'Aguarde...' : quote ? 'Confirmar solicitação' : 'Consultar total e disponibilidade'}</button>
              <small>O proprietário precisa confirmar a solicitação.</small>
            </form>
            </div>
          )}
          {message && <div className="alert alert-info" role="status">{message}</div>}
        </aside>
      </div>
      {!space.is_owner && <a className="mobile-booking button button-primary" href="#reservar">Ver disponibilidade e reservar</a>}
    </main>
  )
}
