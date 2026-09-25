import { Link } from 'react-router-dom'

const labels = {
  garage: 'Garagem',
  parking: 'Vaga',
  warehouse: 'Galpão',
  hour: 'hora',
  day: 'dia',
  month: 'mês',
}

export default function SpaceCard({ space }) {
  return (
    <Link to={`/espacos/${space.id}`} className="space-card">
      <div className="space-image-wrap">
        {space.cover_image ? (
          <img className="space-image" src={space.cover_image} alt={space.title} />
        ) : (
          <div className="space-image placeholder">Garage Rent</div>
        )}
        <span className="badge">{labels[space.space_type]}</span>
      </div>
      <div className="space-card-body">
        {space.is_promoted && <span className="sponsored-label">Patrocinado</span>}
        <div className="space-location">{space.public_location}</div>
        {space.distance_km != null && <small>Aproximadamente {space.distance_km} km em linha reta</small>}
        <h3>{space.title}</h3>
        <p className="muted">{{ available: 'Disponível', negotiating: 'Em negociação', rented: 'Alugado' }[space.availability_status]}</p>
        <div className="space-meta">
          {space.covered && <span>Coberta</span>}
          {space.access_24h && <span>24h</span>}
          {space.security_camera && <span>Câmeras</span>}
          {space.height_m && <span>Altura máx. {space.height_m} m</span>}
          {space.owner.email_verified && <span>E-mail verificado</span>}
        </div>
        {space.rating?.count > 0 && <p>★ {space.rating.average} · {space.rating.count} avaliação(ões) de atendimento</p>}
        <div className="space-price">
          <strong>{Number(space.price).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</strong>
          <span>/{labels[space.billing_period]}</span>
        </div>
      </div>
    </Link>
  )
}
