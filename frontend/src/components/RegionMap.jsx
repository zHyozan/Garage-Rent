import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
const emptySpaces = []

export default function RegionMap({ spaces = emptySpaces, position, onSelect }) {
  const element = useRef(null)
  const map = useRef(null)
  const layer = useRef(null)
  const select = useRef(onSelect)
  select.current = onSelect

  useEffect(() => {
    const instance = L.map(element.current, { scrollWheelZoom: false }).setView([-14.2, -51.9], 4)
    map.current = instance
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(instance)
    layer.current = L.layerGroup().addTo(instance)
    instance.on('click', (event) => select.current?.({ latitude: event.latlng.lat.toFixed(2), longitude: event.latlng.lng.toFixed(2) }))
    return () => { instance.remove(); map.current = null }
  }, [])

  useEffect(() => {
    layer.current.clearLayers()
    const points = []
    spaces.filter((space) => space.latitude != null && space.longitude != null).forEach((space) => {
      const point = [Number(space.latitude), Number(space.longitude)]
      points.push(point)
      const link = document.createElement('a')
      link.href = `/espacos/${space.id}`
      link.textContent = `${space.title} — região aproximada`
      L.circle(point, { radius: 1000, color: '#b45309' }).bindPopup(link).addTo(layer.current)
    })
    if (position?.latitude !== '' && position?.latitude != null && position?.longitude !== '' && position?.longitude != null) {
      const point = [Number(position.latitude), Number(position.longitude)]
      points.push(point)
      L.circle(point, { radius: 1000, color: '#b45309' }).addTo(layer.current)
    }
    if (points.length) map.current.fitBounds(L.latLngBounds(points).pad(0.2), { maxZoom: 12 })
  }, [spaces, position])

  return <div className="region-map" ref={element} role="region" aria-label={onSelect ? 'Mapa: selecione uma região aproximada' : 'Mapa das regiões aproximadas dos anúncios'} />
}
