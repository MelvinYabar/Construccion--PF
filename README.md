# Parmenia - Plataforma de Pre-incubación (Backend MVP)

Backend REST API para la gestión de la incubadora de empresas **Parmenia**. Digitaliza convocatorias, inscripciones, proyectos, entregables, mentores y publicaciones.

## Tecnologías

| Componente    | Tecnología                      |
| ------------- | ------------------------------- |
| Lenguaje      | Python 3.10+                    |
| Framework     | FastAPI                         |
| ORM           | SQLAlchemy                      |
| Base de datos | PostgreSQL (Supabase)           |
| Autenticación | JWT propio (python-jose, HS256) |
| Servidor ASGI | Uvicorn                         |

## Requisitos

- Python 3.10+
- PostgreSQL (Supabase)
- pip

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/MelvinYabar/Construccion--PF.git
cd Construccion--PF-main-CRUD

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Crear un archivo `.env` en la raíz del proyecto:

```env
DATABASE_URL=postgresql://postgres.epxuvpkzhtnutupfrcnl:Perritox23232@aws-1-us-east-1.pooler.supabase.com:6543/postgres
JWT_SECRET=parmenia-dev-secret-change-in-production
```

## Ejecutar

```bash
uvicorn app.main:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`

Documentación interactiva: `http://127.0.0.1:8000/docs`

## Autenticación

### Registrar usuario

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nuevo@parmenia.pe",
    "password": "123456",
    "full_name": "Nuevo Usuario",
    "faculty": "Ingenieria",
    "skills": ["Python", "React"],
    "role": "emprendedor"
  }'
```

### Iniciar sesión

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@parmenia.pe",
    "password": "admin123"
  }'
```

Respuesta:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": { ... }
}
```

### Usar el token

```bash
curl -X GET http://127.0.0.1:8000/profiles/ \
  -H "Authorization: Bearer AQUI_EL_TOKEN"
