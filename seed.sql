-- ═══════════════════════════════════════════════════════════════
-- PARMENIA — Seed de datos de prueba
-- Ejecutar en: Supabase Dashboard → SQL Editor → pegar y Run
-- ═══════════════════════════════════════════════════════════════

-- Limpiar datos existentes (orden por dependencias)
DELETE FROM mentorships;
DELETE FROM deliverable_comments;
DELETE FROM notifications;
DELETE FROM deliverable_reviews;
DELETE FROM deliverables;
DELETE FROM project_mentors;
DELETE FROM project_members;
DELETE FROM projects;
DELETE FROM enrollments;
DELETE FROM posts;
DELETE FROM phases;
DELETE FROM cohorts;
DELETE FROM profiles WHERE email LIKE '%@parmenia.pe' OR email LIKE '%@ulasalle.edu.pe';

-- ═══════════════════════════════════════════════════════════════
-- 1. PERFILES (usuarios)
-- ═══════════════════════════════════════════════════════════════

INSERT INTO profiles (id, email, password, full_name, faculty, skills, role, created_at) VALUES
('a0000000-0000-0000-0000-000000000001', 'admin@parmenia.pe', 'admin123', 'Administrador Parmenia', 'Dirección', ARRAY['Gestión', 'Administración'], 'admin', NOW()),
('a0000000-0000-0000-0000-000000000002', 'carlos.mentor@parmenia.pe', 'mentor123', 'Carlos Mendoza', 'Ingeniería de Software', ARRAY['Mentoría', 'Lean Startup', 'Finanzas'], 'mentor', NOW()),
('a0000000-0000-0000-0000-000000000003', 'ana.mentor@parmenia.pe', 'mentor456', 'Ana Bustamante', 'Administración', ARRAY['Marketing', 'Estrategia', 'Pitch'], 'mentor', NOW()),
('a0000000-0000-0000-0000-000000000004', 'luis.emp@parmenia.pe', 'emp123', 'Luis Fernández', 'Ingeniería de Software', ARRAY['Python', 'React', 'UX'], 'emprendedor', NOW()),
('a0000000-0000-0000-0000-000000000005', 'maria.emp@parmenia.pe', 'emp456', 'María Quispe', 'Administración', ARRAY['Marketing', 'Diseño'], 'emprendedor', NOW()),
('a0000000-0000-0000-0000-000000000006', 'pedro.emp@parmenia.pe', 'emp789', 'Pedro Castillo', 'Ingeniería Industrial', ARRAY['Logística', 'Operaciones'], 'emprendedor', NOW()),
('a0000000-0000-0000-0000-000000000007', 'sofia.emp@parmenia.pe', 'emp012', 'Sofía Yabar', 'Ingeniería de Software', ARRAY['Flutter', 'Firebase', 'Diseño'], 'emprendedor', NOW());

-- ═══════════════════════════════════════════════════════════════
-- 2. FASES del proceso de incubación
-- ═══════════════════════════════════════════════════════════════

INSERT INTO phases (id, name, "order") VALUES
(1, 'Inscripción', 1),
(2, 'Pre-incubación', 2),
(3, 'Incubación', 3),
(4, 'Pitch Final', 4);

-- Resetear la secuencia de phases
SELECT setval('phases_id_seq', (SELECT MAX(id) FROM phases));

-- ═══════════════════════════════════════════════════════════════
-- 3. CONVOCATORIAS (cohorts)
-- ═══════════════════════════════════════════════════════════════

INSERT INTO cohorts (id, name, description, start_date, end_date, created_at) VALUES
('c0000000-0000-0000-0000-000000000001', 'Convocatoria 2025-I', 'Proceso de incubación del primer semestre 2025. Enfocado en proyectos tecnológicos y de impacto social.', '2025-03-01', '2025-07-31', NOW()),
('c0000000-0000-0000-0000-000000000002', 'Convocatoria 2025-II', 'Proceso de pre-incubación e incubación del segundo semestre 2025. Abierta a todas las facultades.', '2025-08-15', '2025-12-20', NOW()),
('c0000000-0000-0000-0000-000000000003', 'Convocatoria 2026-I', 'Convocatoria actual. Pre-incubación para nuevos emprendedores e incubación para proyectos con tracción.', '2026-03-01', NULL, NOW());

