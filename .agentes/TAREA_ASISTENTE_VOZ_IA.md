# Feature — Asistente IA con voz para carga de pedidos

## Idea general
Un asistente conversacional dentro de la app que permita crear pedidos,
consultar datos y responder mensajes usando voz o texto. Ideal para
delivery o vendedores ocupados que no pueden tipear.

## Flujo propuesto
1. Usuario toca botón de micrófono 🎙️ o escribe al asistente
2. El asistente escucha/lee el mensaje
3. Interpreta qué quiere hacer (crear pedido, consultar, etc.)
4. Si faltan campos, pregunta específicamente cuáles faltan
5. Una vez completo, crea el registro en el sistema
6. Responde en texto o audio confirmando lo que hizo

## Arquitectura sugerida — 3 modelos en pipeline (todos gratuitos)

| Rol | Modelo sugerido | Por qué |
|-----|----------------|---------|
| Interpretación / extracción | Llama 3.x vía Groq API | Rápido, gratis, excelente para extraer campos estructurados |
| Ejecución (crear pedido, etc.) | Función JS interna del sistema | Ya existe en index.html (DL.saveOrder, etc.) |
| Respuesta humana / conversación | Llama 3.x vía Groq API | Mismo modelo, prompt diferente para respuesta amigable |

Groq ya está integrado en el sistema. Llama 3.3 70B está disponible gratis ahí.

## Tecnología para voz (100% gratis, sin servidor)
- **Entrada de voz**: Web Speech API (SpeechRecognition) — nativo en Chrome/Edge, sin costo
- **Salida de voz**: Web Speech Synthesis (speechSynthesis) — nativo en todos los browsers
- **Alternativa**: botón de audio que graba y transcribe con Whisper (Groq también ofrece Whisper gratis)

## Casos de uso principales
1. Delivery que está en moto y quiere registrar que entregó un pedido → habla, el sistema actualiza
2. Vendedor que recibe un pedido por WhatsApp → dicta los datos al asistente → se crea solo
3. Admin que quiere saber cuántos pedidos pendientes hay → pregunta por voz o texto
4. Asistente recuerda qué campos faltan y los pide uno por uno

## Implementación sugerida (cuando se planifique)
1. Botón flotante 🎙️ en la app (solo visible cuando el usuario está logueado)
2. Panel de chat pequeño (slide-in desde abajo o lateral)
3. Groq API ya configurada — solo agregar prompts de extracción de pedidos
4. Web Speech API para voz de entrada y salida
5. Function calling de Groq para estructurar el pedido antes de guardarlo

## Prioridad: MEDIA — después de seguridad (contraseñas config/SQL)
## Requiere: planificación de prompts y diseño del panel de chat
