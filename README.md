# Garage Rent

**Garage Rent** é um marketplace especializado exclusivamente no aluguel de **garagens particulares, vagas de estacionamento e galpões**.

A proposta é oferecer uma experiência de locação semelhante a grandes plataformas imobiliárias, mas desenhada para as necessidades específicas desse nicho: descoberta de espaços, filtros, anúncio pelo proprietário, favoritos, reservas, gestão de disponibilidade e evolução futura para pagamentos e avaliações.

## MVP atual

- Cadastro e login por e-mail com JWT. A senha exige no mínimo 8 caracteres, uma letra maiúscula, um número e um símbolo.
- Listagem pública de espaços.
- Busca por título, descrição, cidade e bairro.
- Filtros por tipo de espaço, cidade, estado, período de cobrança e preço.
- Anúncios de garagem, vaga e galpão.
- Upload de imagem de capa.
- Endereço exato protegido; visitantes veem apenas bairro/cidade/UF.
- Área "Meus anúncios".
- Editar e excluir apenas anúncios próprios.
- Favoritar/desfavoritar espaços.
- Solicitar reserva com período definido.
- Bloqueio de reservas sobrepostas pendentes/confirmadas.
- Proprietário pode confirmar ou recusar solicitações.
- Locatário pode cancelar sua reserva.
- Cálculo de valor por hora, diária ou mês (30 dias para estimativa mensal).

## Stack

### Backend
- Python / Django
- Django REST Framework
- Djoser
- SimpleJWT
- django-filter
- django-cors-headers
- SQLite no desenvolvimento

### Frontend
- React
- Vite
- React Router
- Axios

## Estrutura

```text
Garage-Rent/
├── backend/
│   ├── garage_rent/
│   ├── spaces/
│   ├── reservations/
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── .env.example
└── README.md
```

## Executando localmente

### Abrir com um clique no Windows

Com Python e Node.js instalados, dê dois cliques em `Abrir Garage Rent.cmd` na raiz.
O script prepara as dependências, aplica migrações, inicia os servidores em segundo
plano e abre `http://localhost:5173/`. Os logs ficam em `.local/` (fora do Git).
Não feche os servidores se estiver usando os comandos manuais abaixo.

Para testar sem abrir o navegador: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local.ps1 -NoBrowser`.

### Recursos de busca, reserva e confiança

- **Mapa e proximidade:** o anunciante seleciona uma região no mapa ou usa a
  localização do dispositivo. As coordenadas são limitadas a duas casas decimais;
  apenas essa região é armazenada e usada no cálculo de distância em linha reta.
  O mapa mostra as regiões dos resultados da página atual. Anúncios antigos
  precisam receber uma região para aparecer na busca por proximidade; continuam
  disponíveis na busca normal. A localização do visitante só é solicitada ao
  clicar em “Buscar perto de mim”.
- **Anúncios:** veículos aceitos, altura máxima, dimensões e comodidades aparecem
  nos detalhes; a busca permite filtrar veículo, cobertura, acesso 24h e preço.
- **Reserva:** “Consultar total e disponibilidade” calcula no servidor o valor
  por hora, diária ou bloco de 30 dias iniciado. A confirmação revalida o período
  e o total; mudanças de preço exigem nova consulta. As datas enviadas têm fuso.
- **Cancelamento:** o locatário pode cancelar antes do início. Depois, a interface
  orienta combinar alterações com o proprietário. Esta versão não processa
  pagamentos nem reembolsos.
- **Avaliações:** após o fim do período, qualquer participante pode concluir uma
  reserva confirmada. Só o locatário pode publicar uma avaliação de 1 a 5, uma
  por reserva concluída. A nota média e os comentários são públicos.
- **Verificação de e-mail:** usuários conectados podem pedir um link no aviso do
  topo. O link expira em 24 horas; o selo confirma apenas o e-mail, não identidade.
  No desenvolvimento, o link aparece no terminal ou em `.local/backend.log`.
  Para entrega real, configure SMTP em `backend/.env`, como na recuperação de
  senha. Nenhuma credencial deve ser adicionada ao Git.
- **Celular:** menu acessível, filtros expansíveis, troca de fotos por gesto e
  atalho fixo para a seção de reserva.

O mapa usa [Leaflet](https://leafletjs.com/reference.html) e tiles do OpenStreetMap,
com atribuição visível. O mapa base requer internet; em produção, configure um
provedor compatível com o tráfego e com a [política de uso dos tiles](https://operations.osmfoundation.org/policies/tiles/).

### Verificação das alterações

No backend: `.venv\Scripts\python.exe manage.py test`.
No frontend: `npm test` e `npm run build`.

### Paleta de cores

A paleta laranja está em `frontend/src/theme.css`. Para voltar ao verde, altere
`data-theme="orange"` para `data-theme="green"` em `frontend/index.html` e ajuste
a meta `theme-color` para `#173b32`.

### 1. Backend

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\\Scripts\\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie `backend/.env` com base no `.env.example` da raiz e execute:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API: `http://localhost:8000/api/`
Admin: `http://localhost:8000/admin/`

### 2. Frontend

```bash
cd frontend
npm install
```

Crie `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000/api
```

Execute:

```bash
npm run dev
```

Frontend: `http://localhost:5173/`

### Recuperação de senha

No desenvolvimento, o link de recuperação aparece no terminal do backend após o pedido em `/esqueci-senha`. Para entregar o link por e-mail, configure `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` e `FRONTEND_URL` no `backend/.env` (exemplo em `backend/.env.example`). O link expira em 1 hora.

## Endpoints principais

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/api/auth/users/` | Cadastro |
| POST | `/api/auth/jwt/create/` | Login |
| POST | `/api/auth/jwt/refresh/` | Renovação do token |
| GET | `/api/auth/users/me/` | Usuário autenticado |
| GET | `/api/spaces/` | Listar espaços |
| POST | `/api/spaces/` | Criar anúncio |
| GET | `/api/spaces/{id}/` | Detalhe |
| PATCH | `/api/spaces/{id}/` | Editar anúncio próprio |
| DELETE | `/api/spaces/{id}/` | Excluir anúncio próprio |
| GET | `/api/spaces/mine/` | Meus anúncios |
| GET | `/api/spaces/favorites/` | Meus favoritos |
| POST/DELETE | `/api/spaces/{id}/favorite/` | Favoritar/desfavoritar |
| GET/POST | `/api/reservations/` | Minhas reservas / solicitar reserva |
| POST | `/api/reservations/{id}/confirm/` | Confirmar (proprietário) |
| POST | `/api/reservations/{id}/reject/` | Recusar (proprietário) |
| POST | `/api/reservations/{id}/cancel/` | Cancelar (locatário) |

## Próximas evoluções planejadas

1. Geolocalização e mapa.
2. Calendário visual de disponibilidade.
3. Galeria com múltiplas imagens.
4. Pagamentos e repasse ao proprietário.
5. Avaliações de locador e locatário.
6. Chat seguro dentro da plataforma.
7. Verificação de identidade e antifraude.
8. Contrato digital e regras específicas para locações mensais.
9. Notificações por e-mail/push.
10. Painel administrativo de moderação e suporte.

## Regra de privacidade importante

O endereço completo do espaço é armazenado no backend, mas não é exibido publicamente. Ele fica disponível ao proprietário e ao locatário quando houver uma reserva confirmada.
