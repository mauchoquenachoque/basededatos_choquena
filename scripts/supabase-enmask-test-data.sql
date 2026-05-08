-- =============================================================================
-- Datos de prueba para Enmask + Supabase (PostgreSQL)
-- =============================================================================
-- 1) Supabase Dashboard → SQL Editor → New query → pega y ejecuta (Run).
-- 2) En Enmask crea una conexión tipo PostgreSQL:
--    - host: el de "Database" (ej. db.xxxxx.supabase.co), sin https://
--    - port: 5432 (conexión directa; si usas pooler, prueba 6543 según tu proyecto)
--    - database: postgres
--    - username: postgres
--    - password: la contraseña de la base (Settings → Database)
-- 3) Regla de ejemplo:
--    - target_table: enmask_test_customers
--    - target_column: email
--    - strategy: según quieras probar (hashing da hex de 64 chars; substitution con
--      provider "email" genera correos falsos deterministas)
-- 4) Tras el job, en SQL Editor:
--    SELECT id, email, full_name, phone FROM public.enmask_test_customers ORDER BY email;
--
-- Nota: el backend usa la columna "id" como clave al actualizar filas en Postgres.
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.enmask_test_customers (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email       text NOT NULL,
  full_name   text,
  phone       text,
  created_at  timestamptz DEFAULT now()
);

-- Idempotente: vacía la tabla si vuelves a cargar datos de prueba
TRUNCATE TABLE public.enmask_test_customers;

INSERT INTO public.enmask_test_customers (email, full_name, phone) VALUES
  ('ana.garcia@empresa.com',  'Ana García',        '+52 55 1234 5678'),
  ('bruno@cliente.org',       'Bruno Cliente',     '+34 611 222 333'),
  ('carla.dev@startup.io',    'Carla Developer',   NULL),
  ('diego.lopez@correo.net',  'Diego López',       '+1 415 555 0199');

-- Comprueba antes de enmascarar
SELECT id, email, full_name, phone
FROM public.enmask_test_customers
ORDER BY created_at;