-- ═══════════════════════════════════════════════════════════════
-- 4. INSCRIPCIONES (enrollments)
-- ═══════════════════════════════════════════════════════════════

INSERT INTO enrollments (id, user_id, cohort_id, status, enrollment_date) VALUES
-- Convocatoria 2025-I (ya cerrada)
('e0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000004', 'c0000000-0000-0000-0000-000000000001', 'aceptada', '2025-03-05'),
('e0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000005', 'c0000000-0000-0000-0000-000000000001', 'aceptada', '2025-03-06'),
('e0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000006', 'c0000000-0000-0000-0000-000000000001', 'rechazada', '2025-03-07'),
-- Convocatoria 2026-I (actual)
('e0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000006', 'c0000000-0000-0000-0000-000000000003', 'pendiente', '2026-03-10'),
('e0000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000007', 'c0000000-0000-0000-0000-000000000003', 'pendiente', '2026-03-12');

-- ═══════════════════════════════════════════════════════════════
-- 5. PROYECTOS (de emprendedores aceptados en 2025-I)
-- ═══════════════════════════════════════════════════════════════

INSERT INTO projects (id, cohort_id, name, description, leader_id, current_phase_id, created_at) VALUES
('p0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001',
 'EcoTrack',
 'Aplicación móvil para el seguimiento de residuos reciclables. Conecta ciudadanos con recicladores locales mediante geolocalización.',
 'a0000000-0000-0000-0000-000000000004', 3, '2025-03-15'),
('p0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000001',
 'BakeryHub',
 'Plataforma web para la gestión de pedidos de pequeñas panaderías. Incluye catálogo digital, pedidos online y entrega a domicilio.',
 'a0000000-0000-0000-0000-000000000005', 2, '2025-03-16');

-- ═══════════════════════════════════════════════════════════════
-- 6. MIEMBROS DE PROYECTOS
-- ═══════════════════════════════════════════════════════════════

INSERT INTO project_members (project_id, user_id, joined_at) VALUES
-- EcoTrack: Luis (líder) + María
('p0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000004', '2025-03-15'),
('p0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000005', '2025-03-20'),
-- BakeryHub: María (líder)
('p0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000005', '2025-03-16');

-- ═══════════════════════════════════════════════════════════════
-- 7. MENTORES ASIGNADOS
-- ═══════════════════════════════════════════════════════════════

INSERT INTO project_mentors (project_id, mentor_id, assigned_at) VALUES
('p0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000002', '2025-03-20'),
('p0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000003', '2025-03-22');

-- ═══════════════════════════════════════════════════════════════
-- 8. PUBLICACIONES (noticias/anuncios)
-- ═══════════════════════════════════════════════════════════════

