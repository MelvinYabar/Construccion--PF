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
