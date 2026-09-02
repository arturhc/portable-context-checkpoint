# Portable Context Checkpoint Examples

Use these examples only as shape guides. Replace every placeholder with facts verified from the active thread and workspace. Do not copy project names, paths, technologies, or conclusions from an example into a real checkpoint.

## Deep Mode Notes

Use `deep` mode when the user asks for a full-history handoff. The checkpoint should still use `# CONTEXTO PORTABLE`, but it should include:

- `## Linea de tiempo resumida`
- `## Mapa de proyectos / componentes`
- `Deep index:` under `## Fuentes de continuidad del hilo Codex`
- `## Protocolo para consultar este hilo` immediately after the continuity sources
- the absolute JSONL path, explicitly identified as the historical source of truth

Example source line:

```md
- Deep index: `C:/workspace/project/codex-deep-index-YYYY-MM-DD-HH-mm-ss.md`
```

The deep index is not the final answer. It is a structured and lexical evidence map used to write the final checkpoint.

## Compact Mode Example

````md
# CONTEXTO PORTABLE

## Objetivo actual
Corregir una validacion de configuracion que impide iniciar el servicio en el entorno de desarrollo.

## Estado actual
La causa se aislo al cargador de configuracion. Existe un ajuste local y la prueba afectada ya pasa.

## Hechos verificados
- El error se reproduce con la configuracion de desarrollo.
- La validacion rechazaba un valor opcional ausente.
- La prueba focalizada pasa con el ajuste local.

## Inferencias / puntos no confirmados
- Falta confirmar el conjunto completo de pruebas.

## Decisiones clave
- Mantener el cambio acotado al cargador de configuracion.

## Contexto operativo
- Fecha y hora: `YYYY-MM-DD HH:mm Zona/Horaria`
- Proyecto activo: `C:/workspace/project`
- Rama: `fix/config-validation`
- Worktree: `dirty`
- Entorno: `local-dev`
- Servicios / puertos: servicio local en `<port>`

## Fuentes de continuidad del hilo Codex
- Sesion Codex fuente de verdad (ruta absoluta): `C:/Users/example/.codex/sessions/YYYY/MM/DD/rollout-...jsonl`
- Declaracion de fuente de verdad: El JSONL es la fuente historica de verdad; el checkpoint y deep index son mapas de recuperacion.
- Confianza: `alta`
- Deep index: no generado en modo compacto.
- Como consultar sin cargar todo: usar el protocolo siguiente.

## Protocolo para consultar este hilo
1. Leer primero este checkpoint completo y conservar la ruta JSONL exacta.
2. Tratar el JSONL absoluto como fuente historica de verdad.
3. Leer primero el deep index cuando exista.
4. Usar sus temas y linea de tiempo para acotar la busqueda.
5. Consultar el JSONL solo con terminos estrechos o un tail limitado:
   - `Select-String -Path "C:/Users/example/.codex/sessions/YYYY/MM/DD/rollout-...jsonl" -Pattern "config validation" -Context 2,2`
   - `Get-Content -LiteralPath "C:/Users/example/.codex/sessions/YYYY/MM/DD/rollout-...jsonl" -Tail 2000 | Select-String -Pattern "failing test" -Context 2,2`
6. Re-verificar en el workspace, logs y servicios cualquier dato mutable.
7. Incorporar las nuevas decisiones confirmadas al siguiente checkpoint.

El usuario puede activar este flujo con peticiones como `busca en nuestro hilo previo lo de X`. Seguir siempre checkpoint -> deep index -> busqueda focalizada en JSONL -> verificacion en vivo. Nunca abrir, pegar ni cargar el JSONL completo en un prompt; puede contener secretos y datos personales, por lo que cualquier fragmento recuperado debe redactarse antes de reutilizarse.

## Paths y archivos relevantes
- C:/workspace/project/src/config_loader.py
- C:/workspace/project/tests/test_config_loader.py

## Stack / herramientas
Lenguaje y framework del proyecto, runner de pruebas y Git.

## Siguientes pasos
- Ejecutar el conjunto completo de pruebas.
- Iniciar el servicio con la configuracion de desarrollo.
- Confirmar que no se revirtieron cambios ajenos.

## Riesgos / bloqueos
- Otros entornos pueden usar combinaciones de configuracion todavia no verificadas.

## Prompt recomendado para continuar en nuevo hilo
Lee primero este checkpoint completo y su `Protocolo para consultar este hilo`. El JSONL absoluto indicado en `Fuentes de continuidad del hilo Codex` es la fuente historica de verdad; el checkpoint y deep index son mapas de recuperacion. Luego revisa `git status` en `C:/workspace/project`. No reviertas cambios existentes sin pedir confirmacion. Si el usuario pide contexto previo, consulta primero el deep index cuando exista y despues el JSONL con busquedas focalizadas. Nunca cargues el JSONL completo. Despues continua con los siguientes pasos en orden.

## Notas importantes
- No incluir valores de archivos de secretos; solo referenciar su ubicacion cuando sea necesario.
````

## Complete Mode Example

````md
# CONTEXTO PORTABLE

## Objetivo actual
Investigar y corregir por que un proceso en segundo plano sigue usando configuracion anterior despues de un despliegue al entorno de pruebas.

## Estado actual
La investigacion aislo el comportamiento al ciclo de vida del worker. La API principal carga la configuracion nueva, pero el worker activo no se reinicio durante el ultimo despliegue.

