import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '../api/client'
import SpaceForm, { buildSpaceFormData } from '../components/SpaceForm'

export default function EditSpacePage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [space, setSpace] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    setSpace(null)
    api.get(`/spaces/${id}/`).then(({ data }) => {
      if (!active) return
      if (!data.is_owner) {
        setError('Você não pode editar este anúncio.')
        return
      }
      setSpace({ ...data, ...data.exact_address })
    }).catch(() => {
      if (active) setError('Não foi possível carregar o anúncio.')
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [id])

  const submit = async (form, images) => {
    setSaving(true)
    setError('')
    try {
      await api.patch(`/spaces/${id}/`, buildSpaceFormData(form, images))
      navigate(`/espacos/${id}`)
    } catch (err) {
      setError(err.response?.data ? JSON.stringify(err.response.data) : 'Não foi possível salvar o anúncio.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <main className="container section narrow">
      <div className="section-heading"><h1>Editar anúncio</h1><Link to="/meus-anuncios">Meus anúncios</Link></div>
      {loading ? <div className="empty-state">Carregando...</div> : space ? (
        <SpaceForm key={id} initialValues={space} onSubmit={submit} error={error} loading={saving} submitLabel="Salvar alterações" loadingLabel="Salvando..." />
      ) : <div className="alert alert-error">{error}</div>}
    </main>
  )
}
