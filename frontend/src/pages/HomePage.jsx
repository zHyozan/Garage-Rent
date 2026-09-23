import { useEffect, useState } from 'react'
import api from '../api/client'
import SpaceCard from '../components/SpaceCard'
import RegionMap from '../components/RegionMap'
import { apiError } from '../api/errors'

const initialFilters = {
  search: '',
  location: '',
  space_type: '',
  billing_period: '',
  ordering: '-created_at',
  covered: '', access_24h: '', vehicle: '', min_price: '', max_price: '',
}

export default function HomePage({ favoritesOnly = false }) {
  const [spaces, setSpaces] = useState([])
  const [filters, setFilters] = useState(initialFilters)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [nearby, setNearby] = useState(null)
  const [radius, setRadius] = useState('10')
  const [view, setView] = useState('list')
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [locating, setLocating] = useState(false)

  const loadSpaces = async (nextPage = 1, location = nearby) => {
    setLoading(true)
    setError('')
    try {
      const endpoint = favoritesOnly ? '/spaces/favorites/' : '/spaces/'
      const params = favoritesOnly ? { page: nextPage } : { ...Object.fromEntries(Object.entries(filters).filter(([, value]) => value)), page: nextPage, ...(location ? { lat: location.lat, lng: location.lng, radius } : {}) }
      const { data } = await api.get(endpoint, { params })
      setSpaces(data.results || data)
      setPage(nextPage)
      setHasNext(Boolean(data.next))
    } catch (err) {
      setError(apiError(err, 'Não foi possível carregar os espaços.'))
      setSpaces([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSpaces()
  }, [favoritesOnly])

  const submit = (event) => {
    event.preventDefault()
    loadSpaces()
  }

  const locate = () => {
    if (!navigator.geolocation) return setError('Seu navegador não oferece localização. Busque pela cidade ou bairro.')
    setLocating(true)
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      const location = { lat: Number(coords.latitude.toFixed(2)), lng: Number(coords.longitude.toFixed(2)) }
      setNearby(location)
      setLocating(false)
      loadSpaces(1, location)
    }, () => { setLocating(false); setError('Localização indisponível ou sem permissão. Busque pela cidade ou bairro.') }, { timeout: 10000 })
  }

  return (
    <main>
      {!favoritesOnly && (
        <section className="hero">
          <div className="container hero-grid">
            <div>
              <span className="eyebrow">Espaço parado vira renda</span>
              <h1>Encontre a garagem ou o galpão certo para você.</h1>
              <p>Alugue espaços particulares com praticidade, transparência e foco exclusivo em garagens, vagas e galpões.</p>
            </div>
            <div className="hero-stat-card">
              <strong>Garage Rent</strong>
              <span>Um marketplace feito para espaços que os portais imobiliários tradicionais tratam como detalhe.</span>
            </div>
          </div>
        </section>
      )}

      <section className="container section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">{favoritesOnly ? 'Sua seleção' : 'Espaços disponíveis'}</span>
            <h2>{favoritesOnly ? 'Favoritos' : 'Explore oportunidades perto de você'}</h2>
          </div>
        </div>

        {!favoritesOnly && (
          <form className="filter-bar" onSubmit={submit}>
            <input aria-label="Buscar anúncio" placeholder="Buscar anúncio" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
            <input aria-label="Cidade ou bairro" placeholder="Cidade ou bairro" value={filters.location} onChange={(e) => setFilters({ ...filters, location: e.target.value })} />
            <select aria-label="Tipo de espaço" value={filters.space_type} onChange={(e) => setFilters({ ...filters, space_type: e.target.value })}>
              <option value="">Todos os tipos</option>
              <option value="garage">Garagem</option>
              <option value="parking">Vaga</option>
              <option value="warehouse">Galpão</option>
            </select>
            <select aria-label="Período de cobrança" value={filters.billing_period} onChange={(e) => setFilters({ ...filters, billing_period: e.target.value })}>
              <option value="">Qualquer período</option>
              <option value="hour">Por hora</option>
              <option value="day">Por dia</option>
              <option value="month">Por mês</option>
            </select>
            <select aria-label="Ordenar resultados" value={filters.ordering} onChange={(e) => setFilters({ ...filters, ordering: e.target.value })}>
              <option value="-created_at">Mais recentes</option>
              <option value="price">Menor preço</option>
              <option value="-price">Maior preço</option>
              {nearby && <option value="distance">Mais próximos</option>}
            </select>
            <button className="button button-primary" type="submit" disabled={loading}>Buscar</button>
            <details className="extra-filters"><summary>Mais filtros e proximidade</summary><div className="form-grid three">
              <label>Preço mínimo (R$)<input type="number" min="0" step="0.01" value={filters.min_price} onChange={(e) => setFilters({ ...filters, min_price: e.target.value })} /></label>
              <label>Preço máximo (R$)<input type="number" min="0" step="0.01" value={filters.max_price} onChange={(e) => setFilters({ ...filters, max_price: e.target.value })} /></label>
              <label>Veículo<select value={filters.vehicle} onChange={(e) => setFilters({ ...filters, vehicle: e.target.value })}><option value="">Todos</option><option value="motorcycle">Moto</option><option value="car">Carro</option><option value="suv">SUV</option><option value="van">Van</option><option value="truck">Caminhão</option><option value="bicycle">Bicicleta</option></select></label>
              <label className="check"><input type="checkbox" checked={filters.covered === 'true'} onChange={(e) => setFilters({ ...filters, covered: e.target.checked ? 'true' : '' })} />Somente cobertas</label>
              <label className="check"><input type="checkbox" checked={filters.access_24h === 'true'} onChange={(e) => setFilters({ ...filters, access_24h: e.target.checked ? 'true' : '' })} />Acesso 24h</label>
              <label>Raio aproximado<select value={radius} onChange={(e) => setRadius(e.target.value)}>{[5, 10, 25, 50, 100].map((km) => <option key={km} value={km}>{km} km</option>)}</select></label>
            </div><button type="button" className="button button-secondary" disabled={locating || loading} onClick={locate}>{locating ? 'Localizando...' : 'Buscar perto de mim'}</button>
            {nearby && <button type="button" className="link-button" onClick={() => { setNearby(null); loadSpaces(1, null) }}>Remover proximidade</button>}
            <p className="muted">Distâncias aproximadas em linha reta. Anúncios sem região cadastrada aparecem apenas na busca por cidade ou bairro.</p></details>
          </form>
        )}

        <div className="view-controls"><button className="button button-secondary" aria-pressed={view === 'list'} onClick={() => setView('list')}>Lista</button><button className="button button-secondary" aria-pressed={view === 'map'} onClick={() => setView('map')}>Mapa</button></div>
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        {!loading && view === 'map' && <><RegionMap spaces={spaces} /><p className="muted">Regiões aproximadas dos anúncios desta página. O endereço completo fica protegido. {spaces.filter((s) => s.latitude == null).length} anúncio(s) desta página sem região no mapa.</p></>}
        {loading ? (
          <div className="empty-state">Carregando espaços...</div>
        ) : spaces.length ? (
          <div className="space-grid">{spaces.map((space) => <SpaceCard key={space.id} space={space} />)}</div>
        ) : (
          <div className="empty-state">Nenhum espaço encontrado.</div>
        )}
        <div className="pagination"><button className="button button-secondary" disabled={loading || page === 1} onClick={() => loadSpaces(page - 1)}>Anterior</button><span>Página {page}</span><button className="button button-secondary" disabled={loading || !hasNext} onClick={() => loadSpaces(page + 1)}>Próxima</button></div>
      </section>
    </main>
  )
}
