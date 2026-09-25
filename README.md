# Garage Rent

Portal de anúncios de garagens, vagas e galpões. A publicação é gratuita; interessados negociam, contratam e pagam diretamente ao anunciante. O site não cobra comissão nem recebe pagamentos de aluguel.

## Funcionalidades

- Busca por região, tipo, preço e características, mapa aproximado, galeria, favoritos e vitrine de anúncios do mesmo proprietário.
- Contato por WhatsApp, telefone público opcional e formulário para usuários autenticados. O anunciante recebe a mensagem no painel e responde pelo e-mail/telefone informado.
- Disponibilidade: disponível, em negociação e alugado. Alugados saem da busca; anúncios pausados ou ocultos pela moderação não são públicos.
- Painel de resultados dos últimos 30 dias: visualizações, cliques no WhatsApp, cliques no telefone e mensagens. Cliques não significam conversas ou locações. Eventos são deduplicados por visitante estimado, canal, anúncio e dia; visitas do proprietário são ignoradas. Identificadores são hashes diários; não são pessoas únicas comprovadas.
- Destaque opcional inicial de **R$ 29,90 por 7 dias**, cobrança externa e confirmação manual. Publicação gratuita sem limite comercial de anúncios nesta fase.
- Alertas por cidade/bairro, tipo, período e faixa de preço, com consentimento explícito e pausa/exclusão. Entrega de ofertas exige e-mail verificado.
- Avaliações de **atendimento**, uma por usuário/anúncio, após mensagem pelo formulário. Não comprovam locação. Avaliações antigas de reservas não entram nessa nota.
- Denúncias privadas e moderação administrativa; bloqueio de duplicatas ativas do mesmo proprietário com mesmo título, cidade e endereço. Vagas diferentes no mesmo endereço devem ter títulos distintos. Outros casos podem ser denunciados.
- Endereço exato disponível somente ao proprietário, que decide quando compartilhá-lo na negociação. E-mail verificado não equivale a identidade verificada.

## Executar localmente

No Windows, abra `Abrir Garage Rent.cmd`. O iniciador instala dependências, aplica migrações e abre `http://localhost:5173/`. Logs ficam em `.local/`.

Manualmente:

```powershell
cd backend
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe manage.py migrate
.venv/Scripts/python.exe manage.py runserver
```

Em outro terminal:

```powershell
cd frontend
npm install
npm run dev
```

Backend: Django/DRF, JWT e SQLite local. Frontend: React/Vite. Configure variáveis seguindo `.env.example` e `backend/.env.example`. Não publique credenciais.

## Operar o destaque pago

1. Crie uma conta administrativa com `manage.py createsuperuser` e abra `http://localhost:8000/admin/`.
2. Em **Promotion packages**, revise o pacote inicial e preencha instruções reais de cobrança externa (contato comercial ou meio de pagamento escolhido). A configuração inicial apenas orienta aguardar instruções; não contém uma chave Pix ou conta fictícia.
3. O anunciante acessa **Meus anúncios → Resultados e destaque → Solicitar destaque**. O pedido registra preço, duração e instruções daquele momento. Não há checkout nem renovação automática.
4. Em **Promotions**, informe/atualize as instruções específicas do pedido, se necessário. O anunciante as acompanha no painel. Confira o pagamento externamente e salve sua referência em `payment_reference`.
5. Selecione o pedido e use **Confirmar pagamento externo e ativar destaque**. A ação requer referência de pagamento, anúncio ativo, não alugado e não oculto. O prazo começa na ativação; repetir a ação não reinicia o prazo.
6. Apenas destaques vigentes recebem selo **Patrocinado** e prioridade, depois de aplicar os filtros da busca. Entre os patrocinados, vale a ordenação escolhida. A expiração é verificada na consulta, sem depender de uma tarefa agendada.

Anúncios com histórico de destaque devem ser pausados, não excluídos pelo anunciante, para preservar o registro comercial. O anunciante pode cancelar pedidos pendentes. Cancelar/ocultar anúncios ou destaques não faz reembolso. Resolva qualquer pagamento já recebido diretamente com o cliente. Pausar, alugar ou moderar um anúncio interrompe sua exibição, mas não suspende o prazo contratado.

Planos profissionais, pacotes por quantidade e cobrança recorrente ficam para uma próxima fase; não são oferecidos nesta versão.

## E-mails e lembretes

O painel funciona independentemente do e-mail. Para entrega real, configure SMTP (`EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`) e `FRONTEND_URL`.

O comando abaixo simula envios e não transmite mensagens:

```powershell
cd backend
.venv/Scripts/python.exe manage.py send_portal_notifications
```

Após configurar SMTP, execute com `--send` por um único agendador, por exemplo a cada 15 minutos. Esta mudança não instala um agendador de produção nem dispara e-mails reais.

- Novos contatos: aviso ao proprietário e link para o painel; mensagens privadas não entram no corpo do aviso.
- Alertas: resumo de até 20 novos anúncios por execução, respeitando os critérios, o consentimento, a verificação de e-mail e o estado ativo do alerta. O e-mail contém link para pausar/excluir o alerta.
- Disponibilidade: lembrete semanal para anúncios sem revisão há mais de 30 dias; também aparece um aviso no painel.
- Entregas registradas evitam reenvio normal. Use apenas um worker. Como SMTP não é transacional, uma falha depois da transmissão e antes do registro pode gerar repetição no próximo envio; não há garantia de entrega exatamente uma vez.

## Moderação e privacidade

Em **Listing reports**, analise denúncias e use a ação de ocultar anúncios quando necessário. O proprietário não pode remover o bloqueio da moderação. Em **Service reviews**, o administrador pode ocultar avaliações inadequadas. Nunca trate verificação de e-mail como garantia de identidade ou segurança.

Telefone do anúncio é público por escolha do anunciante. E-mail e telefone fornecidos pelo interessado são visíveis somente na área do dono do anúncio (e à administração). Não use esses dados para campanhas não solicitadas.

As reservas antigas permanecem no banco e na API autenticada `/api/reservations/`, apenas para leitura dos participantes. Novas reservas e ações de contratação foram desativadas. A rota antiga `/reservas` redireciona para Meus anúncios.

## Verificar

```powershell
cd backend
.venv/Scripts/python.exe manage.py test
.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

```powershell
cd frontend
npm test
npm run build
```

Testes cobrem privacidade, permissões, duplicatas, contato, métricas, consentimento, entrega de notificações, ativação administrativa, expiração e ranking dos destaques. Não é necessário processar um pagamento real para testar.

O mapa usa Leaflet e tiles OpenStreetMap. Em produção, configure um provedor adequado ao tráfego. A região armazenada permanece aproximada (duas casas decimais).
