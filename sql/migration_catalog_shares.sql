-- Tabla para compartir productos del catálogo entre usuarios
-- Ejecutar en Supabase SQL Editor:
-- https://supabase.com/dashboard/project/hrpnqbmknmgdaaokjelb/sql
--
-- Segura de re-ejecutar (IF NOT EXISTS + UNIQUE previene duplicados).

CREATE TABLE IF NOT EXISTS catalog_shares (
  id          SERIAL PRIMARY KEY,
  producto_id INTEGER NOT NULL REFERENCES catalogo(id) ON DELETE CASCADE,
  owner_id    INTEGER NOT NULL,
  shared_with INTEGER NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(producto_id, shared_with)
);
