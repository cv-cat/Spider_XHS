from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.account_store import AccountStore
from server.operation_store import OperationStore
from server import main


class FakeResponse:
    ok = True
    status_code = 200
    text = ""

    def json(self):
        return {
            "success": True,
            "data": {
                "id": "qr-1",
                "url": "https://www.myaibot.vip/rednote/publish/qr-1",
                "qrcode": "data:image/png;base64,abc",
            },
        }


class FakePcLoginApi:
    @staticmethod
    def cookies_to_str(cookies):
        return "; ".join(f"{key}={value}" for key, value in cookies.items())

    def generate_init_cookies(self):
        return {"a1": "pc-a1"}

    def generate_qrcode(self, cookies):
        return True, "成功", {
            "cookies": cookies,
            "qr_id": "pc-qr",
            "code": "pc-code",
            "qr_url": "https://login.example/pc",
        }

    def check_qrcode_status(self, qr_id, code, cookies):
        assert qr_id == "pc-qr"
        assert code == "pc-code"
        cookies["web_session"] = "pc-session"
        return True, "验证成功", cookies

    def get_user_info(self, cookies):
        return True, {"nickname": "pc-name", "red_id": "red-2"}, cookies


class FakePcApi:
    def get_user_self_info2(self, cookies):
        return True, "ok", {"data": {"basic_info": {"nickname": "cookie-name"}}}


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    account_store = AccountStore(tmp_path / "accounts.json")
    operation_store = OperationStore(tmp_path / "operations.json")
    monkeypatch.setattr(main, "store", account_store)
    monkeypatch.setattr(main, "ops_store", operation_store)
    monkeypatch.setattr(main, "login_sessions", main.LoginSessionStore())
    main.risk_guard._cookie_cache.clear()
    main.risk_guard._last_request_at.clear()
    main.risk_guard._failure_count.clear()
    main.risk_guard._cooldown_until.clear()
    return TestClient(main.app)


def create_account(client: TestClient) -> str:
    response = client.post(
        "/api/accounts",
        json={"name": "brand", "cookies": "a" * 32},
    )
    assert response.status_code == 200
    return response.json()["account"]["id"]


