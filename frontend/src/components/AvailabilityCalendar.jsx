import { useEffect, useState } from 'react'
import api from '../api/client'

const weekdays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
const dateKey = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`

export default function AvailabilityCalendar({ spaceId }) {
  const [month, setMonth] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1))
  const [periods, setPeriods] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [retry, setRetry] = useState(0)
  const year = month.getFullYear()
  const monthIndex = month.getMonth()
  const days = new Date(year, monthIndex + 1, 0).getDate()

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    setSelected(null)
    const from = dateKey(new Date(year, monthIndex, 1))
    const to = dateKey(new Date(year, monthIndex + 1, 1))
    api.get(`/spaces/${spaceId}/availability/`, { params: { from, to } })
      .then(({ data }) => { if (active) setPeriods(data) })
      .catch(() => { if (active) setError('Não foi possível carregar a disponibilidade.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [spaceId, year, monthIndex, retry])

  const periodsForDay = (day) => {
    const start = new Date(year, monthIndex, day)
    const end = new Date(year, monthIndex, day + 1)
    return periods.filter((period) => new Date(period.start_at) < end && new Date(period.end_at) > start)
  }
  const blanks = Array.from({ length: new Date(year, monthIndex, 1).getDay() }, (_, index) => <span key={`blank-${index}`} />)

  return <section className="availability-calendar" aria-label="Disponibilidade do anúncio">
    <h3>Disponibilidade</h3>
    <div className="calendar-heading">
      <button type="button" onClick={() => setMonth(new Date(year, monthIndex - 1, 1))} aria-label="Mês anterior">‹</button>
      <strong>{month.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}</strong>
      <button type="button" onClick={() => setMonth(new Date(year, monthIndex + 1, 1))} aria-label="Próximo mês">›</button>
    </div>
    {error && <div className="alert alert-error">{error} <button type="button" onClick={() => setRetry((value) => value + 1)}>Tentar novamente</button></div>}
    {loading ? <p className="muted">Carregando disponibilidade...</p> : !error && <>
      <div className="calendar-grid">
        {weekdays.map((day) => <strong key={day}>{day}</strong>)}
        {blanks}
        {Array.from({ length: days }, (_, index) => {
          const day = index + 1
          const busy = periodsForDay(day).length > 0
          return <button type="button" key={day} onClick={() => setSelected(day)} className={`${busy ? 'calendar-busy' : ''} ${selected === day ? 'calendar-selected' : ''}`} aria-label={`${day} de ${month.toLocaleDateString('pt-BR', { month: 'long' })}${busy ? ', com reserva' : ', sem reserva'}`} aria-pressed={selected === day}>{day}</button>
        })}
      </div>
      <p className="calendar-legend"><span /> Com reserva pendente ou confirmada. Toque em uma data para ver os horários.</p>
      {selected && <div className="calendar-periods"><strong>{selected} de {month.toLocaleDateString('pt-BR', { month: 'long' })}</strong>
        {periodsForDay(selected).length ? periodsForDay(selected).map((period, index) => <p key={index}>{new Date(period.start_at).toLocaleString('pt-BR')} até {new Date(period.end_at).toLocaleString('pt-BR')}</p>) : <p>Sem reservas nesta data.</p>}
      </div>}
    </>}
  </section>
}
