# Datos de prueba extendidos — pendiente aplicar

## Cuándo: solo cuando se esté trabajando sobre pruebas visuales

## Pedidos extra con distintos formatos de dirección
Crear 4 pedidos adicionales probando distintos formatos:

1. **Solo nombre de lugar** (que Google Maps encuentre):
   - cliente: "Carlos Benítez"
   - direccion: "Mercado 4, Asunción, Paraguay"

2. **Solo latitud/longitud**:
   - cliente: "Laura Gómez"
   - direccion: "-25.2867, -57.6470"

3. **Dirección completa con barrio**:
   - cliente: "Miguel Torres"
   - direccion: "Av. Mcal. López 1234, Barrio Manorá, Asunción"

4. **Dirección mínima solo calle y número**:
   - cliente: "Rosa Ferreira"
   - direccion: "Brasil 890"

## Productos extra (2-4 más)
- Fideos Tallarin 500g — presentaciones: [{"nombre":"500g","precio":3200}]
- Leche Entera 1L — presentaciones: [{"nombre":"1L","precio":5800}]
- Arroz Largo Fino 1kg — presentaciones: [{"nombre":"1kg","precio":6500}]

## Perfil del usuario de prueba
Al crear usuarios de prueba, rellenar también:
- whatsapp: "0981000001" (vendedor), "0981000002" (proveedor), "0981000003" (delivery1), "0981000004" (delivery2)
- ciudad: "Asunción"
- barrio: "Centro"
- departamento: "Central"
- pais: "Paraguay"
- vehiculo: "Moto" (para deliveries)
- patente: "AAA 001" (delivery1), "BBB 002" (delivery2)

## Cómo aplicar
Modificar `.agentes/crear-datos-prueba.py` para agregar estos datos antes de correr el tester visual.
