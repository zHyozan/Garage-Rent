import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

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

  const load = async () => {
    try {
      const { data } = await api.get(`/spaces/${id}/`)
      setSpace(data)
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
    try {
      await api.post('/reservations/', { space: Number(id), ...reservation })
      setMessage('Solicitação de reserva enviada ao proprietário.')
    } catch (error) {
      const data = error.response?.data
      setMessage(data?.non_field_errors?.[0] || data?.detail || (typeof data === 'string' ? data : 'Não foi possível solicitar a reserva.'))
    }
  }

  if (loading) return <div className="page-center">Carregando...</div>
  if (!space) return <div className="page-center">Anúncio não encontrado.</div>
  const photos = space.images?.length ? space.images : (space.cover_image ? [{ url: space.cover_image }] : [])
  const activePhoto = photos[photoIndex] || photos[0]

  return (
    <main className="container section">
      <div className="detail-grid">
        <section>
          {activePhoto ? (
            <div className="photo-gallery">
              <div className="photo-stage">
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
              <strong>Dimensões:</strong> {space.length_m || '?'}m × {space.width_m || '?'}m × {space.height_m || '?'}m
            </div>
          )}

          {space.exact_address && (
            <div className="alert alert-info"><strong>Endereço completo:</strong> {space.exact_address.address_line} {space.exact_address.postal_code}</div>
          )}
        </section>

        <aside className="booking-card">
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
            <form onSubmit={book} className="stack-form">
              <label>Início<input required type="datetime-local" value={reservation.start_at} onChange={(e) => setReservation({ ...reservation, start_at: e.target.value })} /></label>
              <label>Fim<input required type="datetime-local" value={reservation.end_at} onChange={(e) => setReservation({ ...reservation, end_at: e.target.value })} /></label>
              <button className="button button-primary button-full">Solicitar reserva</button>
              <small>O proprietário precisa confirmar a solicitação.</small>
            </form>
          )}
          {message && <div className="alert alert-info">{message}</div>}
        </aside>
      </div>
    </main>
  )
}
