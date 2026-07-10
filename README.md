# Parmenia — Plataforma de Pre-incubación de Empresas

Aplicación full-stack para la gestión de la incubadora de empresas **Parmenia** de la Universidad La Salle. Permite a estudiantes emprender proyectos, recibir mentoría y avanzar por fases estructuradas de pre-incubación e incubación.

## Tabla de contenidos

1. [Tema y objetivo](#tema-y-objetivo)
2. [Arquitectura](#arquitectura)
3. [Proveedor OAuth elegido y por qué](#proveedor-oauth-elegido-y-por-qué)
4. [Justificación de las dos bases de datos](#justificación-de-las-dos-bases-de-datos)
5. [Tecnologías](#tecnologías)
6. [Estructura del proyecto](#estructura-del-proyecto)
7. [Configuración del proveedor OAuth (Google)](#configuración-del-proveedor-oauth-google)
8. [Cómo correr todo localmente](#cómo-correr-todo-localmente)
9. [Colección Postman](#colección-postman)
10. [Deploy](#deploy)
11. [Permisos por rol](#permisos-por-rol)
12. [Usuarios de prueba](#usuarios-de-prueba)
13. [Endpoints cubiertos](#endpoints-cubiertos)

---

## Tema y objetivo

**Tema:** Plataforma de pre-incubación de empresas para la Universidad La Salle.

**Objetivo:** Permitir a estudiantes emprendedores inscribirse en convocatorias, formar proyectos, recibir mentoría de mentores asignados, subir entregables por fase y obtener revisiones que hagan avanzar el proyecto por las distintas fases de la incubación. Incluye un panel de administración para gestionar todo el ciclo, un panel de mentor para revisar entregables y agendar mentorías en Google Calendar, y un panel de emprendedor con dashboard de progreso.

Roles implementados: **admin**, **mentor**, **emprendedor**.

---

## Arquitectura

![Arquitectura Parmenia](architecture.png)

### Componentes

| Componente | Tecnología | Dónde corre |
|---|---|---|
| **Frontend** | Vue 3 + Vite + TailwindCSS (SPA) | Vercel |
| **Backend** | FastAPI (Python) | Render |
| **BD relacional** | PostgreSQL (Supabase) | Supabase Cloud |
| **BD NoSQL** | MongoDB (Atlas) | MongoDB Atlas Cloud |
| **Proveedor OAuth** | Google Identity (OAuth 2.0 Authorization Code) | Google Cloud |
| **Integración externa** | Google Calendar API (mentorías) | Google Cloud |
| **Almacenamiento de archivos** | Supabase Storage | Supabase Cloud |

### Flujo OAuth 2.0 Authorization Code end-to-end

El flujo completo de autenticación delega el Authorization Server a Google (proveedor de terceros). La aplicación nunca ve las credenciales del usuario, solo recibe un código de autorización que intercambia por tokens.

```
┌────────────┐
│  Usuario   │
└─────┬──────┘
      │ 1. click "Continuar con Google"
      ▼
┌──────────────────────────┐
│  Frontend (Vue, Vercel)  │
└─────┬────────────────────┘
      │ 2. window.location = /auth/oauth/google/login
      ▼
┌──────────────────────────────────────────┐
│  Backend (FastAPI, Render)               │
│  GET /auth/oauth/google/login            │
│  · genera state JWT firmado              │
│  · 302 redirect a Google                 │
└─────┬────────────────────────────────────┘
      │ 3. redirect 302
      ▼
┌──────────────────────────────────────────┐
│  Google (Authorization Server)           │
│  https://accounts.google.com/o/oauth2/v2/auth
│  · muestra pantalla de login             │
│  · usuario elige cuenta + consentimiento │
└─────┬────────────────────────────────────┘
      │ 4. redirect 302 callback?code=...&state=...
      ▼
┌──────────────────────────────────────────┐
│  Backend (FastAPI, Render)               │
│  GET /auth/oauth/google/callback         │
│  · verifica state (CSRF protection)      │
│  · POST /token con code + CLIENT_SECRET  │ ← server-to-server
│  · recibe {access_token, id_token}       │
│  · valida id_token con JWKS de Google    │
│  · extrae sub, email, name               │
│  · upsert Profile.guardar google_sub     │
│  · emite JWT local (HS256)               │
│  · log_action() → MongoDB audit_logs     │
└─────┬────────────────────────────────────┘
      │ 5. redirect 302 frontend/?token=<jwt_local>
      ▼
┌──────────────────────────┐
│  Frontend (Vue, Vercel)  │
│  · procesa ?token=       │
│  · llama /auth/me        │
│  · limpia URL            │
│  · guarda sesión         │
└──────────────────────────┘
```

A partir de ahí, todas las peticiones del frontend al backend incluyen `Authorization: Bearer <jwt_local>`. El backend valida ese JWT localmente (HS256 con `JWT_SECRET`) y, según el rol del usuario, permite o deniega el acceso al recurso.

---

## Proveedor OAuth elegido y por qué

**Proveedor elegido:** Google Identity (OAuth 2.0 / OpenID Connect).

### Por qué Google y no Auth0 / Keycloak / Supabase Auth

| Criterio | Google | Auth0 | Keycloak | Supabase Auth |
|---|---|---|---|---|
| Costo | Gratis | 7,500 MAU free | Gratis (self-host) | 50,000 MAU free |
| Setup | Muy simple (Cloud Console) | Simple | Complejo (Docker) | Simple |
| Infra adicional | Ninguna | Ninguna | Docker | Ya lo usamos para PG |
| Documentación | Excelente | Excelente | Regular | Buena |
| Estándares | OAuth 2.0 + OIDC | OAuth 2.0 + OIDC | OAuth 2.0 + OIDC + SAML | OAuth 2.0 + OIDC |
| Usuarios con cuenta Google | Billones | — | — | — |

**Decisión:** Google porque (1) los estudiantes universitarios ya tienen cuenta Google institucional (@ulasalle.edu.pe), (2) no requiere infraestructura adicional, (3) permite demostrar el flujo Authorization Code contra un proveedor real estándar de la industria, (4) gratuito sin límites prácticos para una demo académica.

### Comparación con un Authorization Server custom

En un laboratorio anterior se construyó un Authorization Server propio (con endpoints `/authorize`, `/token`, `/introspect` hechos a mano). La diferencia con delegar a Google:

| Aspecto | Auth Server custom | Google |
|---|---|---|
| Líneas de código del AS | ~500 | 0 (lo provee Google) |
| Manejo de credenciales | Implementar hash + storage | Google las maneja |
| Rotación de claves JWKS | Implementar endpoint | Google rota automáticamente |
| Consentimiento UI | Implementar pantalla | Google la provee |
| CSRF protection con state | Implementar | Implementar (lo hicimos) |
| Validación de tokens | Implementar introspection/JWKS | Usar JWKS de Google |

**Conclusión build vs buy:** Para identidad, casi siempre conviene **buy** (delegar a un proveedor). El esfuerzo de construir un AS seguro y mantenerlo es enorme y no aporta valor al negocio. La aplicación se concentra en su dominio (incubación) y deja la identidad en manos de expertos. Solo se justifica build cuando se necesita control total (ej. entorno corporativo aislado, regulación específica).

---

## Justificación de las dos bases de datos

La rúbrica exige usar efectivamente una BD relacional y una NoSQL, justificando qué datos van a cada una.

### PostgreSQL (relacional, vía Supabase) — datos estructurados del dominio

**Por qué PostgreSQL:** Los datos del dominio tienen relaciones fuertes y necesitan transacciones ACID, foreign keys, constraints y JOINs. Una BD relacional es la opción natural para modelar un dominio con entidades como proyectos, miembros, fases, entregables y revisiones.

**Tablas en PostgreSQL:**

| Tabla | Uso |
|---|---|
| `profiles` | Usuarios (con `google_sub` para identidad OAuth) |
| `phases` | Fases del proceso de incubación |
| `cohorts` | Convocatorias |
| `enrollments` | Inscripciones a convocatorias |
| `projects` | Proyectos emprendedores |
| `project_members` | Miembros de cada proyecto (N:M) |
| `project_mentors` | Mentores asignados a proyectos (N:M) |
| `posts` | Noticias/publicaciones |
| `deliverables` | Entregables subidos por los emprendedores |
| `deliverable_reviews` | Revisiones de mentor a entregables |
| `deliverable_comments` | Comentarios en entregables |
| `notifications` | Notificaciones in-app |
| `mentorships` | Mentorías agendadas en Google Calendar |

### MongoDB (NoSQL, vía Atlas) — audit logs

**Por qué MongoDB:** Los audit logs son registros append-only donde cada acción puede tener un campo `details` con **estructura variable** (campos distintos según el tipo de acción). Por ejemplo, un log de `auth.login.oauth` tiene `{provider, google_sub, role}`, mientras que un log de `mentorship.schedule` tiene `{title, project_id, google_event_id, google_meet_link, start_datetime}`. Encajar esto en tablas relacionales requería columnas nullable o JSON columns. En MongoDB, cada documento es naturalmente flexible.

**Colección en MongoDB:**

| Colección | Uso |
|---|---|
| `audit_logs` | Registros de acciones sensibles: login local, login OAuth, crear proyecto, subir entregable, crear revisión, agendar mentoría, cambio de fase por admin, etc. |

**Esquema de un documento `audit_logs`:**

```json
{
  "_id": ObjectId("..."),
  "user_id": "uuid-string",
  "user_email": "user@example.com",
  "action": "auth.login.oauth_authorization_code",
  "resource": "session",
  "resource_id": null,
  "details": {
    "provider": "google",
    "google_sub": "10769150350006150715",
    "role": "emprendedor",
    "flow": "authorization_code"
  },
  "ip": null,
  "created_at": ISODate("2026-07-10T12:00:00Z")
}
```

**Índices creados** (en `app/mongo.py`):
- `(user_id, created_at desc)` — consulta "mis logs"
- `(action, created_at desc)` — filtrar por tipo de acción
- `(resource, resource_id)` — auditar un recurso específico

### Modo degradado

Si `MONGODB_URI` no está configurado, la app sigue funcionando: `log_action()` retorna `False` silenciosamente y los endpoints `/audit/*` indican "no configurado". Esto permite desarrollo sin MongoDB, pero para la rúbrica debe estar configurado.

---

## Tecnologías

| Componente | Tecnología |
|---|---|
| Backend | FastAPI (Python 3.13) |
| ORM | SQLAlchemy 2.0 |
| BD relacional | PostgreSQL (Supabase) |
| BD NoSQL | MongoDB (Atlas) con PyMongo |
| JWT local | python-jose (HS256) |
| OAuth2/OIDC | Google Identity (Authorization Code flow) |
| Validación ID token | google-auth + JWKS de Google |
| Frontend | Vue 3 + Vite + TailwindCSS |
| Almacenamiento archivos | Supabase Storage |
| Integración externa | Google Calendar API |

---

## Estructura del proyecto

```
Construccion--PF-main/
├── app/
│   ├── main.py                 # FastAPI app + registro de routers
│   ├── auth.py                 # JWT local (create + verify), get_current_user
│   ├── database.py             # SQLAlchemy engine (PostgreSQL)
│   ├── mongo.py                # Conexión MongoDB + helpers log_action/query_audit_logs
│   ├── models.py               # SQLAlchemy ORM (Profile, Project, Mentorship, etc.)
│   ├── schemas.py              # Pydantic schemas
│   ├── supabase_auth.py        # Sincroniza usuarios con Supabase Auth
│   └── routers/
│       ├── auth.py             # /auth/login, /auth/oauth/google/login, /callback, /verify
│       ├── profiles.py
│       ├── phases.py
│       ├── cohorts.py
│       ├── enrollments.py
│       ├── projects.py
│       ├── deliverables.py
│       ├── posts.py
│       ├── notifications.py
│       ├── comments.py
│       ├── integrations.py     # Google Calendar mentorships
│       ├── audit.py            # /audit/status, /audit/logs, /audit/me, /audit/test
│       ├── reports.py          # /reports/dashboard (admin)
│       └── upload.py           # Subida de archivos a Supabase Storage
├── frontend/
│   ├── src/
│   │   ├── App.vue             # App principal (login + dashboard inline)
│   │   ├── api.js              # Cliente HTTP + helpers OAuth
│   │   ├── views/              # Vistas (LoginView, DashboardView, etc.)
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.js
├── supabase/migrations/
│   ├── 001_fix_handle_new_user_profile_sync.sql
│   ├── mentorships_nullable_project.sql
│   └── profiles_google_sub.sql
├── seed.sql                    # Datos de prueba (7 usuarios, 4 fases, 3 cohortes, 2 proyectos)
├── postman_collection.json     # Colección Postman con todos los endpoints
├── architecture.mmd            # Diagrama Mermaid (fuente)
├── architecture.png            # Diagrama de arquitectura (PNG)
├── requirements.txt
├── render.yaml                 # Config deploy backend en Render
├── vercel.json                 # Config deploy frontend en Vercel
├── .env.example                # Todas las vars con placeholders
└── README.md
```

---

## Configuración del proveedor OAuth (Google)

### Paso a paso

1. **Crear proyecto en Google Cloud Console**
   - Ve a https://console.cloud.google.com/
   - Crea un proyecto nuevo (ej: `parmenia-oauth`)

2. **Configurar OAuth consent screen**
   - Menú → APIs & Services → OAuth consent screen
   - User type: External
   - App name: Parmenia
   - Support email: tu correo
   - Scopes: `openid`, `email`, `profile`
   - Test users: agrega los correos con los que vas a probar (mientras la app esté en modo "testing")

3. **Crear OAuth Client ID**
   - Menú → APIs & Services → Credentials → Create Credentials → OAuth client ID
   - Application type: Web application
   - Authorized JavaScript origins:
     ```
     http://localhost:5173
     https://tu-frontend.vercel.app
     ```
   - Authorized redirect URIs (¡importante!):
     ```
     http://localhost:8000/auth/oauth/google/callback
     https://parmenia-api-r0oi.onrender.com/auth/oauth/google/callback
     ```
   - Click Create → **anota `Client ID` y `Client Secret`**

4. **Habilitar Google Calendar API (opcional, para mentorías)**
   - Menú → APIs & Services → Library → busca "Google Calendar API" → Enable

5. **Configurar variables en el backend**
   - Copia `.env.example` a `.env` y completa con tus valores:
   ```env
   GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=tu-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/oauth/google/callback
   SCOPE=openid email profile
   FRONTEND_URL=http://localhost:5173
   COOKIE_SECURE=false
   ```

### Notas importantes

- `GOOGLE_REDIRECT_URI` debe coincidir **exactamente** con una de las URIs registradas en Google Cloud Console.
- En producción (HTTPS), cambia `COOKIE_SECURE=true`.
- El `GOOGLE_CLIENT_SECRET` **nunca** debe ir en el frontend ni en GitHub. Solo en el `.env` del backend.
- El `state` se implementa como JWT firmado con `JWT_SECRET` (no requiere cookies, robusto contra bloqueos cross-site).

---

## Cómo correr todo localmente

### Prerequisitos

- Python 3.13+
- Node.js 18+
- Cuenta Supabase + cadena de conexión PostgreSQL
- Cuenta MongoDB Atlas + cadena de conexión
- OAuth Client ID de Google (ver sección anterior)

### 1. Clonar el repo

```bash
git clone <repo-url>
cd Construccion--PF-main
```

### 2. Configurar backend

```powershell
# Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\activate          # Windows
# source .venv/bin/activate       # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables
copy .env.example .env
# Edita .env con tus valores reales
```

`.env` debe quedar así:

```env
# BD relacional
DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres

# BD NoSQL
MONGODB_URI=mongodb+srv://user:password@cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=parmenia

# JWT
JWT_SECRET=tu-secreto-largo-y-aleatorio

# OAuth Google
GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/oauth/google/callback
SCOPE=openid email profile
FRONTEND_URL=http://localhost:5173
COOKIE_SECURE=false

# Supabase Auth Admin API
SUPABASE_URL=https://tu-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key
```

### 3. Aplicar migraciones en Supabase

Entra a Supabase → SQL Editor y ejecuta los 3 archivos en orden:

1. `supabase/migrations/001_fix_handle_new_user_profile_sync.sql`
2. `supabase/migrations/mentorships_nullable_project.sql`
3. `supabase/migrations/profiles_google_sub.sql`

### 4. (Opcional) Cargar datos de prueba

En Supabase SQL Editor, ejecuta `seed.sql` para tener usuarios de prueba.

### 5. Iniciar backend

```powershell
uvicorn app.main:app --reload --port 8000
```

Backend en `http://localhost:8000`. Swagger en `http://localhost:8000/docs`.

### 6. Configurar frontend

```powershell
cd frontend
npm install

# Crear .env
# frontend/.env
# VITE_API_URL=http://localhost:8000
# VITE_GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
```

### 7. Iniciar frontend

```powershell
npm run dev
```

Frontend en `http://localhost:5173`.

### 8. Probar

1. Abre `http://localhost:5173`
2. Login con `admin@parmenia.pe` / `admin123` (local) **o** click "Continuar con Google"
3. Explora las vistas según el rol

---

## Colección Postman

La colección está en `postman_collection.json` en la raíz del repo. Incluye:

- **16 carpetas** con todos los endpoints organizados por recurso
- **Endpoints públicos** (health checks, login, registro)
- **Endpoints protegidos** con `Authorization: Bearer {{token}}`
- **Variables de entorno** auto-pobladas por tests scripts (`token`, `user_id`, `project_id`, etc.)
- **3 tokens de ejemplo** preconfigurados: `admin_token`, `mentor_token`, `token` (emprendedor)
- **Cuerpos de request** listos para probar (POST/PUT)

### Cómo usarla

1. Abre Postman → Import → selecciona `postman_collection.json`
2. Crea un Environment con las variables:
   ```
   base_url: http://localhost:8000
   token: (vacío — se autocompleta al hacer login)
   admin_token: (vacío)
   mentor_token: (vacío)
   ```
3. Ejecuta el request **"Login as admin"** (carpeta Auth) → auto-puebla `admin_token` y `token`
4. Ejecuta otros requests — el header `Authorization` se setea automáticamente con `{{token}}`

### Carpetas incluidas

| Carpeta | Endpoints |
|---|---|
| Health | `/health`, `/health/db` |
| Auth — Login local | register, login (admin/mentor/emprendedor), /auth/me |
| Auth — OAuth Authorization Code | /login URL, /callback, /verify |
| Profiles | list, get, update |
| Phases | list, create |
| Cohorts | list, create |
| Enrollments | list, create, update status |
| Projects | list, my-stats, create, get, public-detail, update, change phase, members, mentors |
| Posts (Noticias) | list, create |
| Deliverables & Reviews | list, upload, get, create review, list reviews |
| Comments | list, create |
| Notifications | list, unread-count, mark-all-read |
| Mentorships (Google Calendar) | list, schedule |
| Audit Logs (MongoDB) | status, list, my logs, test log |
| Reports (admin) | dashboard, cohort progress |
| Upload file | Supabase Storage upload |

---

## Deploy

### Backend en Render

El repo incluye `render.yaml` con la configuración del web service.

1. Sube el repo a GitHub
2. En Render → New → Web Service → conecta tu repo
3. Render detecta `render.yaml` automáticamente. Si no, configura manualmente:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Variables de entorno en Render (Settings → Environment):
   ```
   DATABASE_URL=postgresql://...@db.xxxxx.supabase.co:5432/postgres
   MONGODB_URI=mongodb+srv://...
   MONGODB_DB=parmenia
   JWT_SECRET=tu-secreto
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   GOOGLE_REDIRECT_URI=https://parmenia-api-r0oi.onrender.com/auth/oauth/google/callback
   SCOPE=openid email profile
   FRONTEND_URL=https://tu-frontend.vercel.app
   COOKIE_SECURE=true
   SUPABASE_URL=https://tu-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=...
   CORS_ORIGINS=https://tu-frontend.vercel.app
   ```
5. Backend URL: `https://parmenia-api-r0oi.onrender.com` (o la que te asigne Render)

### Frontend en Vercel

Ver sección detallada abajo: [Deploy del frontend a Vercel paso a paso](#deploy-del-frontend-a-vercel-paso-a-paso).

### URLs autorizadas en Google Cloud Console

Después de hacer deploy, agrega en Google Cloud Console → Credentials → tu OAuth Client:

- **Authorized JavaScript origins:**
  ```
  http://localhost:5173
  https://tu-frontend.vercel.app
  ```
- **Authorized redirect URIs:**
  ```
  http://localhost:8000/auth/oauth/google/callback
  https://parmenia-api-r0oi.onrender.com/auth/oauth/google/callback
  ```

---

## Deploy del frontend a Vercel paso a paso

### Requisitos previos

- El repo subido a GitHub
- El backend ya deployado en Render (`https://parmenia-api-r0oi.onrender.com`)
- Tu OAuth Client ID de Google

### Paso 1 — Subir el repo a GitHub

Si aún no lo has hecho:

```bash
cd Construccion--PF-main
git init
git add .
git commit -m "Initial commit: Parmenia full-stack con OAuth + MongoDB"
git branch -M main
git remote add origin https://github.com/tu-usuario/parmenia.git
git push -u origin main
```

### Paso 2 — Conectar Vercel con GitHub

1. Ve a https://vercel.com/ y crea una cuenta (puedes usar GitHub login)
2. Click **"Add New..."** → **"Project"**
3. En "Import Git Repository", busca tu repo `parmenia` y click **"Import"**

### Paso 3 — Configurar el proyecto

Vercel detecta automáticamente Vite. Verifica los campos:

| Campo | Valor |
|---|---|
| Framework Preset | Vite |
| Root Directory | `frontend` (¡importante!) |
| Build Command | `npm run build` (se autodetecta) |
| Output Directory | `dist` (se autodetecta) |
| Install Command | `npm install` (se autodetecta) |

**Si Vercel no te deja setear Root Directory desde la UI**, asegúrate de que tu `vercel.json` (en la raíz del repo) tenga esta configuración — ya está en el repo:

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "installCommand": "cd frontend && npm install",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

Los `rewrites` son importantes: como es una SPA, cualquier ruta debe servir `index.html` para que Vue Router maneje la navegación client-side.

### Paso 4 — Configurar variables de entorno

Antes de click "Deploy", despliega **"Environment Variables"** y agrega:

| Name | Value |
|---|---|
| `VITE_API_URL` | `https://parmenia-api-r0oi.onrender.com` |
| `VITE_GOOGLE_CLIENT_ID` | `tu-client-id.apps.googleusercontent.com` |

⚠️ **Sin la barra `/` al final** de `VITE_API_URL`. Si lo dejas con `/`, las URLs quedan `https://..render.com//auth/login` (doble barra) y fallan.

### Paso 5 — Deploy

Click **"Deploy"**. Vercel tarda 1-2 minutos. Cuando termine, te da una URL como:

```
https://parmenia-xxxxx.vercel.app
```

### Paso 6 — Actualizar Google Cloud Console con la URL de Vercel

**Crítico:** Sin esto, el login con Google falla en producción.

1. Ve a Google Cloud Console → APIs & Services → Credentials → tu OAuth Client
2. En **Authorized JavaScript origins** agrega:
   ```
   https://parmenia-xxxxx.vercel.app
   ```
3. En **Authorized redirect URIs** — ya está el del backend, no agregues nada nuevo
4. Click Save

### Paso 7 — Actualizar backend en Render con la URL de Vercel

En Render → tu web service → Environment → actualiza:

```
FRONTEND_URL=https://parmenia-xxxxx.vercel.app
CORS_ORIGINS=https://parmenia-xxxxx.vercel.app
```

Esto hace que el callback OAuth redirija al frontend correcto después del login, y que el backend acepte peticiones CORS desde Vercel.

### Paso 8 — Probar el flujo completo en producción

1. Abre `https://parmenia-xxxxx.vercel.app`
2. Click **"Continuar con Google"**
3. Te redirige a Google → eliges cuenta → regresa al frontend logueado
4. Si todo funciona, ya está deployado

### Troubleshooting de Vercel

| Error | Causa probable | Solución |
|---|---|---|
| `404 Not Found` al abrir la URL | Root Directory mal seteado | En Vercel → Settings → Root Directory → `frontend` |
| `Cannot GET /auth/oauth/google/login` | `VITE_API_URL` mal configurado o sin setear | Revisa variables de entorno en Vercel |
| `redirect_uri_mismatch` de Google | Falta agregar la URL de Vercel a Authorized JavaScript origins | Paso 6 |
| `CORS error` en el browser | `CORS_ORIGINS` en Render no incluye la URL de Vercel | Paso 7 |
| Rutas como `/dashboard` dan 404 al recargar | Faltan los `rewrites` en `vercel.json` | Ya están en el repo, verifica que se subieron |
| `Build failed: vite: command not found` | `npm install` no se ejecutó antes del build | El `vercel.json` ya maneja esto, no lo modifiques |

### Redeploys

Cada vez que hagas `git push` a `main`, Vercel hace un deploy automático. Para forzar un redeploy sin cambiar código: Vercel → tu proyecto → Deployments → click en los 3 puntos del último deploy → "Redeploy".

---

## Permisos por rol

El backend valida permisos con el rol incluido en el JWT y confirmado contra el perfil en la base de datos.

| Rol | Permisos |
|---|---|
| `admin` | Acceso total: crear/editar/eliminar cualquier recurso, ver reportes, gestionar fases/convocatorias, asignar mentores, cambiar fase de proyectos, ver todos los audit logs |
| `mentor` | Ver proyectos asignados, crear publicaciones, revisar entregables de sus proyectos (aprobar/rechazar), agendar mentorías en Google Calendar, ver sus propios audit logs |
| `emprendedor` | Ver/editar su perfil, inscribirse en convocatorias, crear proyectos, subir entregables a sus proyectos, ver noticias/fases/convocatorias, ver sus propios audit logs |

Ejemplos que demuestran la autorización:

```
GET /reports/dashboard con admin       → 200 OK
GET /reports/dashboard con emprendedor → 403 Forbidden
GET /profiles/ con admin               → lista todos los perfiles
GET /profiles/ con emprendedor         → solo su propio perfil
PUT /profiles/{id} con role=admin desde emprendedor → mantiene role=emprendedor
GET /audit/logs con admin              → todos los logs
GET /audit/logs con emprendedor        → solo sus propios logs (forced user_id)
```

---

## Usuarios de prueba

| Email | Password | Rol |
|---|---|---|
| `admin@parmenia.pe` | `admin123` | admin |
| `carlos.mentor@parmenia.pe` | `mentor123` | mentor |
| `ana.mentor@parmenia.pe` | `mentor456` | mentor |
| `luis.emp@parmenia.pe` | `emp123` | emprendedor (proyecto EcoTrack) |
| `maria.emp@parmenia.pe` | `emp456` | emprendedor |
| `pedro.emp@parmenia.pe` | `emp789` | emprendedor |
| `sofia.emp@parmenia.pe` | `emp012` | emprendedor |

Cargar con `seed.sql` en Supabase SQL Editor.

---

## Endpoints cubiertos

### Autenticación

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/register` | Registro local (solo emprendedor) |
| POST | `/auth/login` | Login local → JWT |
| GET | `/auth/oauth/google/login` | Inicia flujo Authorization Code (302 a Google) |
| GET | `/auth/oauth/google/callback` | Recibe code, intercambia, valida, emite JWT (302 a frontend) |
| POST | `/auth/oauth/google/verify` | Valida Google ID token (demo JWKS) |
| POST | `/auth/oauth/google` | (Legacy) Login con ID token directo |
| GET | `/auth/me` | Usuario autenticado actual |

### Perfiles, Fases, Convocatorias, Inscripciones

| Método | Ruta |
|---|---|
| GET/POST/PUT/DELETE | `/profiles/`, `/profiles/{id}` |
| GET/POST/PUT/DELETE | `/phases/`, `/phases/{id}` |
| GET/POST/PUT/DELETE | `/cohorts/`, `/cohorts/{id}` |
| GET/POST/PUT/DELETE | `/enrollments/`, `/enrollments/{id}` |
| PUT | `/enrollments/{id}/status` |

### Proyectos (CRUD + miembros + mentores + fase)

| Método | Ruta |
|---|---|
| GET | `/projects/`, `/projects/{id}`, `/projects/my-stats`, `/projects/{id}/public-detail` |
| POST/PUT/DELETE | `/projects/`, `/projects/{id}` |
| PUT | `/projects/{id}/phase?phase_id=` |
| GET/POST/DELETE | `/projects/{id}/members`, `/projects/{id}/members/{user_id}` |
| GET/POST/DELETE | `/projects/{id}/mentors`, `/projects/{id}/mentors/{mentor_id}` |

### Entregables y Revisiones

| Método | Ruta |
|---|---|
| GET/POST | `/projects/{id}/deliverables` |
| GET/PUT/DELETE | `/deliverables/{id}` |
| GET/POST | `/deliverables/{id}/reviews` |
| GET/PUT/DELETE | `/reviews/{id}` |

### Comentarios y Notificaciones

| Método | Ruta |
|---|---|
| GET/POST | `/deliverables/{id}/comments` |
| DELETE | `/comments/{comment_id}` |
| GET | `/notifications/`, `/notifications/unread-count` |
| PUT | `/notifications/{id}/read`, `/notifications/read-all` |

### Mentorías (Google Calendar) y Audit Logs (MongoDB)

| Método | Ruta |
|---|---|
| POST | `/integrations/google-calendar/mentorships` |
| GET | `/integrations/mentorships` |
| GET | `/audit/status` |
| GET | `/audit/logs` |
| GET | `/audit/me` |
| POST | `/audit/test` |

### Reportes (admin) y Upload

| Método | Ruta |
|---|---|
| GET | `/reports/dashboard` |
| GET | `/reports/cohort/{id}/progress` |
| POST | `/upload/file` |
