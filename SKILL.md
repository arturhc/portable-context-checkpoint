---
name: portable-context-checkpoint
description: Create a reusable context checkpoint for a long conversation thread. Use when the user wants to continue work in a new thread, preserve continuity, avoid re-explaining project state, or package the current work into a clean portable handoff with objectives, current status, decisions, relevant files, tools, pending work, and important restrictions.
---

# Portable Context Checkpoint

## Overview

Generate a copy/paste-ready context block for starting a new thread without losing continuity.

Do not produce a loose summary. Produce an operational handoff that tells another agent exactly:
- what is being worked on now
- why it matters
- what decisions were already made
- which files and paths matter
- which tools, services, and environments are involved
- what should happen next
- what assumptions or restrictions must not be forgotten

## When To Use

Use this skill when the user asks for any of these outcomes:
- create a checkpoint between threads
- package the current context
- summarize the thread for a fresh conversation
- carry over project state into a new chat
- avoid context degradation in a long-running thread
- create a handoff for later continuation

## Workflow

### 1. Reconstruct the real working state

Read the current thread and favor the latest confirmed state over older plans.

If the thread involves code or implementation work, verify the active state from the workspace when useful:
- inspect `git status`
- inspect recent diffs
- inspect the exact files that were touched
- verify builds, tests, or runtime state only if they matter to the handoff

Do not blindly trust stale earlier statements if later edits or validations changed them.

### 2. Extract only portable context

Capture the information that another agent would need immediately:
- current objective
- current implementation status
- key architectural or product decisions
- important absolute file paths
- stack, APIs, infra, tools, URLs, services
- pending work and next steps
- constraints, caveats, and known risks

Skip low-value chatter, dead ends, repeated discussion, and verbose play-by-play.

### 3. Prefer concrete facts

Use:
- exact feature names
- exact routes, endpoints, and entities
- exact absolute paths when referencing files
- exact branch names, commit ids, URLs, environment names, ports, and services when relevant

If something is uncertain, label it clearly as an inference or unresolved point.

### 4. Produce the handoff in the required format

Output a clean block using this exact structure:

```md
# CONTEXTO PORTABLE

## 🎯 Objetivo actual
...

## 📍 Estado actual
...

## 🧠 Decisiones clave
...

## 📂 Paths y archivos relevantes
- /ruta/completa/archivo1
- /ruta/completa/archivo2

## 🛠️ Stack / herramientas
...

## 🔄 Siguientes pasos
...

## ⚠️ Notas importantes
...
```

## Output Rules

- Write in Spanish unless the user explicitly wants another language.
- Keep the output structured and scannable.
- Use short paragraphs or flat bullets.
- Prefer absolute paths for files.
- Group related files together when it improves readability.
- Mention only the most relevant files, not every touched file.
- Include current runtime or deployment state only if it affects continuation.
- Do not include meta-commentary about how you made the summary.
- Do not include "maybe" language unless the point is genuinely uncertain.
- In addition to responding in chat, create a Markdown file in the root of the active project.
- If the current shell folder is a nested package or sub-repository but the real project root is clearly a parent folder discussed in the thread, prefer that project root instead of the literal shell cwd.
- The filename must follow this format: `portable-context-checkpoint-YYYY-MM-DD-HH-mm-ss.md`.
- The file contents must match the generated `# CONTEXTO PORTABLE` block, ready to copy/paste into a new thread.

## Quality Bar

Before finishing, verify that the output answers all of these:
- What is the team trying to accomplish right now?
- What already exists and what is already working?
- What important product or technical decisions were made?
- Where in the codebase should the next agent look first?
- What tools or environments are part of the task?
- What should be done next, in order?
- What pitfalls, assumptions, or restrictions could cause mistakes?

If any of those are missing, the checkpoint is incomplete.

## Default Tone

Write like an operational handoff between senior collaborators:
- direct
- concrete
- compact
- useful immediately

The result should be ready to paste into a brand-new thread with minimal editing.
