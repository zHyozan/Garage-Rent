# Arquitetura — Garage Rent

## Modelo de classificados

`Space` pertence ao anunciante. O preço é informativo e a negociação ocorre diretamente entre as partes. `availability_status` distingue disponível, em negociação e alugado; `is_active` controla pausa voluntária e `moderated` controla bloqueio administrativo. Apenas o proprietário recebe `exact_address`.

`Inquiry` guarda contatos enviados por usuários autenticados. Somente o proprietário acessa a caixa de entrada do anúncio. Há limite de uma mensagem por remetente/anúncio a cada 24 horas e throttling nos endpoints de interação.

`ListingEvent` guarda visualizações e cliques deduplicados por anúncio, canal, dia e hash do visitante estimado. O hash usa HMAC com data e identidade autenticada ou IP/user-agent, sem armazenar estes dois últimos em texto. Métricas ficam restritas ao proprietário. Cliques não são conversas comprovadas.

`ServiceReview` mede atendimento após contato pelo formulário; não representa uma contratação verificada. `ListingReport` é uma denúncia privada. Os administradores moderam ambos.

`PromotionPackage` configura preço, duração e instruções. `Promotion` registra uma cópia das condições comerciais e começa pendente. Somente a ação administrativa, após salvar a referência de pagamento externo, define ativação, operador e validade. Um índice único impede dois pedidos pendentes por anúncio. A API do anunciante não permite editar preço, estado ou validade. Destaques expirados não recebem prioridade; filtros de relevância são aplicados antes da ordenação patrocinada.

`SavedAlert` registra os critérios e o consentimento do usuário. `send_portal_notifications` entrega resumos de novas ofertas a e-mails verificados, avisa sobre contatos e lembra proprietários de revisar disponibilidade. `NotificationDelivery` registra as entregas; o comando exige execução serial por um único worker. SMTP e agendamento são configurações de implantação.

## Rotas

- `/api/spaces/`: catálogo e gestão dos anúncios; `owner` filtra a vitrine de um anunciante.
- `/api/portal/packages/`: ofertas de destaque.
- `/api/portal/{space_id}/event/`: registrar visualização/clique.
- `/api/portal/{space_id}/inquiries/`: enviar mensagem; GET restrito ao proprietário.
- `/api/portal/{space_id}/metrics/`: métricas privadas de 30 dias.
- `/api/portal/{space_id}/promotions/`: pedidos do proprietário e criação idempotente do pedido pendente.
- `/api/portal/{space_id}/cancel_promotion/`: cancelar pedido pendente.
- `/api/portal/{space_id}/refresh/`: confirmar atualização da disponibilidade.
- `/api/portal/{space_id}/feedback/`: avaliações de atendimento.
- `/api/portal/{space_id}/report/`: denúncia autenticada.
- `/api/alerts/`: CRUD de alertas do próprio usuário.
- `/api/reservations/`: arquivo privado, somente leitura, do modelo anterior.

## Operação

Sem gateway ou repasses de aluguel. Dados históricos foram preservados por migrações aditivas. Em produção, usar PostgreSQL, armazenamento externo de imagens, cache compartilhado para throttling e um agendador de notificações. A deduplicação de e-mails não garante exatamente uma entrega em caso de falha entre SMTP e gravação.
