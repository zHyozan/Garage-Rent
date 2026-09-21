# Garage Rent — Roadmap

## Fase 1 — Fundação (implementada nesta reconstrução)
- Autenticação JWT.
- Marketplace de garagens, vagas e galpões.
- Busca, filtros e ordenação.
- Criação e gestão de anúncios.
- Favoritos.
- Reserva por período com prevenção de conflito.
- Fluxo confirmar/recusar/cancelar.
- Endereço exato protegido.

## Fase 2 — Experiência de marketplace
- Galeria com múltiplas fotos.
- Mapa e busca por raio.
- Calendário visual de disponibilidade.
- Edição completa de anúncio pelo frontend.
- Regras de preço por período, descontos e caução.
- Perfis públicos básicos de locador/locatário.

## Fase 3 — Confiança e transação
- Gateway de pagamento e split de repasse.
- KYC/verificação de identidade.
- Contratos e termos digitais.
- Avaliações bilaterais.
- Chat interno com bloqueio de compartilhamento indevido de dados antes da reserva.
- Notificações por e-mail e push.

## Fase 4 — Escala
- PostgreSQL + PostGIS.
- Redis e jobs assíncronos.
- Armazenamento de mídia em objeto (S3 compatível).
- Observabilidade, auditoria e antifraude.
- Painel operacional/moderação.
- Aplicativo mobile ou PWA.
