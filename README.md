# Backend MVP de pre-incubación

Backend MVP en FastAPI para una plataforma de pre-incubación. La base de datos ya existe en Supabase/PostgreSQL, por lo que la aplicación solo mapea las tablas existentes con SQLAlchemy y no crea tablas ni migraciones.

## Requisitos

- Python 3.10+
- PostgreSQL/Supabase con el esquema existente

## Instalación

1. Crear entorno virtual:

```bash
python -m venv .venv
```

2. Activar entorno virtual:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Copiar el archivo de variables de entorno:

```bash
copy .env.example .env
```

5. Colocar los valores reales en `.env`:

```env
DATABASE_URL=postgresql://user:password@host:5432/database
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
```

6. Ejecutar el servidor:

```bash
uvicorn app.main:app --reload
```

7. Abrir Swagger:

```text
http://127.0.0.1:8000/docs
```

## Endpoints principales

- `GET /health`
- `GET /posts/`
- `POST /posts/`
- `GET /cohorts/`
- `POST /enrollments/`
- `PATCH /enrollments/{enrollment_id}/status`
- `POST /projects/`
- `GET /projects/`
- `GET /projects/{project_id}`
- `POST /projects/{project_id}/members`
- `POST /projects/{project_id}/mentors`
- `POST /projects/{project_id}/deliverables`
- `GET /projects/{project_id}/deliverables`
- `POST /deliverables/{deliverable_id}/reviews`
