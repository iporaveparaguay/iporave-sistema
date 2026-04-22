-- Cambiar columna foto_entrega de boolean a text para almacenar la imagen real (base64)
-- Ejecutar en Supabase SQL Editor: https://supabase.com/dashboard/project/hrpnqbmknmgdaaokjelb/sql

ALTER TABLE pedidos
  ALTER COLUMN foto_entrega TYPE text USING NULL;

-- Los pedidos ya entregados quedan con foto_entrega = NULL (sin foto histórica, es aceptable)
-- Los nuevos pedidos entregados guardarán la imagen en base64
