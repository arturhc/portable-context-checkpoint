---
name: portable-context-checkpoint
description: Create a portable operational handoff for continuing work in a new thread or later session. Use when the user asks for a checkpoint, handoff, context transfer, resume-later package, fresh-thread summary, session continuity package, or reusable project-state snapshot. Best for long technical or product conversations where the next agent needs the current objective, verified status, key decisions, active repo and branch, worktree state, relevant files, tools and services, pending work, important constraints, and a safe pointer to the original Codex session file under ~/.codex/sessions without rereading the whole thread.
---

# Portable Context Checkpoint

## Overview

Generate a copy/paste-ready handoff for starting a new thread without losing continuity.

Do not produce a loose summary. Produce an operational checkpoint that another agent can act on immediately.

Prefer verified facts over recollection. Redact secrets and unnecessary sensitive data. Include only the context that materially helps continuation.

When local Codex session files are available, include a safe reference to the most likely original session JSONL file. This lets the next agent query the source conversation on demand without pasting the whole thread.

Every generated checkpoint must also contain a durable retrieval protocol for the source thread. Treat the original JSONL as immutable source material, the deep index as the first historical retrieval layer, and targeted searches as the final escalation. Do not rely on the next thread retaining this conversation in its active context.

## Output Modes

Support three modes:

- `complete`: default mode. Use for most engineering, debugging, or multi-repo work.
- `compact`: use when the user explicitly asks for something short, lightweight, or easy to paste quickly.
- `deep`: use when the user asks for a very detailed checkpoint, a full-history handoff, "todo el hilo", "super detallado", "hasta atras", or when the thread is long enough that recent context is not enough.

If a previous checkpoint exists or the user asks what changed, include an extra section:

- `Cambios desde el ultimo checkpoint`

See `references/examples.md` for sample output shapes for both modes.

## Workflow

### 1. Reconstruct the real working state

Read the current thread and favor the latest confirmed state over older plans.

If the task involves implementation work, verify the workspace when useful:

- inspect `git status`
- inspect the current branch
- inspect recent diffs or touched files
- verify builds, tests, runtime state, ports, logs, or deployed services only if they matter to the handoff

Do not blindly trust stale earlier statements if later edits, logs, or validations changed the picture.

### 2. Capture the source session reference when available

If the local filesystem exposes Codex session files, run the bundled probe from the skill folder:

```bash
python scripts/codex_session_probe.py --format markdown
```

If the active project path is known and the shell is currently elsewhere, pass it explicitly:

```bash
python scripts/codex_session_probe.py --cwd "/absolute/project/path" --format markdown
```

Use the output as the basis for the checkpoint section `Fuentes de continuidad del hilo Codex`.

Rules:

- Include the session path and query commands, not the full JSONL contents.
- Treat the selected session as `probable`, not guaranteed, unless directly confirmed.
- If several Codex sessions are active, include the top candidates and explain that the newest matching file is most likely.
- If the session file is very large, explicitly warn the next agent to use `tail`, `Select-String`, `rg`, or the helper script instead of opening the whole file.
- If the environment does not expose `~/.codex/sessions`, say `No disponible en este entorno` and continue.

### 2b. Build a deep source index when requested

When mode is `deep`, do not rely only on the recent conversation tail. Use the selected Codex session JSONL as the historical source.

After identifying the likely session path with `codex_session_probe.py`, run:

```bash
python scripts/codex_deep_index.py --session-path "/absolute/path/to/session.jsonl" --format markdown --output "/active/project/root/codex-deep-index-YYYY-MM-DD-HH-mm-ss.md"
```

If the project root is unclear, run without `--output` and use the markdown in memory:

```bash
python scripts/codex_deep_index.py --session-path "/absolute/path/to/session.jsonl" --format markdown
```

Treat the selected session JSONL, referenced with its absolute path, as the historical source of truth. The checkpoint is the current operational map and the deep index is the retrieval map; neither replaces the original JSONL when a historical detail, rationale, or decision must be recovered.

Use the generated deep index as raw material, not as the final checkpoint. Synthesize it into the normal `# CONTEXTO PORTABLE` structure.

Deep mode requirements:

- scan the full JSONL by streaming, not by opening or pasting it whole
- extract a timeline from the beginning, middle, and latest state
- identify major workstreams, projects, deploys, bugs, decisions, AWS resources, database moves, and pending work
- include the deep index file path under `Fuentes de continuidad del hilo Codex` when written
- include targeted search commands for the JSONL
- explicitly say which facts came from the deep index and which were re-verified from the workspace
- redact secrets again before writing the final checkpoint
- include a substantial historical summary of every major workstream discussed in the thread, not only the latest task
- preserve enough timeline, decisions, completed work, reversals, risks, and pending work that a new thread can recover any important topic through the deep index and the source JSONL

If the deep index is too large, read it by sections. Prefer topic samples and the timeline over copying raw output.

### 2c. Include the mandatory thread-memory retrieval protocol

