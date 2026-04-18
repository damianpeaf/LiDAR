from __future__ import annotations

import asyncio
import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ValidationRun:
    def __init__(self, base_dir: Path, snapshot_interval_seconds: int = 5) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.started_at = self._now_iso()
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.run_dir = self.base_dir / f"run_{self.run_id}_pid{os.getpid()}"
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_path = self.run_dir / "metadata.json"
        self.snapshots_path = self.run_dir / "snapshots.jsonl"
        self.events_path = self.run_dir / "events.jsonl"
        self.summary_path = self.run_dir / "summary.json"
        self.snapshot_interval_seconds = snapshot_interval_seconds

        self.metrics: dict[str, Any] = {
            "messages_text": 0,
            "messages_binary": 0,
            "parse_failures": 0,
            "points_parsed": 0,
            "points_processed": 0,
            "points_stored": 0,
            "clients_connected": 0,
            "clients_disconnected": 0,
            "web_clients_registered": 0,
            "active_clients": 0,
            "active_web_clients": 0,
            "unknown_messages": 0,
            "redis_store_failures": 0,
        }

        self._write_json(
            self.metadata_path,
            {
                "run_id": self.run_id,
                "started_at": self.started_at,
                "pid": os.getpid(),
                "snapshot_interval_seconds": self.snapshot_interval_seconds,
                "run_dir": str(self.run_dir),
            },
        )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def increment(self, key: str, amount: int = 1) -> None:
        self.metrics[key] = int(self.metrics.get(key, 0)) + amount

    def set_value(self, key: str, value: Any) -> None:
        self.metrics[key] = value

    def record_event(self, event: str, **data: Any) -> None:
        self._append_jsonl(
            self.events_path,
            {
                "timestamp": self._now_iso(),
                "event": event,
                **data,
            },
        )

    def snapshot(self, reason: str) -> dict[str, Any]:
        snapshot = {
            "timestamp": self._now_iso(),
            "reason": reason,
            "started_at": self.started_at,
            "metrics": deepcopy(self.metrics),
        }
        self._append_jsonl(self.snapshots_path, snapshot)
        return snapshot

    async def snapshot_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self.snapshot_interval_seconds)
                self.snapshot("periodic")
        except asyncio.CancelledError:
            raise

    async def close(self) -> None:
        ended_at = self._now_iso()
        final_snapshot = self.snapshot("final")
        self._write_json(
            self.summary_path,
            {
                "run_id": self.run_id,
                "started_at": self.started_at,
                "ended_at": ended_at,
                "metrics": deepcopy(self.metrics),
                "final_snapshot": final_snapshot,
            },
        )