def test_health(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_account_cookie_is_masked(client: TestClient):
    account_id = create_account(client)
    response = client.get("/api/accounts")
    account = response.json()["accounts"][0]
    assert account["id"] == account_id
    assert "cookies" not in account
    assert "..." in account["cookie_preview"]


def test_manual_cookie_name_can_be_resolved(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(main, "pc_api", FakePcApi())
    response = client.post("/api/accounts", json={"name": "", "cookies": "a" * 32})
    assert response.status_code == 200
    body = response.json()
    assert body["account"]["name"] == "cookie-name"
    assert body["name_source"] == "pc"
    assert "cookies" not in body["account"]


def test_pc_qrcode_login_uses_code_and_saves_account(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(main, "pc_login_api", FakePcLoginApi())
    response = client.post("/api/login/qrcode", json={"platform": "pc"})
    assert response.status_code == 200
    qr_data = response.json()

    response = client.post(
        f"/api/login/qrcode/{qr_data['session_id']}/check",
        json={"account_name": "pc custom", "save_account": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["account"]["name"] == "pc custom"
    assert body["account"]["last_check_status"] == "valid"


def test_qrcode_login_rejects_creator_platform(client: TestClient):
    response = client.post("/api/login/qrcode", json={"platform": "creator"})
    assert response.status_code == 422


def test_publish_history_crud(client: TestClient):
    account_id = create_account(client)
    response = client.post(
        "/api/publish-tasks",
        json={
            "account_id": account_id,
            "title": "Task",
            "desc": "Body",
            "topics": ["tag"],
            "media_type": "image",
            "media_names": ["a.jpg"],
        },
    )
    assert response.status_code == 200
    task_id = response.json()["task"]["id"]

    response = client.get("/api/publish-tasks")
    assert len(response.json()["tasks"]) == 1
    response = client.get("/api/publish-history")
    assert len(response.json()["items"]) == 1

    response = client.delete(f"/api/publish-tasks/{task_id}")
    assert response.status_code == 200
    assert client.get("/api/publish-tasks").json()["tasks"] == []


def test_search_monitor_crud(client: TestClient):
    account_id = create_account(client)
    response = client.post(
        "/api/search-monitors",
        json={"account_id": account_id, "keyword": "新加坡 qt", "require_num": 10},
    )
    assert response.status_code == 200
    monitor_id = response.json()["monitor"]["id"]

    response = client.get("/api/search-monitors")
    assert response.json()["monitors"][0]["keyword"] == "新加坡 qt"

    response = client.delete(f"/api/search-monitors/{monitor_id}")
    assert response.status_code == 200


def test_search_monitor_rejects_too_short_interval(client: TestClient):
    account_id = create_account(client)
    response = client.post(
        "/api/search-monitors",
        json={"account_id": account_id, "keyword": "新加坡 qt", "require_num": 10, "interval_minutes": 2},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["loc"][-1] == "interval_minutes"


def test_search_results_are_deduped_by_note_id(tmp_path: Path):
    operation_store = OperationStore(tmp_path / "operations.json")
    note = {
        "note_id": "note-1",
        "note_url": "https://www.xiaohongshu.com/explore/note-1?xsec_token=a",
        "xsec_token": "a",
        "title": "Title",
    }
    duplicate = {
        **note,
        "note_url": "https://www.xiaohongshu.com/explore/note-1?xsec_token=b",
        "xsec_token": "b",
    }

    saved = operation_store.save_search_results("monitor-1", "新加坡 qt", [note, duplicate])
    assert len(saved) == 1
    saved_again = operation_store.save_search_results("monitor-1", "新加坡 qt", [duplicate])
    assert saved_again == []
    assert len(operation_store.list_search_results("monitor-1")) == 1


def test_invalid_empty_search_note_is_filtered():
    invalid = {
        "note_id": "bad-note",
        "note_url": "https://www.xiaohongshu.com/explore/bad-note",
        "title": "无标题",
        "nickname": "",
        "cover": "",
    }
    valid = {
        "note_id": "good-note",
        "note_url": "https://www.xiaohongshu.com/explore/good-note",
        "title": "真实标题",
        "nickname": "",
        "cover": "",
    }
    assert main.is_useful_note(invalid) is False
    assert main.is_useful_note(valid) is True


def test_external_publish_config_masks_api_key(client: TestClient):
    response = client.post(
        "/api/external-publish/config",
        json={"api_key": "sk_test_1234567890"},
    )
    assert response.status_code == 200
    config = response.json()["config"]
    assert config["has_api_key"] is True
    assert config["api_key"] == ""
    assert config["api_key_preview"].startswith("sk_t")


def test_external_publish_validation_requires_media(client: TestClient):
    client.post("/api/external-publish/config", json={"api_key": "sk_test_1234567890"})
    response = client.post(
        "/api/external-publish/qrcode",
        json={"type": "normal", "title": "No image", "content": "Body", "images": []},
    )
    assert response.status_code == 400
    assert "图片" in response.json()["detail"]


def test_external_publish_qrcode_uses_mocked_provider(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    account_id = create_account(client)
    client.post("/api/external-publish/config", json={"api_key": "sk_test_1234567890"})
    monkeypatch.setattr(main.requests, "post", lambda *args, **kwargs: FakeResponse())

    response = client.post(
        "/api/external-publish/qrcode",
        json={
            "account_id": account_id,
            "type": "normal",
            "title": "Title",
            "content": "Body #tag",
            "images": ["https://example.com/a.jpg"],
        },
    )
    assert response.status_code == 200
    assert response.json()["result"]["qrcode"].startswith("data:image/png")
    records = client.get("/api/external-publish/records").json()["records"]
    assert len(records) == 1
    tasks = client.get("/api/publish-tasks").json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["status"] == "published"
    assert tasks[0]["topics"] == ["tag"]
    assert tasks[0]["media_names"] == ["https://example.com/a.jpg"]
