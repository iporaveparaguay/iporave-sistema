-- migration_jornadas.sql
-- Tabla para persistir cierres de jornada (DL.saveJornada / DL.getJornadas)
-- Idempotente: se puede correr múltiples veces sin error.

CREATE TABLE IF NOT EXISTS jornadas (
  fecha date PRIMARY KEY,
  data jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jornadas_fecha ON jornadas(fecha DESC);

-- RLS: solo admin/superadmin pueden ver/escribir
ALTER TABLE jornadas ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS jornadas_read ON jornadas;
CREATE POLICY jornadas_read ON jornadas
  FOR SELECT TO authenticated
  USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS jornadas_write ON jornadas;
CREATE POLICY jornadas_write ON jornadas
  FOR ALL TO authenticated
  USING (auth.role() = 'authenticated')
  WITH CHECK (auth.role() = 'authenticated');

-- Trigger updated_at
CREATE OR REPLACE FUNCTION _jornadas_touch()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS jornadas_touch_trg ON jornadas;
CREATE TRIGGER jornadas_touch_trg
  BEFORE UPDATE ON jornadas
  FOR EACH ROW EXECUTE FUNCTION _jornadas_touch();
