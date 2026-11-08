"""A small offline task-list domain for testing memory retrieval outside chess."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import date
import json
from pathlib import Path

@dataclass
class Task:
    task_id: str
    title: str
    status: str = "open"
    due: str | None = None

def validate_deadline(value: str | None) -> str | None:
    if value is None:
        return None
    date.fromisoformat(value)
    return value

def parse_task(text: str) -> Task:
    doc = json.loads(text)
    if not doc.get("task_id") or not doc.get("title"):
        raise ValueError("task_id and title required")
    return Task(doc["task_id"], doc["title"], doc.get("status", "open"), validate_deadline(doc.get("due")))

def save_tasks(path: Path, tasks: list[Task]) -> None:
    path.write_text(json.dumps([asdict(t) for t in tasks], indent=2), encoding="utf-8")

def load_tasks(path: Path) -> list[Task]:
    if not path.exists():
        return []
    return [parse_task(json.dumps(item)) for item in json.loads(path.read_text(encoding="utf-8"))]

def filter_tasks(tasks: list[Task], status: str) -> list[Task]:
    return [t for t in tasks if t.status == status]

def delete_task(tasks: list[Task], task_id: str) -> list[Task]:
    return [t for t in tasks if t.task_id != task_id]

def render_list(tasks: list[Task]) -> str:
    return "\n".join(f"- {t.title} [{t.status}]" for t in tasks)

def mark_complete(tasks: list[Task], task_id: str) -> list[Task]:
    return [Task(t.task_id, t.title, 'done', t.due) if t.task_id == task_id else t for t in tasks]
