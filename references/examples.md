# Portable Context Checkpoint Examples

Use these examples as shape guides. Do not copy them verbatim when generating a real checkpoint.

## Compact Mode Example

```md
# CONTEXTO PORTABLE

## Objetivo actual
Corregir la ingestion de imagenes entrantes en un flujo de WhatsApp Web para que aparezcan en Aiuda.

## Estado actual
Se aislo el bug al cliente de Baileys. El backend principal no requeria cambios para este caso.

## Hechos verificados
- El chat afectado existe en la DB y pertenece al canal `whatsapp-web`.
- La foto visible en WhatsApp no se persistio como `message.type = image`.
- El build local del servicio corregido compilo correctamente.

## Inferencias / puntos no confirmados
- Es probable que otras fotos envueltas como `ephemeral` o `view once` fallen igual hasta desplegar.

## Decisiones clave
- Corregir el flujo en el cliente de Baileys, no en el webhook receiver.

## Contexto operativo
- Fecha y hora: 2026-05-07 18:20 America/Mexico_City
- Proyecto activo: `ivana-wa-client-api`
- Rama: `fix/baileys-wrapped-media-ingestion`
- Worktree: `dirty`
- Entorno: `dev`
- Servicios / puertos: AWS CLI profile `chatnshop`, Elastic Beanstalk dev

## Paths y archivos relevantes
- C:/repo/ivana-wa-client-api/src/service/baileys/baileys.service.ts
- C:/repo/ivana-wa-client-api/src/service/baileys/baileys-message-utils.service.ts

## Stack / herramientas
NestJS, Baileys, MySQL, AWS CLI, Elastic Beanstalk.

## Siguientes pasos
- Desplegar el servicio corregido.
- Enviar una foto real desde WhatsApp.
- Confirmar que aparece en Aiuda y en la DB.

## Riesgos / bloqueos
- Sin despliegue, el bug puede seguir ocurriendo en dev.

## Notas importantes
- No incluir credenciales de `.env.dev`; solo referenciar su ubicacion.
```

## Complete Mode Example

```md
# CONTEXTO PORTABLE

## Objetivo actual
Investigar y corregir por que algunas imagenes que si llegan a WhatsApp no se reflejan en Aiuda para la shop Lienzarte en ambiente dev.

## Estado actual
La investigacion ya aislo el problema al flujo de ingestion de `whatsapp-web`. En el chat afectado, las imagenes anteriores si existen en la base de datos, pero la foto del comprobante reportada por negocio no se persistio como mensaje multimedia. Se implemento un ajuste local en el cliente de Baileys para normalizar mensajes envueltos antes de detectar o descargar media.

## Hechos verificados
- El chat `1cfdd4b2-4b55-4ef2-a71d-cef54659c8fe` existe y pertenece a la shop `Lienzarte`.
- El canal del chat es `whatsapp-web`.
- En la DB no hay fila `image` para la foto de comprobante reportada.
- En el codigo original, el servicio revisaba media sobre `waMessage.message` aunque el contenido util venia envuelto.
- El build local del servicio con el parche compilo correctamente.

## Inferencias / puntos no confirmados
- Otras imagenes `ephemeral` o `view once` probablemente fallan por el mismo patron.
- El comportamiento exacto en produccion no se confirmo todavia.

## Decisiones clave
- Mantener el fix acotado al cliente de Baileys.
- No tocar `chatnshop-webhook-receiver` para este bug.
- Validar en vivo con una foto nueva despues del despliegue.

## Contexto operativo
- Fecha y hora: 2026-05-07 18:20 America/Mexico_City
- Proyecto activo: `ivana-wa-client-api`
- Rama: `fix/baileys-wrapped-media-ingestion`
- Worktree: `dirty`
- Entorno: `dev`
- Servicios / puertos: AWS CLI profile `chatnshop`, logs de Elastic Beanstalk, MySQL dev

## Paths y archivos relevantes
- C:/repo/ivana-wa-client-api/src/service/baileys/baileys.service.ts
- C:/repo/ivana-wa-client-api/src/service/baileys/baileys-message-utils.service.ts
- C:/repo/chatnshop-api/src/service/chat/whatsapp-web/whatsapp-web.service.ts
- C:/repo/chatnshop-api/src/controller/chat/whatsapp/whatsapp-web.controller.ts

## Stack / herramientas
NestJS, Baileys, Axios, MySQL, AWS CLI, CloudWatch, Elastic Beanstalk.

## Cambios desde el ultimo checkpoint
- Se descarto una causa en S3 o render de UI para el caso puntual.
- Se confirmo que la perdida ocurre antes de persistir el mensaje.
- Se implemento un helper de normalizacion de wrappers en Baileys.

## Siguientes pasos
- Desplegar la rama corregida del cliente de Baileys al ambiente que atiende la shop.
- Repetir el caso enviando una imagen real por WhatsApp.
- Verificar aparicion en Aiuda, en la tabla `message` y en logs del servicio.

## Riesgos / bloqueos
- El entorno desplegado seguira con el bug hasta que se actualice el servicio.
- Si aparecen wrappers adicionales no contemplados, puede requerirse ampliar la normalizacion.

## Notas importantes
- Redactar secretos; no copiar valores de `.env`.
- Si hay varios repos abiertos, dejar explicito cual es el principal y cual es soporte.
```
