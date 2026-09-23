import { useEffect, useState } from 'react'
import api from '../api/client'
import { apiError } from '../api/errors'

export default function Reviews({ spaceId }) {
  const [items, setItems] = useState([])
  const [page, setPage] = useState(1)
  const [next, setNext] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    api.get(`/spaces/${spaceId}/reviews/`, { params: { page } }).then(({ data }) => { if (active) { setItems(data.results); setNext(Boolean(data.next)); setError('') } }).catch((err) => { if (active) setError(apiError(err)) })
    return () => { active = false }
  }, [spaceId, page])
  return <section className="reviews"><h2>Avaliações de locações concluídas</h2>{error && <p role="alert">{error}</p>}{!items.length && !error && <p className="muted">Nenhuma avaliação ainda.</p>}{items.map((item) => <article className="review" key={item.id}><strong>{item.score}/5 · {item.author}</strong><p>{item.comment || 'Sem comentário.'}</p><small>{new Date(item.created_at).toLocaleDateString('pt-BR')}</small></article>)}{(page > 1 || next) && <div className="pagination"><button disabled={page === 1} onClick={() => setPage(page - 1)}>Anterior</button><span>Página {page}</span><button disabled={!next} onClick={() => setPage(page + 1)}>Próxima</button></div>}</section>
}
