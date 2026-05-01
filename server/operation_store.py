import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_STORE_PATH = ROOT_DIR / "datas" / "operations.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OperationStore:
    def __init__(self, path: Path = DEFAULT_STORE_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _empty(self) -> dict[str, Any]:
        return {
            "publish_tasks": [],
            "search_monitors": [],
            "search_results": [],
            "analytics_snapshots": [],
            "logs": [],
        }

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("operations store must be an object")
        merged = self._empty()
        merged.update(data)
        return merged

    def _write(self, data: dict[str, Any]) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp_path.replace(self.path)

    def log(self, event_type: str, message: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = self._read()
        item = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "message": message,
            "payload": payload or {},
            "created_at": utc_now(),
        }
        data["logs"].insert(0, item)
        data["logs"] = data["logs"][:200]
        self._write(data)
        return item

    def summary(self) -> dict[str, Any]:
        data = self._read()
        publish_tasks = data["publish_tasks"]
        monitors = data["search_monitors"]
        snapshots = data["analytics_snapshots"]
        return {
            "publish_total": len(publish_tasks),
            "publish_pending": len([item for item in publish_tasks if item.get("status") in {"draft", "pending"}]),
            "publish_done": len([item for item in publish_tasks if item.get("status") == "published"]),
            "publish_failed": len([item for item in publish_tasks if item.get("status") == "failed"]),
            "monitor_total": len(monitors),
            "monitor_enabled": len([item for item in monitors if item.get("enabled", True)]),
            "search_result_total": len(data["search_results"]),
            "analytics_snapshot_total": len(snapshots),
            "latest_logs": data["logs"][:20],
        }

    def list_publish_tasks(self) -> list[dict[str, Any]]:
        return self._read()["publish_tasks"]

    def create_publish_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        now = utc_now()
        item = {
            "id": str(uuid.uuid4()),
            "account_id": payload["account_id"],
            "title": payload["title"].strip(),
            "desc": payload.get("desc", ""),
            "topics": payload.get("topics", []),
            "location": payload.get("location", ""),
            "privacy_type": payload.get("privacy_type", 1),
            "media_type": payload.get("media_type", "image"),
            "media_names": payload.get("media_names", []),
            "scheduled_date": payload.get("scheduled_date") or "",
            "status": payload.get("status") or "pending",
            "last_error": "",
            "publish_response": None,
            "created_at": now,
            "updated_at": now,
        }
        data["publish_tasks"].insert(0, item)
        data["logs"].insert(0, {
            "id": str(uuid.uuid4()),
            "event_type": "publish_task_created",
            "message": f"创建发布任务：{item['title']}",
            "payload": {"task_id": item["id"]},
            "created_at": now,
        })
        self._write(data)
        return item

    def update_publish_task_status(
        self,
        task_id: str,
        status: str,
        last_error: str = "",
        publish_response: Any = None,
    ) -> dict[str, Any] | None:
        data = self._read()
        now = utc_now()
        for item in data["publish_tasks"]:
            if item["id"] == task_id:
                item["status"] = status
                item["last_error"] = last_error
                if publish_response is not None:
                    item["publish_response"] = publish_response
                item["updated_at"] = now
                data["logs"].insert(0, {
                    "id": str(uuid.uuid4()),
                    "event_type": "publish_task_status",
                    "message": f"发布任务状态更新为 {status}",
                    "payload": {"task_id": task_id, "error": last_error},
                    "created_at": now,
                })
                self._write(data)
                return item
        return None

    def delete_publish_task(self, task_id: str) -> bool:
        data = self._read()
        before = len(data["publish_tasks"])
        data["publish_tasks"] = [item for item in data["publish_tasks"] if item["id"] != task_id]
        if len(data["publish_tasks"]) == before:
            return False
        self._write(data)
        return True

    def list_search_monitors(self) -> list[dict[str, Any]]:
        return self._read()["search_monitors"]

    def create_search_monitor(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        now = utc_now()
        item = {
            "id": str(uuid.uuid4()),
            "account_id": payload["account_id"],
            "keyword": payload["keyword"].strip(),
            "require_num": payload.get("require_num", 10),
            "sort_type_choice": payload.get("sort_type_choice", 0),
            "note_type": payload.get("note_type", 0),
            "note_time": payload.get("note_time", 0),
            "interval_minutes": payload.get("interval_minutes", 60),
            "enabled": payload.get("enabled", True),
            "last_run_at": None,
            "last_run_status": "",
            "last_run_message": "",
            "created_at": now,
            "updated_at": now,
        }
        data["search_monitors"].insert(0, item)
        self._write(data)
        return item

    def delete_search_monitor(self, monitor_id: str) -> bool:
        data = self._read()
        before = len(data["search_monitors"])
        data["search_monitors"] = [item for item in data["search_monitors"] if item["id"] != monitor_id]
        if len(data["search_monitors"]) == before:
            return False
        self._write(data)
        return True

    def get_search_monitor(self, monitor_id: str) -> dict[str, Any] | None:
        return next((item for item in self._read()["search_monitors"] if item["id"] == monitor_id), None)

    def update_search_monitor_run(self, monitor_id: str, status: str, message: str) -> dict[str, Any] | None:
        data = self._read()
        now = utc_now()
        for item in data["search_monitors"]:
            if item["id"] == monitor_id:
                item["last_run_at"] = now
                item["last_run_status"] = status
                item["last_run_message"] = message
                item["updated_at"] = now
                self._write(data)
                return item
        return None

    def save_search_results(self, monitor_id: str, keyword: str, notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        data = self._read()
        now = utc_now()
        existing_keys = {
            (item.get("monitor_id"), item.get("note_id"), item.get("xsec_token"))
            for item in data["search_results"]
        }
        saved = []
        for note in notes:
            key = (monitor_id, note.get("note_id"), note.get("xsec_token"))
            if key in existing_keys:
                continue
            item = {
                "id": str(uuid.uuid4()),
                "monitor_id": monitor_id,
                "keyword": keyword,
                "note": note,
                "status": "new",
                "created_at": now,
            }
            data["search_results"].insert(0, item)
            saved.append(item)
        data["search_results"] = data["search_results"][:1000]
        self._write(data)
        return saved

    def list_search_results(self, monitor_id: str | None = None) -> list[dict[str, Any]]:
        results = self._read()["search_results"]
        if monitor_id:
            return [item for item in results if item.get("monitor_id") == monitor_id]
        return results

    def save_analytics_snapshot(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        item = {
            "id": str(uuid.uuid4()),
            "account_id": payload["account_id"],
            "profile": payload.get("profile", {}),
            "recent_notes": payload.get("recent_notes", []),
            "created_at": utc_now(),
        }
        data["analytics_snapshots"].insert(0, item)
        data["analytics_snapshots"] = data["analytics_snapshots"][:300]
        self._write(data)
        return item

    def list_analytics_snapshots(self, account_id: str | None = None) -> list[dict[str, Any]]:
        snapshots = self._read()["analytics_snapshots"]
        if account_id:
            return [item for item in snapshots if item.get("account_id") == account_id]
        return snapshots
