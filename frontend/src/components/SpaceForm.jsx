import { useEffect, useState } from 'react'
const empty = {
  space_type: 'garage', title: '', description: '', price: '', billing_period: 'month',
  state: 'SP', city: '', neighborhood: '', postal_code: '', address_line: '',
  length_m: '', width_m: '', height_m: '', covered: false, electric_gate: false,
  security_camera: false, access_24h: false, lighting: false, electricity: false, restroom: false,
}

export function buildSpaceFormData(form, image) {
  const payload = new FormData()
  Object.entries(form).forEach(([key, value]) => payload.append(key, value ?? ''))
  if (image) payload.append('cover_image', image)
  return payload
}

export default function SpaceForm({ initialValues = {}, onSubmit, error, loading, submitLabel, loadingLabel }) {
  const [form, setForm] = useState(() => Object.fromEntries(
    Object.entries(empty).map(([key, value]) => [key, initialValues[key] ?? value])
  ))
  const [image, setImage] = useState(null)
  const [preview, setPreview] = useState('')
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])
  const set = (field, value) => setForm((old) => ({ ...old, [field]: value }))
  const submit = (event) => {
    event.preventDefault()
    if (!loading) onSubmit(form, image)
  }
  const checkboxes = [
    ['covered', 'Coberta'], ['electric_gate', 'Portão elétrico'], ['security_camera', 'Câmeras'],
    ['access_24h', 'Acesso 24h'], ['lighting', 'Iluminação'], ['electricity', 'Energia'], ['restroom', 'Banheiro'],
  ]

  return (
      <form className="form-card" onSubmit={submit}>
        <div className="form-grid two">
          <label>Tipo<select value={form.space_type} onChange={(e) => set('space_type', e.target.value)}><option value="garage">Garagem</option><option value="parking">Vaga</option><option value="warehouse">Galpão</option></select></label>
          <label>Período de cobrança<select value={form.billing_period} onChange={(e) => set('billing_period', e.target.value)}><option value="hour">Hora</option><option value="day">Dia</option><option value="month">Mês</option></select></label>
        </div>
        <label>Título<input required value={form.title} onChange={(e) => set('title', e.target.value)} /></label>
        <label>Descrição<textarea required rows="5" value={form.description} onChange={(e) => set('description', e.target.value)} /></label>
        <label>Preço (R$)<input required type="number" min="0.01" step="0.01" value={form.price} onChange={(e) => set('price', e.target.value)} /></label>

        <h2>Localização</h2>
        <div className="form-grid three">
          <label>UF<input required maxLength="2" value={form.state} onChange={(e) => set('state', e.target.value.toUpperCase())} /></label>
          <label>Cidade<input required value={form.city} onChange={(e) => set('city', e.target.value)} /></label>
          <label>Bairro<input required value={form.neighborhood} onChange={(e) => set('neighborhood', e.target.value)} /></label>
        </div>
        <div className="form-grid two">
          <label>CEP<input value={form.postal_code} onChange={(e) => set('postal_code', e.target.value)} /></label>
          <label>Endereço completo<input required value={form.address_line} onChange={(e) => set('address_line', e.target.value)} /></label>
        </div>
        <div className="alert alert-info">O endereço completo não será exibido publicamente.</div>

        <h2>Dimensões (opcional)</h2>
        <div className="form-grid three">
          <label>Comprimento (m)<input type="number" step="0.01" value={form.length_m} onChange={(e) => set('length_m', e.target.value)} /></label>
          <label>Largura (m)<input type="number" step="0.01" value={form.width_m} onChange={(e) => set('width_m', e.target.value)} /></label>
          <label>Altura (m)<input type="number" step="0.01" value={form.height_m} onChange={(e) => set('height_m', e.target.value)} /></label>
        </div>

        <h2>Comodidades</h2>
        <div className="checkbox-grid">
          {checkboxes.map(([field, label]) => (
            <label className="check" key={field}><input type="checkbox" checked={form[field]} onChange={(e) => set(field, e.target.checked)} />{label}</label>
          ))}
        </div>

        <h2>Foto de capa</h2>
        <input type="file" accept="image/*" onChange={(e) => {
          const file = e.target.files?.[0]
          setImage(file || null)
          setPreview(file ? URL.createObjectURL(file) : '')
        }} />
        {(preview || initialValues.cover_image) && <img className="image-preview" src={preview || initialValues.cover_image} alt="Pré-visualização" />}

        {error && <div className="alert alert-error">{error}</div>}
        <button disabled={loading} className="button button-primary">{loading ? loadingLabel : submitLabel}</button>
      </form>
  )
}
