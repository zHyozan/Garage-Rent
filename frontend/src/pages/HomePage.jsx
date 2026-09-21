import { useEffect, useState } from 'react'
import api from '../api/client'
import SpaceCard from '../components/SpaceCard'

const initialFilters = {
  search: '',
  location: '',
  space_type: '',
  billing_period: '',
  ordering: '-created_at',
}

export default function HomePage({ favoritesOnly = false }) {
  const [spaces, setSpaces] = useState([])
  const [filters, setFilters] = useState(initialFilters)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadSpaces = async () => {
    setLoading(true)
    setError('')
    try {
      const endpoint = favoritesOnly ? '/spaces/favorites/' : '/spaces/'
      const params = favoritesOnly ? undefined : Object.fromEntries(Object.entries(filters).filter(([, value]) => value))
      const { data } = await api.get(endpoint, { params })
      setSpaces(data.results || data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Não foi possível carregar os espaços.')
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
            <input placeholder="Buscar anúncio" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
            <input placeholder="Cidade ou bairro" value={filters.location} onChange={(e) => setFilters({ ...filters, location: e.target.value })} />
            <select value={filters.space_type} onChange={(e) => setFilters({ ...filters, space_type: e.target.value })}>
              <option value="">Todos os tipos</option>
              <option value="garage">Garagem</option>
              <option value="parking">Vaga</option>
              <option value="warehouse">Galpão</option>
            </select>
            <select value={filters.billing_period} onChange={(e) => setFilters({ ...filters, billing_period: e.target.value })}>
              <option value="">Qualquer período</option>
              <option value="hour">Por hora</option>
              <option value="day">Por dia</option>
              <option value="month">Por mês</option>
            </select>
            <select value={filters.ordering} onChange={(e) => setFilters({ ...filters, ordering: e.target.value })}>
              <option value="-created_at">Mais recentes</option>
              <option value="price">Menor preço</option>
              <option value="-price">Maior preço</option>
            </select>
            <button className="button button-primary" type="submit">Buscar</button>
          </form>
        )}

        {error && <div className="alert alert-error">{error}</div>}
        {loading ? (
          <div className="empty-state">Carregando espaços...</div>
        ) : spaces.length ? (
          <div className="space-grid">{spaces.map((space) => <SpaceCard key={space.id} space={space} />)}</div>
        ) : (
          <div className="empty-state">Nenhum espaço encontrado.</div>
        )}
      </section>
    </main>
  )
}
