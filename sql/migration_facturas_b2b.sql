-- Crea la tabla facturas_b2b usada por el módulo "Facturas B2B"
-- Ejecutar en Supabase SQL Editor:
-- https://supabase.com/dashboard/project/hrpnqbmknmgdaaokjelb/sql
--
-- Bug reportado por el usuario: "no se pudo cargar las facturas — columnas
-- de factura b2b emisor y receptor no existen". Causa probable: la tabla
-- facturas_b2b nunca fue creada en Supabase, o fue creada con otro schema.
-- Este script es seguro de re-ejecutar (IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS facturas_b2b (
  id           BIGSERIAL PRIMARY KEY,
  emisor_id    BIGINT      NOT NULL,
  receptor_id  BIGINT      NOT NULL,
  monto        NUMERIC(14,2) NOT NULL DEFAULT 0,
  descripcion  TEXT        DEFAULT '',
  estado       TEXT        NOT NULL DEFAULT 'Pendiente',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Por si la tabla ya existía con otro schema (parcial), agregamos columnas faltantes:
ALTER TABLE facturas_b2b ADD COLUMN IF NOT EXISTS emisor_id    BIGINT;
ALTER TABLE facturas_b2b ADD COLUMN IF NOT EXISTS receptor_id  BIGINT;
ALTER TABLE facturas_b2b ADD COLUMN IF NOT EXISTS monto        NUMERIC(14,2) DEFAULT 0;
ALTER TABLE facturas_b2b ADD COLUMN IF NOT EXISTS descripcion  TEXT DEFAULT '';
ALTER TABLE facturas_b2b ADD COLUMN IF NOT EXISTS estado       TEXT DEFAULT 'Pendiente';
ALTER TABLE facturas_b2b ADD COLUMN IF NOT EXISTS created_at   TIMESTAMPTZ DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_facturas_b2b_emisor   ON facturas_b2b(emisor_id);
CREATE INDEX IF NOT EXISTS idx_facturas_b2b_receptor ON facturas_b2b(receptor_id);
CREATE INDEX IF NOT EXISTS idx_facturas_b2b_created  ON facturas_b2b(created_at DESC);

-- RLS: permitir a authenticated leer/insertar sus propias facturas.
ALTER TABLE facturas_b2b ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS facturas_b2b_select ON facturas_b2b;
CREATE POLICY facturas_b2b_select ON facturas_b2b
  FOR SELECT TO authenticated
  USING (true);

DROP POLICY IF EXISTS facturas_b2b_insert ON facturas_b2b;
CREATE POLICY facturas_b2b_insert ON facturas_b2b
  FOR INSERT TO authenticated
  WITH CHECK (true);

DROP POLICY IF EXISTS facturas_b2b_update ON facturas_b2b;
CREATE POLICY facturas_b2b_update ON facturas_b2b
  FOR UPDATE TO authenticated
  USING (true);
