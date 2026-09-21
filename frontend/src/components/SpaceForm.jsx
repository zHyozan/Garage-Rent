import { useEffect, useRef, useState } from 'react'
const empty = {
  space_type: 'garage', title: '', description: '', price: '', billing_period: 'month',
  state: 'SP', city: '', neighborhood: '', postal_code: '', address_line: '',
  length_m: '', width_m: '', height_m: '', covered: false, electric_gate: false,
  security_camera: false, access_24h: false, lighting: false, electricity: false, restroom: false,
}

export function buildSpaceFormData(form, gallery, removedIds = []) {
  const payload = new FormData()
  Object.entries(form).forEach(([key, value]) => payload.append(key, value ?? ''))
  let newIndex = 0
  gallery.forEach((item) => {
    if (item.file) {
      payload.append('images_upload', item.file)
      payload.append('gallery_order', `new:${newIndex++}`)
    } else if (item.id != null) {
      payload.append('gallery_order', `old:${item.id}`)
    }
  })
  removedIds.forEach((id) => payload.append('remove_image_ids', id))
  return payload
}

export default function SpaceForm({ initialValues = {}, onSubmit, error, loading, submitLabel, loadingLabel }) {
  const [form, setForm] = useState(() => Object.fromEntries(
    Object.entries(empty).map(([key, value]) => [key, initialValues[key] ?? value])
  ))
  const [gallery, setGallery] = useState(() => initialValues.images || (initialValues.cover_image ? [{ id: null, url: initialValues.cover_image }] : []))
  const [removedIds, setRemovedIds] = useState([])
  const [imageError, setImageError] = useState('')
  const previewUrls = useRef(new Set())
  useEffect(() => () => previewUrls.current.forEach((url) => URL.revokeObjectURL(url)), [])
  const set = (field, value) => setForm((old) => ({ ...old, [field]: value }))
  const submit = (event) => {
    event.preventDefault()
    if (!loading && !imageError) onSubmit(form, gallery, removedIds)
  }
  const addImages = (files) => {
    const selected = Array.from(files || [])
    if (gallery.length + selected.length > 8) return setImageError('O anúncio pode ter no máximo 8 imagens.')
    if (selected.some((file) => file.size > 5 * 1024 * 1024)) return setImageError('Cada imagem deve ter no máximo 5 MB.')
    if (selected.some((file) => !['image/jpeg', 'image/png', 'image/webp'].includes(file.type))) return setImageError('Envie imagens JPEG, PNG ou WebP.')
    setImageError('')
    const additions = selected.map((file) => {
      const url = URL.createObjectURL(file)
      previewUrls.current.add(url)
      return { file, url }
    })
    setGallery((old) => [...old, ...additions])
  }
  const removeImage = (index) => {
    const item = gallery[index]
    if (item.id != null) setRemovedIds((old) => [...old, item.id])
    if (item.file) {
      URL.revokeObjectURL(item.url)
      previewUrls.current.delete(item.url)
    }
    setGallery((old) => old.filter((_, position) => position !== index))
    setImageError('')
  }
  const moveImage = (index, direction) => {
    const next = [...gallery]
    const target = index + direction
    if (target < 0 || target >= next.length) return
    ;[next[index], next[target]] = [next[target], next[index]]
    setGallery(next)
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

        <h2>Fotos do anúncio</h2>
        <p className="muted">Até 8 imagens JPEG, PNG ou WebP, com no máximo 5 MB cada. A primeira será a capa.</p>
        <input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={(e) => { addImages(e.target.files); e.target.value = '' }} />
        {imageError && <div className="alert alert-error">{imageError}</div>}
        <div className="image-preview-grid">
          {gallery.map((image, index) => <div className="image-preview-item" key={image.id ?? image.url}>
            <img className="image-preview" src={image.url} alt={`Foto ${index + 1}`} />
            {index === 0 && <strong>Capa</strong>}
            <div className="image-actions">
              <button type="button" disabled={index === 0} onClick={() => moveImage(index, -1)} aria-label={`Mover foto ${index + 1} para antes`}>←</button>
              <button type="button" disabled={index === gallery.length - 1} onClick={() => moveImage(index, 1)} aria-label={`Mover foto ${index + 1} para depois`}>→</button>
              <button type="button" onClick={() => removeImage(index)} aria-label={`Remover foto ${index + 1}`}>Remover</button>
            </div>
          </div>)}
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        <button disabled={loading} className="button button-primary">{loading ? loadingLabel : submitLabel}</button>
      </form>
  )
}
