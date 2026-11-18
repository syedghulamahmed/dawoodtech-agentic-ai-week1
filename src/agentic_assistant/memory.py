"""Per-user persistent SQLite memory and narrow tool contracts."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, ValidationError

class SaveMemoryArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    key: str = Field(min_length=1, max_length=80, description="Short key for this user memory.")
    value: str = Field(min_length=1, max_length=1200, description="Concise fact or preference to remember.")

class SearchMemoryArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=160, description="Words describing the memory to find.")

class ForgetMemoryArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    key: str = Field(min_length=1, max_length=80, description="Exact key to delete for this user.")

class UserMemoryStore:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS user_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                memory_key TEXT NOT NULL, memory_value TEXT NOT NULL, updated_at TEXT NOT NULL,
                UNIQUE(user_id, memory_key))""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_memory_user_updated ON user_memories(user_id, updated_at DESC)")

    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        user = user_id.strip()
        if not user or len(user) > 80:
            raise ValueError("user_id must contain 1 to 80 characters.")
        return user

    def _connect(self):
        db = sqlite3.connect(self.database_path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def save(self, user_id: str, key: str, value: str) -> dict[str, Any]:
        user = self._validate_user_id(user_id)
        key, value = key.strip(), value.strip()
        if not key or len(key) > 80 or not value or len(value) > 1200:
            raise ValueError("Memory key/value is empty or exceeds its length limit.")
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as db:
            db.execute("""INSERT INTO user_memories(user_id,memory_key,memory_value,updated_at)
                VALUES(?,?,?,?) ON CONFLICT(user_id,memory_key) DO UPDATE SET
                memory_value=excluded.memory_value, updated_at=excluded.updated_at""",
                (user, key, value, now))
        return {"saved": True, "key": key, "updated_at": now}

    def load_for_user(self, user_id: str, limit: int = 20) -> list[dict[str, str]]:
        user = self._validate_user_id(user_id)
        with self._connect() as db:
            rows = db.execute("""SELECT memory_key,memory_value,updated_at FROM user_memories
                WHERE user_id=? ORDER BY updated_at DESC,id DESC LIMIT ?""",
                (user, max(1, min(int(limit), 50)))).fetchall()
        return [dict(row) for row in rows]

    def search(self, user_id: str, query: str, limit: int = 5) -> dict[str, Any]:
        user = self._validate_user_id(user_id)
        terms = query.strip().split()
        if not terms:
            raise ValueError("Memory search query cannot be empty.")
        conditions = " OR ".join("(memory_key LIKE ? OR memory_value LIKE ?)" for _ in terms)
        params = []
        for term in terms:
            safe = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            params.extend((f"%{safe}%", f"%{safe}%"))
        params.append(max(1, min(int(limit), 10)))
        with self._connect() as db:
            rows = db.execute(
                f"SELECT memory_key,memory_value,updated_at FROM user_memories WHERE user_id=? AND ({conditions}) ORDER BY updated_at DESC LIMIT ?",
                [user, *params],
            ).fetchall()
        return {"count": len(rows), "memories": [dict(row) for row in rows]}

    def forget(self, user_id: str, key: str) -> dict[str, Any]:
        user = self._validate_user_id(user_id)
        with self._connect() as db:
            cursor = db.execute("DELETE FROM user_memories WHERE user_id=? AND memory_key=?", (user, key.strip()))
        return {"deleted": cursor.rowcount > 0, "key": key.strip()}

    def tool_schemas(self) -> list[dict[str, Any]]:
        definitions = [
            ("save_memory", "Save/update a concise fact or preference only when the user explicitly asks you to remember it.", SaveMemoryArgs),
            ("search_memory", "Search this user's saved memories; returns at most five short matches.", SearchMemoryArgs),
            ("forget_memory", "Delete one exact memory key for the current user when explicitly requested.", ForgetMemoryArgs),
        ]
        output = []
        for name, description, model in definitions:
            schema = model.model_json_schema()
            schema.pop("title", None)
            output.append({"type": "function", "function": {"name": name, "description": description, "parameters": schema}})
        return output

    def execute_tool(self, user_id: str, name: str, raw_arguments: str) -> dict[str, Any]:
        models = {"save_memory": SaveMemoryArgs, "search_memory": SearchMemoryArgs, "forget_memory": ForgetMemoryArgs}
        model = models.get(name)
        if model is None:
            return {"error": "Unknown memory tool", "tool": name}
        try:
            args = model.model_validate_json(raw_arguments)
            values = args.model_dump()
            if name == "save_memory":
                return self.save(user_id, **values)
            if name == "search_memory":
                return self.search(user_id, **values)
            return self.forget(user_id, **values)
        except ValidationError as exc:
            return {"error": "Invalid tool arguments", "details": exc.errors(include_url=False)}
        except (TypeError, ValueError) as exc:
            return {"error": type(exc).__name__, "message": str(exc)}