## Hechos verificados
- El archivo de configuracion desplegado contiene el valor esperado.
- El proceso de API reporta la version nueva.
- El worker activo se inicio antes del ultimo despliegue.
- Reiniciar el worker en local hace que adopte la configuracion nueva.

## Inferencias / puntos no confirmados
- El procedimiento de despliegue del entorno de pruebas probablemente omite reiniciar workers.
- Falta confirmar el comportamiento en el entorno desplegado.

## Decisiones clave
- Corregir el procedimiento de despliegue en vez de duplicar la lectura de configuracion en cada tarea.
- Validar primero en el entorno de pruebas.

## Contexto operativo
- Fecha y hora: `YYYY-MM-DD HH:mm Zona/Horaria`
- Proyecto activo: `C:/workspace/project`
- Rama: `fix/restart-background-worker`
- Worktree: `dirty`
- Entorno: `test`
- Servicios / puertos: API, worker y almacenamiento de configuracion

## Fuentes de continuidad del hilo Codex
- Sesion Codex fuente de verdad (ruta absoluta): `C:/Users/example/.codex/sessions/YYYY/MM/DD/rollout-...jsonl`
- Declaracion de fuente de verdad: El JSONL es la fuente historica de verdad; el checkpoint y deep index son mapas de recuperacion.
- Confianza: `alta`; score: `<probe-score>`
- Ultima modificacion: `YYYY-MM-DDTHH:mm:ss-00:00`
- Tamano: `<session-size>`
- Deep index: no generado en modo completo.
- Como consultar sin cargar todo:

```powershell
Get-Content -LiteralPath "C:/Users/example/.codex/sessions/YYYY/MM/DD/rollout-...jsonl" -Tail 2000 | Select-String -Pattern "worker restart" -Context 2,2
```

- Nota de seguridad: el JSONL puede contener salidas de herramientas y referencias sensibles; no copiarlo completo.

## Protocolo para consultar este hilo
1. Leer completamente este checkpoint para conocer el estado, restricciones y ruta JSONL exacta.
2. Tratar el JSONL absoluto como fuente historica de verdad. Si el usuario dice `busca en nuestro hilo previo X`, consultar esta fuente y no limitarse al contexto visible.
3. Leer el deep index antes del JSONL cuando exista.
4. Usar sus headings, muestras, linea de tiempo y busquedas recomendadas para identificar el area historica minima.
5. Consultar el JSONL solamente con terminos estrechos, rangos o un tail limitado:

```powershell
Select-String -Path "C:/Users/example/.codex/sessions/YYYY/MM/DD/rollout-...jsonl" -Pattern "deployment|worker|configuration" -Context 2,2
Get-Content -LiteralPath "C:/Users/example/.codex/sessions/YYYY/MM/DD/rollout-...jsonl" -Tail 2000 | Select-String -Pattern "restart" -Context 2,2
```

6. Re-verificar los hechos mutables en el workspace, logs y servicios activos.
7. Añadir las decisiones recien confirmadas al siguiente checkpoint.

El usuario puede pedir en cualquier momento `revisa que decidimos sobre Y` o `ubica el contexto de Z`. Seguir checkpoint -> deep index -> busqueda focalizada en JSONL -> verificacion en vivo. Nunca abrir, pegar ni incluir el JSONL completo en un prompt. Puede contener secretos y datos personales; redactar los fragmentos recuperados antes de reutilizarlos. El deep index es una capa estructurada/lexica, no embeddings; un indice vectorial real debe construirse localmente con fragmentos acotados y redactados.

## Paths y archivos relevantes
- C:/workspace/project/deploy/restart_workers.ps1
- C:/workspace/project/src/worker.py
- C:/workspace/project/tests/test_worker_config.py

## Stack / herramientas
Lenguaje y framework del proyecto, sistema de despliegue, runner de pruebas y Git.

## Cambios desde el ultimo checkpoint
- Se descarto que el archivo de configuracion estuviera desactualizado.
- Se confirmo que el worker conserva el estado anterior al despliegue.
- Se preparo un cambio acotado al procedimiento de reinicio.

## Siguientes pasos
- Ejecutar las pruebas del worker y del procedimiento de despliegue.
- Aplicar el cambio al entorno de pruebas.
- Confirmar la version del worker y ejecutar una tarea controlada.

## Riesgos / bloqueos
- Reiniciar workers puede interrumpir tareas activas; verificar la estrategia de drenado antes del despliegue.
- El estado en produccion no se ha verificado.

## Prompt recomendado para continuar en nuevo hilo
Lee primero este checkpoint completo y su `Protocolo para consultar este hilo`. El JSONL absoluto indicado en `Fuentes de continuidad del hilo Codex` es la fuente historica de verdad; el checkpoint y deep index son mapas de recuperacion. Luego revisa `git status` en los repos indicados. No reviertas cambios existentes sin pedir confirmacion. Si falta contexto historico, consulta primero el deep index cuando exista y despues el JSONL mediante busquedas focalizadas. Nunca cargues el JSONL completo. Despues continua con el objetivo actual y ejecuta los siguientes pasos en orden.

## Notas importantes
- Redactar secretos y datos personales antes de reutilizar fragmentos del hilo.
- Sustituir todos los placeholders por valores verificados en el checkpoint real.
````
