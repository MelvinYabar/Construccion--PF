# Parmenia - Plataforma de Pre-incubacion

Aplicacion para la gestion de la incubadora de empresas **Parmenia**. Incluye:

- Backend REST API con FastAPI.
- Frontend en Vue.js.
- Autenticacion tradicional con email/password.
- OAuth2 / OpenID Connect con Google.
- Consumo de todos los endpoints principales del backend desde el frontend.

## Tecnologias

| Componente | Tecnologia |
| --- | --- |
| Backend | FastAPI |
| ORM | SQLAlchemy |
| Base de datos | PostgreSQL |
| Auth local | JWT propio con `python-jose` |
| OAuth2 | Google Identity Services |
| Frontend | Vue 3 + Vite |

## Estructura

```text
app/
  main.py
  auth.py
  database.py
  models.py
  schemas.py
  routers/
frontend/
  src/
  package.json
```

## Configuracion Backend

Copia `.env.example` a `.env`:

```powershell
copy .env.example .env
```

Configura:

```env
DATABASE_URL=postgresql://user:password@host:5432/database
JWT_SECRET=parmenia-dev-secret-change-in-production
GOOGLE_CLIENT_ID=paste-your-google-client-id.apps.googleusercontent.com
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=paste-your-service-role-key
```

`GOOGLE_CLIENT_ID` debe ser el Client ID del OAuth Client creado en Google Cloud.

`SUPABASE_SERVICE_ROLE_KEY` solo debe existir en el backend. Nunca debe ponerse en el frontend ni subirse a GitHub.

## Configuracion Supabase

El proyecto usa Supabase como PostgreSQL y tambien sincroniza los registros con **Authentication > Users**.

Para que los usuarios creados desde la pagina aparezcan correctamente en Supabase Auth y en `public.profiles`, aplica la migracion:

```text
supabase/migrations/001_fix_handle_new_user_profile_sync.sql
```

Esa funcion usa el email real de `auth.users` y crea/actualiza el perfil relacionado.

## Configuracion Frontend

Crea `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_GOOGLE_CLIENT_ID=paste-your-google-client-id.apps.googleusercontent.com
```

`VITE_GOOGLE_CLIENT_ID` debe coincidir con `GOOGLE_CLIENT_ID`.

## Ejecutar Backend

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Ejecutar Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Deploy

### Backend en Render

El backend FastAPI esta preparado para Render con:

```text
render.yaml
```

Variables necesarias en Render:

```env
DATABASE_URL=...
JWT_SECRET=...
GOOGLE_CLIENT_ID=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
```

Comandos usados por Render:

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Frontend en Vercel

El frontend Vue/Vite esta preparado para Vercel con:

```text
vercel.json
```

Variables necesarias en Vercel:

```env
VITE_API_URL=https://tu-backend-en-render.onrender.com
VITE_GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
```

Despues de desplegar, agrega el dominio de Vercel en Google Cloud como origen autorizado para OAuth2.

## OAuth2 con Google

El frontend carga Google Identity Services. Cuando el usuario inicia sesion con Google, el frontend recibe un `credential` de Google y lo envia al backend:

```http
POST /auth/oauth/google
Content-Type: application/json

{
  "credential": "<google_id_token>"
}
```

El backend valida ese token con Google usando `GOOGLE_CLIENT_ID`.

Si el usuario no existe, se crea un perfil local con rol:

```text
emprendedor
```

Ademas, el backend sincroniza el usuario con **Supabase Authentication > Users** usando la Auth Admin API de Supabase. Para eso se usan estas variables:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=paste-your-service-role-key
```

Luego el backend devuelve el JWT local de la API:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {}
}
```

Desde ese momento, el frontend consume todos los endpoints protegidos con:

```http
Authorization: Bearer <access_token>
```

## Integracion Externa: Google Calendar API

El dashboard incluye una integracion con **Google Calendar API** para agendar mentorias.

Flujo:

```text
1. El usuario inicia sesion en la app.
2. En Dashboard completa titulo, fecha, hora e invitados.
3. Presiona "Autorizar y agendar".
4. Google solicita permiso para el scope https://www.googleapis.com/auth/calendar.events.
5. El frontend recibe un access token temporal de Google.
6. El backend usa ese token para crear el evento en Google Calendar.
```

Endpoint:

```http
POST /integrations/google-calendar/mentorships
Authorization: Bearer <jwt_local>
Content-Type: application/json
```

Body:

```json
{
  "google_access_token": "<google_calendar_access_token>",
  "title": "Mentoria Parmenia",
  "description": "Revision de avance del proyecto",
  "start_datetime": "2026-06-26T15:00:00-05:00",
  "end_datetime": "2026-06-26T16:00:00-05:00",
  "attendee_emails": ["mentor@gmail.com"],
  "timezone": "America/Lima",
  "create_meet": true
}
```

Para que funcione en Google Cloud:

