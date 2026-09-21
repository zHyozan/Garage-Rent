import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import SpaceForm, { buildSpaceFormData } from '../components/SpaceForm'

export default function CreateSpacePage() {
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const submit = async (form, image) => {
    setLoading(true)
    setError('')
    try {
      const payload = buildSpaceFormData(form, image)
      const { data } = await api.post('/spaces/', payload, { headers: { 'Content-Type': 'multipart/form-data' } })
      navigate(`/espacos/${data.id}`)
    } catch (err) {
      const data = err.response?.data
      setError(data ? JSON.stringify(data) : 'Não foi possível criar o anúncio.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container section narrow">
      <div className="section-heading"><div><span className="eyebrow">Novo anúncio</span><h1>Anuncie seu espaço</h1></div></div>
      <SpaceForm
        onSubmit={submit}
        error={error}
        loading={loading}
        submitLabel="Publicar anúncio"
        loadingLabel="Publicando..."
      />
    </main>
  )
}
