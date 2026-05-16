-- ============================================================
-- migration_delivery_pago.sql
-- Método de pago configurable por delivery.
-- Permite al admin configurar cómo le paga a cada repartidor:
--   'cupo'      → cantidad fija de pedidos mensuales (sistema actual, default)
--   'porPedido' → monto fijo por cada pedido entregado
--   'fija'      → tarifa fija mensual sin importar entregas
--   'externa'   → logística externa (Uber, PedidosYa, etc.)
--
-- Backward-compatible: si los campos están nulos/vacíos,
-- el sistema asume 'cupo' con los defaults históricos.
-- ============================================================

-- Modalidad de pago
ALTER TABLE usuarios
  ADD COLUMN IF NOT EXISTS pago_metodo TEXT DEFAULT 'cupo';

-- Configuración específica del método (estructura JSONB):
--   cupo:      { "cupo_mensual": 100, "premio_x_cupo": 50000 }
--   porPedido: { "monto_por_pedido": 20000 }
--   fija:      { "monto_mensual": 1500000 }
--   externa:   { "plataforma": "uber", "comision_pct": 15, "tarifa_base": 18000 }
ALTER TABLE usuarios
  ADD COLUMN IF NOT EXISTS pago_config JSONB DEFAULT '{}'::jsonb;

-- Notas libres sobre el acuerdo (opcional, máx. 500 chars en frontend)
ALTER TABLE usuarios
  ADD COLUMN IF NOT EXISTS pago_notas TEXT;

-- Constraint suave de valores válidos para pago_metodo
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'usuarios_pago_metodo_chk'
  ) THEN
    ALTER TABLE usuarios
      ADD CONSTRAINT usuarios_pago_metodo_chk
      CHECK (pago_metodo IS NULL OR pago_metodo IN ('cupo','porPedido','fija','externa'));
  END IF;
END$$;

COMMENT ON COLUMN usuarios.pago_metodo IS 'Modalidad de pago del delivery: cupo | porPedido | fija | externa';
COMMENT ON COLUMN usuarios.pago_config IS 'Parámetros del método de pago (JSONB). Estructura depende de pago_metodo.';
COMMENT ON COLUMN usuarios.pago_notas  IS 'Notas libres sobre el acuerdo de pago con el delivery.';
