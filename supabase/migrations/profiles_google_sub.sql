-- Migración: agregar columna google_sub a profiles
-- Razón: el flujo OAuth 2.0 Authorization Code con Google requiere identificar al usuario
-- por el claim `sub` del proveedor (no por email, que puede cambiar). Esto permite:
--  - Hacer ownership check por `sub` (requisito de la rúbrica)
--  - Relacionar de forma estable al usuario entre login y login (incluso si cambia su email)

ALTER TABLE profiles
    ADD COLUMN IF NOT EXISTS google_sub TEXT UNIQUE;

-- Backfill: si ya existen usuarios creados vía el flujo anterior (ID Token),
-- no podemos recuperar su `sub` retroactivamente — quedará NULL hasta su próximo login,
-- momento en que el backend lo completará. Esta consulta es safe para re-ejecutar.
