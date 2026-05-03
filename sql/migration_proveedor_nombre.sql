-- Agregar columna proveedor_nombre a la tabla catalogo
-- Ejecutar en Supabase SQL Editor:
-- https://supabase.com/dashboard/project/hrpnqbmknmgdaaokjelb/sql
--
-- Es segura de re-ejecutar (IF NOT EXISTS).
-- No rompe datos existentes: DEFAULT '' mantiene filas anteriores intactas.

ALTER TABLE catalogo
  ADD COLUMN IF NOT EXISTS proveedor_nombre TEXT DEFAULT '';
