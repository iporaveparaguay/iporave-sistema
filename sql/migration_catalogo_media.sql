-- Migración completa del catálogo — media, precios, inventario y tienda pública
-- Ejecutar en Supabase SQL Editor:
-- https://supabase.com/dashboard/project/hrpnqbmknmgdaaokjelb/sql
--
-- Segura de re-ejecutar (IF NOT EXISTS / IF NOT EXISTS en cada columna).
-- Incluye también proveedor_nombre y catalog_shares de migraciones anteriores.

-- ─── 1. Columnas nuevas en catalogo ──────────────────────────────────────────

ALTER TABLE catalogo
  ADD COLUMN IF NOT EXISTS proveedor_nombre    TEXT      DEFAULT '',
  ADD COLUMN IF NOT EXISTS foto                TEXT      DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS fotos               JSONB     DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS videos              JSONB     DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS descripcion_html    TEXT      DEFAULT '',
  ADD COLUMN IF NOT EXISTS categoria           TEXT      DEFAULT '',
  ADD COLUMN IF NOT EXISTS stock               INTEGER   DEFAULT 0,
  ADD COLUMN IF NOT EXISTS codigo_barras       TEXT      DEFAULT '',
  ADD COLUMN IF NOT EXISTS precio_comparacion  NUMERIC   DEFAULT 0,
  ADD COLUMN IF NOT EXISTS publicar_tienda     BOOLEAN   DEFAULT false;

-- ─── 2. Tabla catalog_shares ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS catalog_shares (
  id          SERIAL    PRIMARY KEY,
  producto_id INTEGER   NOT NULL REFERENCES catalogo(id) ON DELETE CASCADE,
  owner_id    INTEGER   NOT NULL,
  shared_with INTEGER   NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(producto_id, shared_with)
);
