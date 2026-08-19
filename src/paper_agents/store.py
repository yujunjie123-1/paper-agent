from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import RunState, WorkflowEvent


class SQLiteRunStore:
    """Small durable event/checkpoint store for the runnable MVP."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_run
                    ON events(run_id, sequence);
                """
            )

    def save(self, state: RunState) -> None:
        state_json = state.model_dump_json()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO runs(run_id, state_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    state_json = excluded.state_json,
                    updated_at = excluded.updated_at
                """,
                (state.run_id, state_json, state.updated_at.isoformat()),
            )

    def append_event(self, run_id: str, event: WorkflowEvent) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO events(run_id, event_type, event_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    run_id,
                    event.event_type,
                    event.model_dump_json(),
                    event.created_at.isoformat(),
                ),
            )

    def load(self, run_id: str) -> RunState | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state_json FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        return RunState.model_validate_json(row["state_json"]) if row else None

    def list_events(self, run_id: str) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT sequence, event_json FROM events WHERE run_id = ? ORDER BY sequence",
                (run_id,),
            ).fetchall()
        return [
            {"sequence": row["sequence"], **json.loads(row["event_json"])} for row in rows
        ]