Every checkpoint that has a source session must include `## Protocolo para consultar este hilo` immediately after `## Fuentes de continuidad del hilo Codex`.

The `## Fuentes de continuidad del hilo Codex` section must always include the **absolute path** to the selected session JSONL and state explicitly: `El JSONL es la fuente historica de verdad; el checkpoint y deep index son mapas de recuperacion.` Never provide a relative session path when an absolute path is available.

This section is mandatory in every mode and must tell the next agent, in this exact operational order:

1. Read the checkpoint completely to understand current state, scope, constraints, and the exact JSONL path.
2. Treat the absolute-path JSONL as the historical source of truth. If the user says `busca en nuestro hilo previo X`, the request means consult this JSONL through the safe retrieval strategy, not just the visible conversation tail.
3. Read the deep index, when one exists, before searching the raw JSONL.
4. Use the deep index headings, topic samples, timeline, and recommended searches to identify the smallest relevant historical area.
5. Search the raw JSONL only with narrow terms, a bounded tail, or a line-range helper. Never open, paste, or embed the full JSONL in an agent prompt.
6. Re-verify mutable facts in the workspace, logs, AWS, database, or running services before acting.
7. Add newly confirmed decisions to the next checkpoint so the retrieval chain stays current.

Include concrete PowerShell commands tailored to the selected JSONL and deep-index paths. At minimum provide one `Select-String` example and one bounded `Get-Content -Tail` example. Make it explicit that the raw session may contain secrets and personal data, so retrieved snippets must be redacted before reuse.

The protocol must explicitly tell the next agent that the user may invoke this retrieval at any time with requests such as `busca en nuestro hilo previo lo de X`, `revisa que decidimos sobre Y`, or `ubica el contexto de Z`. In that case, use checkpoint -> deep index -> targeted JSONL search -> live verification, in that order.

If the user asks for semantic retrieval, explain the distinction clearly in the checkpoint:

- The deep index is a structured/lexical retrieval layer, not embeddings.
- A true vector index must be built locally from redacted, bounded chunks; never upload or embed the raw session JSONL with a hosted provider by default.
- A local lexical index plus the deep index is the safe default until a redaction-aware vector index is intentionally implemented.

### 3. Separate verified facts from inference

Classify information before writing:

- `Hechos verificados`: confirmed from the latest thread state, tool output, files, logs, diffs, or runtime checks
- `Inferencias / puntos no confirmados`: likely explanations, assumptions, or unresolved points that were not fully proven

If something is uncertain, label it explicitly instead of smoothing it into the main state.

### 4. Extract only portable context

Capture the information another agent needs immediately:

- current objective
- why it matters
- current implementation or investigation status
- key product or technical decisions
- important absolute paths
- stack, tools, services, URLs, environments, and ports
- next steps in execution order
- known risks, blockers, and constraints

Skip low-value chatter, dead ends, repeated discussion, and verbose play-by-play.

### 5. Capture operational context

Include a concise operational snapshot whenever relevant:

- current date and time
- active project or repo
- branch name
- worktree state such as `clean` or `dirty`
- active environment such as `local-dev`, `dev`, or `prod`
- services, ports, or infrastructure currently involved

If multiple repos are in play, identify the main repo and mention any secondary repos only if they affect continuation.

### 6. Redact sensitive information

Never copy sensitive values into the checkpoint unless the user explicitly asks and it is clearly safe.

Redact or omit:

- API keys
- passwords
- access tokens
- cookies
- private keys
- full `.env` contents
- raw connection strings with credentials
- unnecessary personal data

If sensitive information matters to continuation, mention only its location or role. Example:

- `environment/.env.dev` contains the dev database credentials
- `Cloud provider CLI profile dev is available locally`

Mask nonessential sensitive values with placeholders such as `<redacted>`.

The Codex session file itself may contain sensitive content. It is acceptable to reference the path, but do not quote large raw session chunks into the checkpoint.

### 7. Produce the handoff in the required structure

Use this structure in `complete` and `deep` mode:

```md
# CONTEXTO PORTABLE

## Objetivo actual
...

## Estado actual
...

## Linea de tiempo resumida
...

## Hechos verificados
...

## Inferencias / puntos no confirmados
...

## Decisiones clave
...

## Mapa de proyectos / componentes
...

## Contexto operativo
- Fecha y hora:
- Proyecto activo:
- Rama:
- Worktree:
- Entorno:
- Servicios / puertos:

## Fuentes de continuidad del hilo Codex
- Sesion Codex fuente de verdad (ruta absoluta):
- Declaracion de fuente de verdad: El JSONL es la fuente historica de verdad; el checkpoint y deep index son mapas de recuperacion.
- Confianza:
- Ultima modificacion:
- Tamano:
- Deep index:
- Como consultar sin cargar todo:

## Protocolo para consultar este hilo
...

## Paths y archivos relevantes
- /ruta/completa/archivo1
- /ruta/completa/archivo2

## Stack / herramientas
...

## Siguientes pasos
...

## Riesgos / bloqueos
...

## Prompt recomendado para continuar en nuevo hilo
...

## Notas importantes
...
```

