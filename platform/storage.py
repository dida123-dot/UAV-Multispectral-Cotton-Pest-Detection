"""检测任务存储（SQLite）。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id    TEXT PRIMARY KEY,
    filename   TEXT NOT NULL,
    created_at TEXT NOT NULL,
    model      TEXT NOT NULL,
    width      INTEGER NOT NULL,
    height     INTEGER NOT NULL,
    total      INTEGER NOT NULL,
    payload    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS detections (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id    TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    cls_name   TEXT NOT NULL,
    conf       REAL NOT NULL,
    severity   INTEGER NOT NULL,
    x1 INTEGER NOT NULL, y1 INTEGER NOT NULL, x2 INTEGER NOT NULL, y2 INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_detections_task ON detections(task_id);
"""


class Store:
    def __init__(self, db_path: str | Path):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def save(self, task_id: str, filename: str, model: str, image_shape: tuple[int, int], result: dict) -> None:
        height, width = image_shape
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO tasks (task_id, filename, created_at, model, width, height, total, payload)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    task_id,
                    filename,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    model,
                    width,
                    height,
                    result["summary"]["total"],
                    json.dumps(result, ensure_ascii=False),
                ),
            )
            conn.executemany(
                "INSERT INTO detections (task_id, cls_name, conf, severity, x1, y1, x2, y2)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (task_id, d["cls_name"], d["conf"], d["severity"], *d["bbox"])
                    for d in result["detections"]
                ],
            )

    def get(self, task_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            return None
        payload = json.loads(row["payload"])
        payload.update(
            {
                "task_id": row["task_id"],
                "image": row["filename"],
                "created_at": row["created_at"],
                "model": row["model"],
            }
        )
        return payload

    def list_tasks(self, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT task_id, filename, created_at, model, total FROM tasks"
                " ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
