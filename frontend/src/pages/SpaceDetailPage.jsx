import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '../api/client'
import ContactPanel from '../components/ContactPanel'
import ListingTrust from '../components/ListingTrust'
import { useAuth } from '../context/AuthContext'
import { apiError } from '../api/errors'
import RegionMap from '../components/RegionMap'
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
  const touchStart = useRef(null)

  const load = async () => {
    try {
      const { data } = await api.get(`/spaces/${id}/`)
      setSpace(data)
      if (!data.is_owner) api.post(`/portal/${id}/event/`, { kind: 'view' }).catch(() => {})
    } catch (error) {
      setMessage(apiError(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { setPhotoIndex(0); setSpace(null); setLoading(true); setMessage(''); load() }, [id])

  const toggleFavorite = async () => {
    if (!user) return navigate('/entrar', { state: { from: `/espacos/${id}` } })
    try {
      if (space.is_favorite) await api.delete(`/spaces/${id}/favorite/`)
      else await api.post(`/spaces/${id}/favorite/`)
      await load()
    } catch (error) { setMessage(apiError(error)) }
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
              <h1>{space.title}</h1>{space.is_promoted && <span className="sponsored-label">Patrocinado</span>}
              <p className="muted">{space.public_location}</p>
            </div>
            {!space.is_owner && <button className="button button-secondary" onClick={toggleFavorite}>{space.is_favorite ? '★ Favoritado' : '☆ Favoritar'}</button>}
          </div>
          {space.is_owner && !space.is_active && <div className="alert alert-info">Este anúncio está pausado e não aparece para outros usuários.</div>}
          {space.is_owner && space.moderated && <div className="alert alert-error">Este anúncio foi ocultado pela moderação.</div>}
          <p className="detail-description">{space.description}</p>
          <p>Anunciado por <Link to={`/?owner=${space.owner.id}`}>{space.owner.username}</Link> {space.owner.email_verified && <span className="status">E-mail verificado</span>}</p>
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
          {space.latitude != null && <section><h2>Região aproximada</h2><RegionMap position={space} /><p className="muted">O mapa mostra apenas a região. O proprietário compartilha o endereço completo durante a negociação.</p></section>}
          {!space.moderated && space.is_active && <ListingTrust key={id} space={space} />}
        </section>

        <aside className="booking-card" id="contato">
          <div className="space-price big-price">
            <strong>{Number(space.price).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</strong>
            <span>/{labels[space.billing_period]}</span>
          </div>
          {space.is_owner ? (
            <div className="stack-form">
              <p>Este anúncio é seu.</p>
              <Link className="button button-primary button-full" to={`/meus-anuncios/${space.id}/resultados`}>Resultados e destaque</Link>
              <Link className="button button-primary button-full" to={`/meus-anuncios/${space.id}/editar`}>Editar anúncio</Link>
              <Link className="button button-secondary button-full" to="/meus-anuncios">Meus anúncios</Link>
            </div>
          ) : <ContactPanel key={id} space={space} />}
          {message && <div className="alert alert-info" role="status">{message}</div>}
        </aside>
      </div>
      {!space.is_owner && <a className="mobile-booking button button-primary" href="#contato">Entrar em contato</a>}
    </main>
  )
}
