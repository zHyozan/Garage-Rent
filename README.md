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