INSERT INTO posts (id, author_id, title, content, image_url, is_published, published_at, created_at) VALUES
('f0000000-0000-0000-0000-000000000001',
 'a0000000-0000-0000-0000-000000000001',
 '¡Abrimos convocatoria 2026-I!',
 'Estimados estudiantes, les damos la bienvenida a la convocatoria 2026-I de Parmenia. Este semestre abrimos plazas para pre-incubación (ideas en etapa temprana) e incubación (proyectos con MVP). Las inscripciones están abiertas hasta el 30 de marzo. ¡No pierdan la oportunidad de transformar su idea en realidad!',
 NULL, true, NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days'),

('f0000000-0000-0000-0000-000000000002',
 'a0000000-0000-0000-0000-000000000001',
 'Taller: Cómo estructurar tu modelo de negocio',
 'El próximo viernes 15 de marzo a las 15:00 hrs realizaremos un taller sobre Canvas de Modelo de Negocio. El taller será dictado por la mentora Ana Bustamante y se realizará en el laboratorio de innovación. Cupos limitados, inscribirse en recepción.',
 NULL, true, NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days'),

('f0000000-0000-0000-0000-000000000003',
 'a0000000-0000-0000-0000-000000000001',
 'Resultados convocatoria 2025-I',
 'Felicitamos a los 12 proyectos seleccionados de la convocatoria 2025-I. Los proyectos comenzarán su proceso de incubación la próxima semana. Agradecemos a todos los que participaron y los invitamos a postular en la próxima convocatoria.',
 NULL, true, NOW() - INTERVAL '30 days', NOW() - INTERVAL '30 days'),

('f0000000-0000-0000-0000-000000000004',
 'a0000000-0000-0000-0000-000000000001',
 'Mentoría 1:1 disponible',
 'Los emprendedores con proyectos activos pueden agendar sesiones de mentoría 1:1 con nuestros mentores. Carlos Mendoza (Lean Startup, Finanzas) y Ana Bustamante (Marketing, Pitch) tienen horarios disponibles. Contactar a coordinación.',
 NULL, true, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),

('f0000000-0000-0000-0000-000000000005',
 'a0000000-0000-0000-0000-000000000001',
 'Borrador: Calendario de entregables 2026-I',
 'Documento en preparación con las fechas de entregables para la convocatoria 2026-I. Se publicará próximamente.',
 NULL, false, NULL, NOW() - INTERVAL '1 hour');

-- ═══════════════════════════════════════════════════════════════
-- 9. ENTREGABLES (de proyectos de 2025-I)
-- ═══════════════════════════════════════════════════════════════

INSERT INTO deliverables (id, project_id, phase_id, uploaded_by, file_url, created_at) VALUES
-- EcoTrack - Fase 1
('d0000000-0000-0000-0000-000000000001',
 'p0000000-0000-0000-0000-000000000001', 1,
 'a0000000-0000-0000-0000-000000000004',
 'https://drive.google.com/file/d/ecotrack-inscripcion.pdf', NOW() - INTERVAL '60 days'),
-- EcoTrack - Fase 2
('d0000000-0000-0000-0000-000000000002',
 'p0000000-0000-0000-0000-000000000001', 2,
 'a0000000-0000-0000-0000-000000000004',
 'https://drive.google.com/file/d/ecotrack-canvas.pdf', NOW() - INTERVAL '40 days'),
-- BakeryHub - Fase 1
('d0000000-0000-0000-0000-000000000003',
 'p0000000-0000-0000-0000-000000000002', 1,
 'a0000000-0000-0000-0000-000000000005',
 'https://drive.google.com/file/d/bakeryhub-inscripcion.pdf', NOW() - INTERVAL '55 days');

-- ═══════════════════════════════════════════════════════════════
-- 10. REVISIONES DE ENTREGABLES
-- ═══════════════════════════════════════════════════════════════

INSERT INTO deliverable_reviews (id, deliverable_id, mentor_id, status, feedback, reviewed_at) VALUES
-- EcoTrack Fase 1: Aprobado
('r0000000-0000-0000-0000-000000000001',
 'd0000000-0000-0000-0000-000000000001',
 'a0000000-0000-0000-0000-000000000002',
 'aprobado',
 'Excelente presentación del problema y la solución. El equipo muestra claridad en el modelo de negocio. Avanzar a la siguiente fase.',
 NOW() - INTERVAL '55 days'),
-- EcoTrack Fase 2: Aprobado
('r0000000-0000-0000-0000-000000000002',
 'd0000000-0000-0000-0000-000000000002',
 'a0000000-0000-0000-0000-000000000002',
 'aprobado',
 'Buen Canvas de modelo de negocio. Sugerencia: definir mejor los canales de distribución. Avanzar a incubación.',
 NOW() - INTERVAL '35 days'),
-- BakeryHub Fase 1: Aprobado
('r0000000-0000-0000-0000-000000000003',
 'd0000000-0000-0000-0000-000000000003',
 'a0000000-0000-0000-0000-000000000003',
 'aprobado',
 'Proyecto interesante con mercado claro. Recomiendo validar el modelo de entrega a domicilio con usuarios piloto.',
 NOW() - INTERVAL '50 days');

-- ═══════════════════════════════════════════════════════════════
-- 11. NOTIFICACIONES (ejemplos)
-- ═══════════════════════════════════════════════════════════════

INSERT INTO notifications (id, user_id, title, message, type, is_read, related_id, created_at) VALUES
('n0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000004',
 'Bienvenido a Parmenia', 'Tu cuenta ha sido creada. Inscríbete en una convocatoria para comenzar.', 'info', true, NULL, NOW() - INTERVAL '30 days'),
('n0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000004',
 'Entregable aprobado', 'Tu entregable de la fase Inscripción fue aprobado.', 'review', true,
 'd0000000-0000-0000-0000-000000000001', NOW() - INTERVAL '55 days'),
('n0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000002',
 'Nuevo entregable', 'El proyecto EcoTrack subió un entregable para la fase Pre-incubación.', 'deliverable', false,
 'd0000000-0000-0000-0000-000000000002', NOW() - INTERVAL '40 days'),
('n0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000004',
 'Nueva mentoría agendada', 'Tienes una mentoría con Carlos Mendoza el día 20/03 a las 15:00.', 'info', false, NULL, NOW() - INTERVAL '2 days');

-- ═══════════════════════════════════════════════════════════════
-- 12. COMENTARIOS EN ENTREGABLES
-- ═══════════════════════════════════════════════════════════════

INSERT INTO deliverable_comments (id, deliverable_id, author_id, content, created_at) VALUES
('cc000000-0000-0000-0000-000000000001',
 'd0000000-0000-0000-0000-000000000001',
 'a0000000-0000-0000-0000-000000000004',
 'Adjuntamos el formulario de inscripción completo con los datos del equipo.', NOW() - INTERVAL '60 days'),
('cc000000-0000-0000-0000-000000000002',
 'd0000000-0000-0000-0000-000000000001',
 'a0000000-0000-0000-0000-000000000002',
 'Perfecto, el formulario está completo. Procedo a revisar.', NOW() - INTERVAL '58 days'),
('cc000000-0000-0000-0000-000000000003',
 'd0000000-0000-0000-0000-000000000002',
 'a0000000-0000-0000-0000-000000000004',
 'Aquí está el Canvas de Modelo de Negocio. Tuvimos algunas dudas sobre los canales de distribución.', NOW() - INTERVAL '40 days'),
('cc000000-0000-0000-0000-000000000004',
 'd0000000-0000-0000-0000-000000000002',
 'a0000000-0000-0000-0000-000000000002',
 'Buen trabajo. Sugiero que definan mejor si van por canales digitales o presenciales. Lo apruebo con esa observación.', NOW() - INTERVAL '37 days');

-- ═══════════════════════════════════════════════════════════════
-- VERIFICACIÓN
-- ═══════════════════════════════════════════════════════════════

SELECT 'Perfiles' as tabla, COUNT(*) as total FROM profiles
UNION ALL SELECT 'Fases', COUNT(*) FROM phases
UNION ALL SELECT 'Convocatorias', COUNT(*) FROM cohorts
UNION ALL SELECT 'Inscripciones', COUNT(*) FROM enrollments
UNION ALL SELECT 'Proyectos', COUNT(*) FROM projects
UNION ALL SELECT 'Miembros', COUNT(*) FROM project_members
UNION ALL SELECT 'Mentores asignados', COUNT(*) FROM project_mentors
UNION ALL SELECT 'Publicaciones', COUNT(*) FROM posts
UNION ALL SELECT 'Entregables', COUNT(*) FROM deliverables
UNION ALL SELECT 'Revisiones', COUNT(*) FROM deliverable_reviews
UNION ALL SELECT 'Notificaciones', COUNT(*) FROM notifications
UNION ALL SELECT 'Comentarios', COUNT(*) FROM deliverable_comments;

-- ═══════════════════════════════════════════════════════════════
-- DATOS SEMBRADOS:
--   7 usuarios (1 admin, 2 mentores, 4 emprendedores)
--   4 fases (Inscripción → Pre-incubación → Incubación → Pitch Final)
--   3 convocatorias (2 pasadas + 1 activa)
--   5 inscripciones (3 aceptadas, 1 rechazada, 2 pendientes)
--   2 proyectos (EcoTrack en Fase 3, BakeryHub en Fase 2)
--   3 miembros de proyectos
--   2 mentores asignados
--   5 publicaciones (4 publicadas + 1 borrador)
--   3 entregables con 3 revisiones aprobadas
--   4 notificaciones (2 leídas, 2 no leídas)
--   4 comentarios en entregables
-- ═══════════════════════════════════════════════════════════════
