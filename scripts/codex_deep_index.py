#!/usr/bin/env python3
"""Build a bounded, redacted deep index from a Codex session JSONL file.

This script is for handoff preparation. It streams the whole JSONL file without
loading it all into memory, extracts useful continuity anchors, and emits a
safe markdown/json index that a next agent can use before writing the final
portable checkpoint.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


TOPIC_KEYWORDS: dict[str, list[str]] = {
    "objectives-decisions": ["objective", "objetivo", "requirement", "requisito", "decision", "decisión", "agreed", "acordado"],
    "frontend-ui": ["frontend", "ui", "component", "componente", "layout", "responsive", "react", "angular", "vue", "css"],
    "backend-api": ["backend", "api", "endpoint", "controller", "service", "server", "graphql", "grpc", "webhook"],
    "data-database": ["database", "base de datos", "schema", "migration", "migración", "sql", "table", "query", "snapshot"],
    "infrastructure-cloud": ["infrastructure", "infraestructura", "cloud", "network", "iam", "terraform", "kubernetes", "docker"],
    "deployment-operations": ["deploy", "deployment", "despliegue", "release", "production", "producción", "staging", "rollback", "logs"],
    "testing-quality": ["test", "testing", "prueba", "pytest", "jest", "lint", "build", "ci", "check"],
    "security-privacy": ["security", "seguridad", "auth", "oauth", "permission", "secret", "vulnerability", "privacy", "redact"],
    "automation-jobs": ["automation", "automatización", "scheduled", "scheduler", "cron", "job", "queue", "worker"],
    "integrations-messaging": ["integration", "integración", "webhook", "message", "mensaje", "email", "notification", "notificación"],
    "documentation-handoff": ["documentation", "documentación", "readme", "handoff", "checkpoint", "context", "jsonl"],
}


MILESTONE_PATTERNS = [
    r"\blisto\b",
    r"\bya qued[oó]\b",
    r"\bdespleg",
    r"\bimplement",
    r"\bvalid",
    r"\bcorreg",
    r"\barregl",
    r"\bpush",
    r"\bcommit",
    r"\bcre[eé]",
    r"\bborr",
    r"\bnecesito\b",
    r"\bquiero\b",
    r"\bhaz\b",
]


SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b"), "<aws-access-key-redacted>"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\b"), "<jwt-redacted>"),
    (
        re.compile(
            r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|db_password|stripe[_-]?secret)\b"
            r"\s*[:=]\s*['\"]?[^'\"\s,;]+"
        ),
        r"\1=<redacted>",
    ),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "<private-key-redacted>"),
]


def default_sessions_dir() -> Path:
    return Path(os.path.expanduser("~")) / ".codex" / "sessions"


def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{num_bytes} B"


def redact(text: str) -> str:
    redacted = text
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def compact_text(value: Any, max_chars: int = 420) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    elif isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
            elif isinstance(item, str):
                parts.append(item)
        text = " ".join(parts)
    elif isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    text = " ".join(text.replace("\x00", " ").split())
    text = redact(text)
    if len(text) > max_chars:
        return text[: max_chars - 3].rstrip() + "..."
    return text


def parse_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {"raw": raw}
    return {}


def iter_records(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                yield record


def find_latest_session(sessions_dir: Path) -> Path | None:
    if not sessions_dir.exists():
        return None
    candidates = sorted(sessions_dir.rglob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def classify_topics(text: str) -> tuple[list[str], list[str]]:
    lowered = text.lower()
    topics: list[str] = []
    matched_keywords: list[str] = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        matches = [keyword for keyword in keywords if re.search(rf"(?<![\w-]){re.escape(keyword)}", lowered)]
        if matches:
            topics.append(topic)
            matched_keywords.extend(matches)
    return topics or ["general"], matched_keywords


def is_milestone(text: str, role: str) -> bool:
    lowered = text.lower()
    if role == "tool":
        return any(
            token in lowered
            for token in [
                "git ", "npm ", "pnpm ", "yarn ", "python ", "pytest ",
                "dotnet ", "cargo ", "go ", "docker ", "kubectl ",
                "terraform ", "deploy", "push", "test", "build",
            ]
        )
    return any(re.search(pattern, lowered) for pattern in MILESTONE_PATTERNS)


def extract_event(record: dict[str, Any]) -> dict[str, str] | None:
    timestamp = str(record.get("timestamp") or "")
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    record_type = record.get("type")
    payload_type = payload.get("type")

    if record_type == "event_msg":
        kind = payload.get("type")
        if kind == "user_message":
            text = compact_text(payload.get("message"))
            return {"timestamp": timestamp, "role": "user", "kind": "message", "text": text} if text else None
        if kind == "agent_message":
            text = compact_text(payload.get("message"))
            return {"timestamp": timestamp, "role": "assistant", "kind": "message", "text": text} if text else None

    if record_type == "response_item" and payload_type == "message":
        role = str(payload.get("role") or "unknown")
        text = compact_text(payload.get("content"))
        return {"timestamp": timestamp, "role": role, "kind": "message", "text": text} if text else None

    if record_type == "response_item" and payload_type == "function_call":
        name = str(payload.get("name") or "tool")
        args = parse_arguments(payload.get("arguments"))
        command = args.get("command") or args.get("cmd") or args.get("query") or args.get("search_query") or args.get("workdir") or args
        text = compact_text(command, max_chars=520)
        return {"timestamp": timestamp, "role": "tool", "kind": name, "text": text}

    return None


def build_index(path: Path, max_events_per_topic: int, recent_limit: int) -> dict[str, Any]:
    topic_counts: Counter[str] = Counter()
    search_term_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    tool_counts: Counter[str] = Counter()
    first_seen: dict[str, str] = {}
    last_seen: dict[str, str] = {}
    topic_samples: dict[str, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=max_events_per_topic))
    timeline: list[dict[str, Any]] = []
    recent: deque[dict[str, Any]] = deque(maxlen=recent_limit)
    seen_events: set[tuple[str, str, str, str]] = set()
    line_count = 0
    event_count = 0

    for record in iter_records(path):
        line_count += 1
        event = extract_event(record)
        if not event:
            continue
        signature = (
            event.get("timestamp", "")[:19],
            event.get("role", ""),
            event.get("kind", ""),
            event.get("text", "")[:500],
        )
        if signature in seen_events:
            continue
        seen_events.add(signature)
        event_count += 1
        role = event["role"]
        text = event["text"]
        role_counts[role] += 1
        if role == "tool":
            tool_counts[event["kind"]] += 1
        topics, matched_keywords = classify_topics(text)
        search_term_counts.update(matched_keywords)
        event_with_topics = {**event, "topics": topics}
        recent.append(event_with_topics)

        for topic in topics:
            topic_counts[topic] += 1
            first_seen.setdefault(topic, event["timestamp"])
            last_seen[topic] = event["timestamp"]
            if is_milestone(text, role):
                topic_samples[topic].append(event_with_topics)

        if is_milestone(text, role):
            timeline.append(event_with_topics)

    stat = path.stat()
    return {
        "session_path": str(path),
        "size_bytes": stat.st_size,
        "size_human": human_size(stat.st_size),
        "last_modified": dt.datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
        "line_count": line_count,
        "event_count": event_count,
        "role_counts": dict(role_counts),
        "tool_counts": dict(tool_counts),
        "search_terms": [term for term, _ in search_term_counts.most_common(8)],
        "topics": [
            {
                "topic": topic,
                "count": count,
                "first_seen": first_seen.get(topic, ""),
                "last_seen": last_seen.get(topic, ""),
                "samples": list(topic_samples.get(topic, [])),
            }
            for topic, count in topic_counts.most_common()
        ],
        "timeline": timeline,
        "recent": list(recent),
    }


def md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def markdown(index: dict[str, Any], max_timeline: int) -> str:
    session_path = index["session_path"]
    search_terms = index.get("search_terms") or ["error", "decision", "todo"]
    pattern_args = ",".join(f'"{term}"' for term in search_terms[:5])
    lines = [
        "# DEEP CODEX SESSION INDEX",
        "",
        "Este indice fue generado recorriendo el JSONL completo por streaming. Usalo como materia prima para redactar el checkpoint final; no sustituye el juicio del agente.",
        "",
        "## Fuente",
        f"- Sesion: `{session_path}`",
        f"- Tamano: `{index['size_human']}`",
        f"- Ultima modificacion: `{index['last_modified']}`",
        f"- Lineas leidas: `{index['line_count']}`",
        f"- Eventos extraidos: `{index['event_count']}`",
        "",
        "## Conteo por rol",
    ]
    for role, count in sorted(index["role_counts"].items()):
        lines.append(f"- `{role}`: {count}")

    if index["tool_counts"]:
        lines.extend(["", "## Herramientas detectadas"])
        for tool, count in sorted(index["tool_counts"].items(), key=lambda item: item[1], reverse=True):
            lines.append(f"- `{tool}`: {count}")

    lines.extend(["", "## Inventario de temas", "", "| Tema | Eventos | Primero | Ultimo |", "| --- | ---: | --- | --- |"])
    for topic in index["topics"]:
        lines.append(
            f"| `{topic['topic']}` | {topic['count']} | {md_escape(topic['first_seen'])} | {md_escape(topic['last_seen'])} |"
        )

    lines.extend(["", "## Muestras por tema"])
    for topic in index["topics"]:
        samples = topic.get("samples") or []
        if not samples:
            continue
        lines.extend(["", f"### {topic['topic']}"])
        for sample in samples[-8:]:
            stamp = sample.get("timestamp") or "sin timestamp"
            role = sample.get("role") or "unknown"
            text = sample.get("text") or ""
            lines.append(f"- `{stamp}` `{role}`: {text}")

    lines.extend(["", "## Timeline de hitos"])
    timeline = index["timeline"]
    if len(timeline) > max_timeline:
        head = timeline[: max_timeline // 2]
        tail = timeline[-(max_timeline - len(head)) :]
        timeline_to_print = head + [{"timestamp": "...", "role": "...", "kind": "...", "text": f"{len(timeline) - len(head) - len(tail)} hitos omitidos", "topics": []}] + tail
    else:
        timeline_to_print = timeline
    for item in timeline_to_print:
        topics = ", ".join(item.get("topics") or [])
        lines.append(f"- `{item.get('timestamp') or ''}` `{item.get('role')}` `{topics}`: {item.get('text')}")

    lines.extend(["", "## Eventos recientes"])
    for item in index["recent"][-20:]:
        topics = ", ".join(item.get("topics") or [])
        lines.append(f"- `{item.get('timestamp') or ''}` `{item.get('role')}` `{topics}`: {item.get('text')}")

    lines.extend(
        [
            "",
            "## Busquedas focalizadas recomendadas",
            "",
            "```powershell",
            f"Select-String -LiteralPath \"{session_path}\" -Pattern {pattern_args} -Context 2,2",
            f"Get-Content -LiteralPath \"{session_path}\" -Tail 2000 | Select-String -Pattern {pattern_args} -Context 2,2",
            "```",
            "",
            "## Reglas de seguridad",
            "- El indice ya aplica redaccion basica, pero el agente debe volver a revisar antes de copiar contenido al checkpoint final.",
            "- No copiar secretos, tokens, passwords, dumps, PEMs, cookies ni JSONL crudo.",
            "- Usar este indice para encontrar zonas relevantes y luego hacer busquedas especificas si falta detalle.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a redacted deep index from a Codex session JSONL.")
    parser.add_argument("--session-path", default="")
    parser.add_argument("--sessions-dir", default=str(default_sessions_dir()))
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", default="")
    parser.add_argument("--max-events-per-topic", type=int, default=35)
    parser.add_argument("--max-timeline", type=int, default=220)
    parser.add_argument("--recent-limit", type=int, default=80)
    args = parser.parse_args()

    path = Path(args.session_path) if args.session_path else find_latest_session(Path(args.sessions_dir))
    if not path or not path.exists():
        print("No Codex session JSONL found.")
        return 1

    index = build_index(path, args.max_events_per_topic, args.recent_limit)
    rendered = markdown(index, args.max_timeline) if args.format == "markdown" else json.dumps(index, ensure_ascii=False, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        print(str(output_path))
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