- Habilita **Google Calendar API**.
- En el OAuth Client usado por el frontend, agrega el origen autorizado `http://localhost:5173`.
- En OAuth consent screen, permite el scope `https://www.googleapis.com/auth/calendar.events`.

## Permisos por Rol

El backend valida permisos con el rol incluido en el JWT y confirmado contra el perfil de la base de datos.

| Rol | Permisos |
| --- | --- |
| `admin` | Puede crear, listar, actualizar y eliminar recursos. Tambien puede ver reportes, gestionar fases, convocatorias, perfiles, proyectos, mentores, entregables y revisiones. |
| `emprendedor` | Puede ver/editar su propio perfil, inscribirse en convocatorias, crear proyectos, ver sus proyectos, subir/editar sus entregables y consultar publicaciones/fases/convocatorias. No puede crear admins, ver reportes admin, borrar recursos globales ni cambiarse el rol. |
| `mentor` | Puede consultar proyectos asignados, crear publicaciones y revisar entregables de proyectos donde esta asignado. |

Ejemplos para demostrar:

```text
GET /reports/dashboard con admin -> 200 OK
GET /reports/dashboard con emprendedor -> 403 Forbidden
GET /profiles/ con admin -> lista todos
GET /profiles/ con emprendedor -> solo devuelve su propio perfil
PUT /profiles/{id} con role=admin desde emprendedor -> mantiene role=emprendedor
```

## Endpoints Cubiertos por el Frontend

### Autenticacion

| Metodo | Ruta | Descripcion |
| --- | --- | --- |
| POST | `/auth/register` | Registro local |
| POST | `/auth/login` | Login local |
| POST | `/auth/oauth/google` | Login con Google OAuth2 |
| GET | `/auth/me` | Usuario autenticado |

### Perfiles

| Metodo | Ruta |
| --- | --- |
| GET | `/profiles/` |
| GET | `/profiles/{id}` |
| POST | `/profiles/` |
| PUT | `/profiles/{id}` |
| DELETE | `/profiles/{id}` |

### Fases

| Metodo | Ruta |
| --- | --- |
| GET | `/phases/` |
| GET | `/phases/{id}` |
| POST | `/phases/` |
| PUT | `/phases/{id}` |
| DELETE | `/phases/{id}` |

### Convocatorias

| Metodo | Ruta |
| --- | --- |
| GET | `/cohorts/` |
| GET | `/cohorts/{id}` |
| POST | `/cohorts/` |
| PUT | `/cohorts/{id}` |
| DELETE | `/cohorts/{id}` |

### Inscripciones

| Metodo | Ruta |
| --- | --- |
| GET | `/enrollments/` |
| GET | `/enrollments/{id}` |
| POST | `/enrollments/` |
| PUT | `/enrollments/{id}` |
| PUT | `/enrollments/{id}/status` |
| DELETE | `/enrollments/{id}` |

### Proyectos

| Metodo | Ruta |
| --- | --- |
| GET | `/projects/` |
| GET | `/projects/{id}` |
| POST | `/projects/` |
| PUT | `/projects/{id}` |
| DELETE | `/projects/{id}` |
| GET | `/projects/{id}/members` |
| POST | `/projects/{id}/members` |
| DELETE | `/projects/{id}/members/{user_id}` |
| GET | `/projects/{id}/mentors` |
| POST | `/projects/{id}/mentors` |
| DELETE | `/projects/{id}/mentors/{mentor_id}` |

### Publicaciones

| Metodo | Ruta |
| --- | --- |
| GET | `/posts/` |
| GET | `/posts/{id}` |
| POST | `/posts/` |
| PUT | `/posts/{id}` |
| DELETE | `/posts/{id}` |

### Entregables y Revisiones

| Metodo | Ruta |
| --- | --- |
| GET | `/projects/{id}/deliverables` |
| POST | `/projects/{id}/deliverables` |
| GET | `/deliverables/{id}` |
| PUT | `/deliverables/{id}` |
| DELETE | `/deliverables/{id}` |
| GET | `/deliverables/{id}/reviews` |
| POST | `/deliverables/{id}/reviews` |
| GET | `/reviews/{id}` |
| PUT | `/reviews/{id}` |
| DELETE | `/reviews/{id}` |

### Reportes

| Metodo | Ruta |
| --- | --- |
| GET | `/reports/dashboard` |
| GET | `/reports/cohort/{cohort_id}/progress` |

## Usuarios de Prueba

| Email | Password | Rol |
| --- | --- | --- |
| `admin@parmenia.pe` | `admin123` | admin |
| `carlos.mentor@parmenia.pe` | `mentor123` | mentor |
| `ana.mentor@parmenia.pe` | `mentor456` | mentor |
| `luis.emp@parmenia.pe` | `emp123` | emprendedor |
| `maria.emp@parmenia.pe` | `emp456` | emprendedor |
| `pedro.emp@parmenia.pe` | `emp789` | emprendedor |
| `sofia.emp@parmenia.pe` | `emp012` | emprendedor |
