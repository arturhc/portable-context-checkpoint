#!/usr/bin/env python3
"""Locate the most likely active Codex session and emit a safe reference block.

The script is intentionally conservative: it never reads a whole session file by
default. Codex session JSONL files can become very large, so this utility only
reads a tail window and produces pointers plus query commands for the next agent.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any, Iterable


DEFAULT_TAIL_BYTES = 4 * 1024 * 1024
DEFAULT_LIMIT = 8


def default_sessions_dir() -> Path:
    home = Path(os.path.expanduser("~"))
    return home / ".codex" / "sessions"


def iso_from_timestamp(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts).astimezone().isoformat(timespec="seconds")


def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{num_bytes} B"


def tail_text(path: Path, max_bytes: int) -> str:
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - max_bytes), os.SEEK_SET)
        data = handle.read()
    return data.decode("utf-8", errors="replace")


def iter_jsonl_tail(path: Path, max_bytes: int) -> Iterable[dict[str, Any]]:
    text = tail_text(path, max_bytes)
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            yield item


def extract_text(value: Any, max_chars: int = 240) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    elif isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        text = " ".join(parts)
    elif isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    text = " ".join(text.replace("\x00", " ").split())
    if len(text) > max_chars:
        return text[: max_chars - 3].rstrip() + "..."
    return text


def summarize_tail(path: Path, max_bytes: int, cwd: str | None) -> dict[str, Any]:
    records = list(iter_jsonl_tail(path, max_bytes))
    last_user = ""
    last_assistant = ""
    last_tool = ""
    last_timestamp = ""
    tool_names: list[str] = []
    tail_blob_for_score = ""

    for record in records[-250:]:
        last_timestamp = record.get("timestamp") or last_timestamp
        payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
        record_type = record.get("type")
        payload_type = payload.get("type")

        if record_type == "event_msg":
            message = extract_text(payload.get("message"))
            event_kind = payload.get("type")
            if event_kind == "user_message" and message:
                last_user = message
            elif event_kind == "agent_message" and message:
                last_assistant = message
        elif record_type == "response_item" and payload_type == "message":
            role = payload.get("role")
            text = extract_text(payload.get("content"))
            if role == "user" and text:
                last_user = text
            elif role == "assistant" and text:
                last_assistant = text
        elif record_type == "response_item" and payload_type == "function_call":
            name = str(payload.get("name") or "")
            if name:
                tool_names.append(name)
                last_tool = name

    try:
        tail_blob_for_score = tail_text(path, min(max_bytes, 512 * 1024)).lower()
    except OSError:
        tail_blob_for_score = ""

    score = 0
    now = dt.datetime.now().astimezone()
    modified = dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    age_minutes = max(0.0, (now - modified).total_seconds() / 60)
    if age_minutes <= 15:
        score += 60
    elif age_minutes <= 120:
        score += 35
    elif age_minutes <= 1440:
        score += 15

    if cwd and cwd.lower() in tail_blob_for_score:
        score += 40

    if records:
        score += 10

    if score >= 70:
        confidence = "alta"
    elif score >= 45:
        confidence = "media"
    else:
        confidence = "baja"

    stat = path.stat()
    return {
        "path": str(path),
        "size_bytes": stat.st_size,
        "size_human": human_size(stat.st_size),
        "last_modified": iso_from_timestamp(stat.st_mtime),
        "last_timestamp": last_timestamp,
        "confidence": confidence,
        "score": score,
        "last_user_preview": last_user,
        "last_assistant_preview": last_assistant,
        "last_tool": last_tool,
        "recent_tools": sorted(set(tool_names[-20:])),
    }


def find_sessions(sessions_dir: Path) -> list[Path]:
    if not sessions_dir.exists():
        return []
    return sorted(
        sessions_dir.rglob("*.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def markdown_block(selected: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    path = selected["path"]
    escaped_path = path.replace("`", "\\`")
    lines = [
        "## Fuentes de continuidad del hilo Codex",
        "",
        f"- Sesion Codex probable: `{escaped_path}`",
        f"- Confianza: `{selected['confidence']}`; score: `{selected['score']}`",
        f"- Ultima modificacion: `{selected['last_modified']}`",
        f"- Tamano: `{selected['size_human']}`",
    ]

    if selected.get("last_user_preview"):
        lines.append(f"- Ultimo usuario detectado: {selected['last_user_preview']}")
    if selected.get("last_assistant_preview"):
        lines.append(f"- Ultimo asistente detectado: {selected['last_assistant_preview']}")
    if selected.get("last_tool"):
        lines.append(f"- Ultima herramienta detectada: `{selected['last_tool']}`")

    lines.extend(
        [
            "",
            "Consulta rapida sin cargar todo el archivo:",
            "",
            "```powershell",
            f"Get-Content -Tail 2000 -LiteralPath \"{path}\" | Select-String -Pattern \"PALABRA_CLAVE\" -Context 2,2",
            "```",
            "",
            "Consulta estructurada con este helper:",
            "",
            "```powershell",
            "python scripts/codex_session_probe.py --format markdown",
            "```",
            "",
            "Notas de seguridad:",
            "- El archivo de sesion puede contener rutas, prompts, salidas de herramientas y referencias sensibles.",
            "- No copies el JSONL completo al checkpoint.",
            "- Usa busquedas focalizadas por palabra clave, ruta, servicio, error o timestamp.",
        ]
    )

    if len(candidates) > 1:
        lines.extend(["", "Candidatos recientes:", ""])
        for item in candidates[:5]:
            marker = "seleccionado" if item["path"] == selected["path"] else "alterno"
            lines.append(
                f"- `{marker}` `{item['path']}` | {item['size_human']} | {item['last_modified']} | confianza {item['confidence']}"
            )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Find likely Codex session files for portable handoffs.")
    parser.add_argument("--sessions-dir", default=str(default_sessions_dir()))
    parser.add_argument("--session-path", default="")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--tail-bytes", type=int, default=DEFAULT_TAIL_BYTES)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()

    cwd = str(Path(args.cwd).resolve()) if args.cwd else ""

    if args.session_path:
        session_paths = [Path(args.session_path)]
    else:
        session_paths = find_sessions(Path(args.sessions_dir))[: max(1, args.limit)]

    summaries = [
        summarize_tail(path, args.tail_bytes, cwd)
        for path in session_paths
        if path.exists() and path.is_file()
    ]
    summaries.sort(key=lambda item: (item["score"], item["last_modified"]), reverse=True)

    result = {
        "sessions_dir": str(Path(args.sessions_dir)),
        "cwd": cwd,
        "selected": summaries[0] if summaries else None,
        "candidates": summaries,
    }

    if args.format == "markdown":
        if not summaries:
            print("## Fuentes de continuidad del hilo Codex\n\nNo se encontro ninguna sesion Codex.")
        else:
            print(markdown_block(summaries[0], summaries))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if summaries else 1


if __name__ == "__main__":
    raise SystemExit(main())
