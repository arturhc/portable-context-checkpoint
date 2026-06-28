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

## Output Modes

Support two modes:

- `complete`: default mode. Use for most engineering, debugging, or multi-repo work.
- `compact`: use when the user explicitly asks for something short, lightweight, or easy to paste quickly.

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
- `AWS CLI profile chatnshop is available locally`

Mask nonessential sensitive values with placeholders such as `<redacted>`.

The Codex session file itself may contain sensitive content. It is acceptable to reference the path, but do not quote large raw session chunks into the checkpoint.

### 7. Produce the handoff in the required structure

Use this structure in `complete` mode:

```md
# CONTEXTO PORTABLE

## Objetivo actual
...

## Estado actual
...

## Hechos verificados
...

## Inferencias / puntos no confirmados
...

## Decisiones clave
...

## Contexto operativo
- Fecha y hora:
- Proyecto activo:
- Rama:
- Worktree:
- Entorno:
- Servicios / puertos:

## Fuentes de continuidad del hilo Codex
- Sesion Codex probable:
- Confianza:
- Ultima modificacion:
- Tamano:
- Como consultar sin cargar todo:

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
- Add `## Cambios desde el ultimo checkpoint` only when relevant.
- Keep `## Fuentes de continuidad del hilo Codex` even in compact mode when a session path is available.
- Prefer short paragraphs or flat bullets.
- Prefer absolute paths for files.
- Group related files together when it improves readability.
- Mention only the most relevant files, not every touched file.
- The continuation prompt should instruct the next agent to read the checkpoint first, inspect `git status`, avoid reverting unrelated changes, and use the session JSONL path only for targeted searches.

Recommended continuation prompt shape:

```text
Lee primero este checkpoint completo. Luego revisa `git status` en el repo indicado.
No reviertas cambios existentes sin pedir confirmacion.
Si falta contexto historico, consulta la sesion Codex indicada en `Fuentes de continuidad del hilo Codex` usando busquedas focalizadas, no abriendo el archivo completo.
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
- What should be done next, in order?
- What blockers, risks, or assumptions could cause mistakes?

If any of those are missing, the checkpoint is incomplete.

## Closure Checklist

Before finalizing:

- confirm the current objective is explicit
- confirm the latest validated state overrides older plans
- confirm facts and inferences are separated
- confirm the branch, worktree, and environment are included when relevant
- confirm the Codex session reference is included or explicitly unavailable
- confirm secrets are redacted
- confirm the next steps are ordered and actionable
- confirm the chosen project root for the Markdown file makes sense

## Default Tone

Write like an operational handoff between senior collaborators:

- direct
- concrete
- compact
- immediately useful