Rules for output shape:

- In `compact` mode, keep the same spirit but compress aggressively.
- In `compact` mode, collapse low-priority detail into short bullets.
- In `complete` mode, omit `## Linea de tiempo resumida` and `## Mapa de proyectos / componentes` if they would add little value.
- In `deep` mode, keep the same structure but expand sections enough to preserve all major workstreams and historical decisions.
- In `deep` mode, write a genuinely comprehensive historical handoff. Cover every high-signal workstream represented in the source thread: product, UI, backend, data, infrastructure, deployment, documentation, testing, operational incidents, reversals, and pending work. Do not reduce a months-long thread to only the last objective.
- A deep checkpoint is not a transcript: retain decisions and outcomes, omit low-value chatter, and route fine detail back to the absolute-path JSONL through targeted commands.
- In `deep` mode, include `## Linea de tiempo resumida` and `## Mapa de proyectos / componentes`.
- Add `## Cambios desde el ultimo checkpoint` only when relevant.
- Keep `## Fuentes de continuidad del hilo Codex` even in compact mode when a session path is available.
- Prefer short paragraphs or flat bullets.
- Prefer absolute paths for files.
- Group related files together when it improves readability.
- Mention only the most relevant files, not every touched file.
- The continuation prompt should instruct the next agent to read the checkpoint first, inspect `git status`, avoid reverting unrelated changes, and use the session JSONL path only for targeted searches.
- In `deep` mode, the continuation prompt should also mention the deep index path, and tell the next agent to consult it before searching the raw JSONL.
- The continuation prompt must mention the `Protocolo para consultar este hilo` and prohibit loading the full raw JSONL.

Recommended continuation prompt shape:

```text
Lee primero este checkpoint completo. El JSONL absoluto indicado en `Fuentes de continuidad del hilo Codex` es la fuente historica de verdad; el checkpoint y deep index solo son mapas para consultarlo sin cargarlo completo.
Luego revisa `git status` en el repo indicado.
No reviertas cambios existentes sin pedir confirmacion.
Si el usuario pide buscar algo del hilo previo, o falta contexto historico, consulta primero el deep index y despues el JSONL absoluto mediante busquedas focalizadas, no abriendo el archivo completo.
Despues continua con el objetivo actual y los siguientes pasos en orden.
```

### 8. Create the Markdown file when appropriate

In addition to responding in chat, create a Markdown file in the root of the active project when all of these are true:

- the active project root is clear
- the filesystem is writable
- writing the file is useful for continuation

If the current shell folder is a nested package or sub-repo but the real project root is clearly a parent folder discussed in the thread, prefer that project root.

If there is no clear project root, if the environment is read-only, or if writing a file would be misleading, return the checkpoint in chat and explicitly say the file was skipped.

Use this filename format:

- `portable-context-checkpoint-YYYY-MM-DD-HH-mm-ss.md`

The file contents must match the generated `# CONTEXTO PORTABLE` block.

## Output Rules

- Write in Spanish unless the user explicitly wants another language.
- Keep the output structured and scannable.
- Prefer concrete facts over narrative.
- Use exact feature names, entities, routes, endpoints, services, branches, ports, and environments when relevant.
- Do not include meta-commentary about how the checkpoint was prepared.
- Do not blur unverified assumptions into confirmed status.
- Do not leak secrets.

## Quality Bar

Before finishing, verify that the checkpoint answers all of these:

- What is the team trying to accomplish right now?
- What already exists and what is already working?
- What was directly verified?
- What remains inferred or unresolved?
- What important product or technical decisions were made?
- Which files and paths should the next agent inspect first?
- Which tools, services, and environments are involved?
- Where can the next agent query the original Codex thread if needed?
- Does the checkpoint include the source JSONL's absolute path and explicitly mark it as the historical source of truth?
- What should be done next, in order?
- What blockers, risks, or assumptions could cause mistakes?
- If deep mode was requested, did the checkpoint cover the full thread's major workstreams instead of only the latest context?
- If deep mode was requested, did it include the deep index path or explain why one was not written?

If any of those are missing, the checkpoint is incomplete.

## Closure Checklist

Before finalizing:

- confirm the current objective is explicit
- confirm the latest validated state overrides older plans
- confirm facts and inferences are separated
- confirm the branch, worktree, and environment are included when relevant
- confirm the Codex session reference is included or explicitly unavailable
- confirm the source JSONL path is absolute and marked as the historical source of truth whenever available
- confirm the deep index was generated when the user requested full-history detail
- confirm `## Protocolo para consultar este hilo` is present whenever a source session is available
- confirm the protocol directs the next agent to checkpoint -> deep index -> targeted raw search -> live re-verification
- confirm secrets are redacted
- confirm the next steps are ordered and actionable
- confirm the chosen project root for the Markdown file makes sense

## Default Tone

Write like an operational handoff between senior collaborators:

- direct
- concrete
- compact
- immediately useful