```

## Usuarios de prueba

| Email                     | Password  | Rol         |
| ------------------------- | --------- | ----------- |
| admin@parmenia.pe         | admin123  | admin       |
| carlos.mentor@parmenia.pe | mentor123 | mentor      |
| ana.mentor@parmenia.pe    | mentor456 | mentor      |
| luis.emp@parmenia.pe      | emp123    | emprendedor |
| maria.emp@parmenia.pe     | emp456    | emprendedor |
| pedro.emp@parmenia.pe     | emp789    | emprendedor |
| sofia.emp@parmenia.pe     | emp012    | emprendedor |

## Endpoints

### Autenticación

| Método | Ruta             | Descripción                    | Roles       |
| ------ | ---------------- | ------------------------------ | ----------- |
| POST   | `/auth/register` | Registrar nuevo usuario        | Público     |
| POST   | `/auth/login`    | Iniciar sesión                 | Público     |
| GET    | `/auth/me`       | Perfil del usuario autenticado | Autenticado |

### Perfiles

| Método | Ruta             | Descripción           | Roles          |
| ------ | ---------------- | --------------------- | -------------- |
| GET    | `/profiles/`     | Listar perfiles       | Autenticado    |
| GET    | `/profiles/{id}` | Obtener perfil por ID | Autenticado    |
| POST   | `/profiles/`     | Crear perfil          | Admin          |
| PUT    | `/profiles/{id}` | Actualizar perfil     | Admin / Propio |
| DELETE | `/profiles/{id}` | Eliminar perfil       | Admin          |

### Fases

| Método | Ruta           | Descripción         | Roles       |
| ------ | -------------- | ------------------- | ----------- |
| GET    | `/phases/`     | Listar fases        | Autenticado |
| GET    | `/phases/{id}` | Obtener fase por ID | Autenticado |
| POST   | `/phases/`     | Crear fase          | Admin       |
| PUT    | `/phases/{id}` | Actualizar fase     | Admin       |
| DELETE | `/phases/{id}` | Eliminar fase       | Admin       |

### Convocatorias

| Método | Ruta            | Descripción             | Roles       |
| ------ | --------------- | ----------------------- | ----------- |
| GET    | `/cohorts/`     | Listar convocatorias    | Autenticado |
| GET    | `/cohorts/{id}` | Obtener convocatoria    | Autenticado |
| POST   | `/cohorts/`     | Crear convocatoria      | Admin       |
| PUT    | `/cohorts/{id}` | Actualizar convocatoria | Admin       |
| DELETE | `/cohorts/{id}` | Eliminar convocatoria   | Admin       |

### Inscripciones

| Método | Ruta                       | Descripción                  | Roles       |
| ------ | -------------------------- | ---------------------------- | ----------- |
| GET    | `/enrollments/`            | Listar inscripciones         | Autenticado |
| GET    | `/enrollments/{id}`        | Obtener inscripción          | Autenticado |
| POST   | `/enrollments/`            | Inscribirse a convocatoria   | Emprendedor |
| PUT    | `/enrollments/{id}`        | Actualizar inscripción       | Admin       |
| PUT    | `/enrollments/{id}/status` | Aceptar/rechazar inscripción | Admin       |
| DELETE | `/enrollments/{id}`        | Eliminar inscripción         | Admin       |

### Proyectos

| Método | Ruta                                 | Descripción                     | Roles         |
| ------ | ------------------------------------ | ------------------------------- | ------------- |
| GET    | `/projects/`                         | Listar proyectos                | Autenticado   |
| GET    | `/projects/{id}`                     | Detalle con miembros y mentores | Autenticado   |
| POST   | `/projects/`                         | Crear proyecto                  | Emprendedor   |
| PUT    | `/projects/{id}`                     | Actualizar proyecto             | Admin / Líder |
| DELETE | `/projects/{id}`                     | Eliminar proyecto               | Admin         |
| POST   | `/projects/{id}/members`             | Agregar miembro                 | Admin / Líder |
| GET    | `/projects/{id}/members`             | Listar miembros                 | Autenticado   |
| DELETE | `/projects/{id}/members/{user_id}`   | Remover miembro                 | Admin / Líder |
| POST   | `/projects/{id}/mentors`             | Asignar mentor                  | Admin         |
| GET    | `/projects/{id}/mentors`             | Listar mentores                 | Autenticado   |
| DELETE | `/projects/{id}/mentors/{mentor_id}` | Desasignar mentor               | Admin         |

### Publicaciones

| Método | Ruta          | Descripción            | Roles          |
| ------ | ------------- | ---------------------- | -------------- |
| GET    | `/posts/`     | Listar publicaciones   | Autenticado    |
| GET    | `/posts/{id}` | Obtener publicación    | Autenticado    |
| POST   | `/posts/`     | Crear publicación      | Admin / Mentor |
| PUT    | `/posts/{id}` | Actualizar publicación | Admin / Autor  |
| DELETE | `/posts/{id}` | Eliminar publicación   | Admin / Autor  |

### Entregables

| Método | Ruta                          | Descripción           | Roles                |
| ------ | ----------------------------- | --------------------- | -------------------- |
| GET    | `/projects/{id}/deliverables` | Listar entregables    | Autenticado          |
| GET    | `/deliverables/{id}`          | Obtener entregable    | Autenticado          |
| POST   | `/projects/{id}/deliverables` | Subir entregable      | Miembro del proyecto |
| PUT    | `/deliverables/{id}`          | Actualizar entregable | Admin / Subidor      |
| DELETE | `/deliverables/{id}`          | Eliminar entregable   | Admin / Subidor      |

### Revisiones de Entregables

| Método | Ruta                         | Descripción         | Roles                  |
| ------ | ---------------------------- | ------------------- | ---------------------- |
| GET    | `/deliverables/{id}/reviews` | Listar revisiones   | Autenticado            |
| GET    | `/reviews/{id}`              | Obtener revisión    | Autenticado            |
| POST   | `/deliverables/{id}/reviews` | Crear revisión      | Mentor asignado        |
| PUT    | `/reviews/{id}`              | Actualizar revisión | Admin / Mentor revisor |
| DELETE | `/reviews/{id}`              | Eliminar revisión   | Admin                  |

## Estructura del proyecto

```
app/
├── __init__.py
├── main.py              # Aplicación FastAPI, inclusión de routers
├── auth.py              # Autenticación JWT, roles, permisos
├── database.py          # Conexión a PostgreSQL
├── models.py            # Modelos SQLAlchemy (10 tablas)
├── schemas.py           # Schemas Pydantic (entrada/salida)
└── routers/
    ├── __init__.py
    ├── auth.py           # Register, Login, Me
    ├── profiles.py       # CRUD perfiles
    ├── phases.py         # CRUD fases
    ├── cohorts.py        # CRUD convocatorias
    ├── enrollments.py    # CRUD inscripciones
    ├── projects.py       # CRUD proyectos + miembros + mentores
    ├── posts.py          # CRUD publicaciones
    └── deliverables.py   # CRUD entregables + revisiones
```
