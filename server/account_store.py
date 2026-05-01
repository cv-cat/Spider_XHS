import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_STORE_PATH = ROOT_DIR / "datas" / "accounts.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def mask_cookie(cookies: str) -> str:
    if not cookies:
        return ""
    if len(cookies) <= 16:
        return "*" * len(cookies)
    return f"{cookies[:8]}...{cookies[-8:]}"


class AccountStore:
    def __init__(self, path: Path = DEFAULT_STORE_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("accounts store must be a list")
        return data

    def _write(self, accounts: list[dict[str, Any]]) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)
        tmp_path.replace(self.path)

    def list_accounts(self) -> list[dict[str, Any]]:
        return [self.to_public(account) for account in self._read()]

    def get_account(self, account_id: str) -> dict[str, Any] | None:
        return next((item for item in self._read() if item["id"] == account_id), None)

    def create_account(self, name: str, cookies: str) -> dict[str, Any]:
        now = utc_now()
        account = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "cookies": cookies.strip(),
            "created_at": now,
            "updated_at": now,
            "last_check_at": None,
            "last_check_status": None,
        }
        accounts = self._read()
        accounts.append(account)
        self._write(accounts)
        return self.to_public(account)

    def delete_account(self, account_id: str) -> bool:
        accounts = self._read()
        next_accounts = [item for item in accounts if item["id"] != account_id]
        if len(next_accounts) == len(accounts):
            return False
        self._write(next_accounts)
        return True

    def update_check_status(self, account_id: str, status: str) -> dict[str, Any] | None:
        accounts = self._read()
        for account in accounts:
            if account["id"] == account_id:
                account["last_check_at"] = utc_now()
                account["last_check_status"] = status
                account["updated_at"] = utc_now()
                self._write(accounts)
                return self.to_public(account)
        return None

    @staticmethod
    def to_public(account: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": account["id"],
            "name": account["name"],
            "cookie_preview": mask_cookie(account.get("cookies", "")),
            "created_at": account.get("created_at"),
            "updated_at": account.get("updated_at"),
            "last_check_at": account.get("last_check_at"),
            "last_check_status": account.get("last_check_status"),
        }
