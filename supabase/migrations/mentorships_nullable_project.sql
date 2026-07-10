-- Migración: permitir project_id NULL en mentorships
-- Razón: un mentor puede agendar una mentoría general sin asignarla a un proyecto específico.
-- Antes esto causaba IntegrityError en db.commit() después de haber creado ya el evento en Google Calendar,
-- por lo que el evento aparecía en Calendar pero la mentoría no se persistía en BD.

ALTER TABLE mentorships
    ALTER COLUMN project_id DROP NOT NULL;
