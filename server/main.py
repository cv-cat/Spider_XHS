import json
import os
import random
import re
import threading
import time
from pathlib import Path
from typing import Annotated
from urllib.parse import urlencode, urlparse

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import requests

from apis.xhs_creator_apis import XHS_Creator_Apis
from apis.xhs_pc_apis import XHS_Apis
from server.account_store import AccountStore
from server.operation_store import OperationStore
from xhs_utils.data_util import handle_note_info
from xhs_utils.http_util import REQUEST_TIMEOUT
from xhs_utils.cookie_util import trans_cookies


def disable_proxy_for_xhs() -> None:
    if os.getenv("XHS_USE_PROXY", "").lower() in {"1", "true", "yes"}:
        return
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        os.environ.pop(key, None)
    no_proxy_hosts = [
        "creator.xiaohongshu.com",
        "edith.xiaohongshu.com",
        "www.xiaohongshu.com",
        "ros-upload.xiaohongshu.com",
        "as.xiaohongshu.com",
        ".xiaohongshu.com",
        ".xhscdn.com",
    ]
    current_no_proxy = os.getenv("NO_PROXY") or os.getenv("no_proxy") or ""
    merged_hosts = [host for host in current_no_proxy.split(",") if host.strip()]
    for host in no_proxy_hosts:
        if host not in merged_hosts:
            merged_hosts.append(host)
    no_proxy = ",".join(merged_hosts)
    os.environ["NO_PROXY"] = no_proxy
    os.environ["no_proxy"] = no_proxy


disable_proxy_for_xhs()

app = FastAPI(title="Spider XHS Web Publisher")
store = AccountStore()
ops_store = OperationStore()
creator_api = XHS_Creator_Apis()
pc_api = XHS_Apis()

COOKIE_CHECK_TTL_SECONDS = 600
REQUEST_INTERVAL_RANGE_SECONDS = (2.0, 6.0)
FAILURE_COOLDOWN_THRESHOLD = 3
FAILURE_COOLDOWN_SECONDS = 300


class RiskGuard:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_request_at: dict[str, float] = {}
        self._failure_count: dict[str, int] = {}
        self._cooldown_until: dict[str, float] = {}
        self._cookie_cache: dict[str, tuple[float, bool, str]] = {}

    def before_request(self, account_id: str) -> None:
        now = time.time()
        with self._lock:
            cooldown_until = self._cooldown_until.get(account_id, 0)
            if cooldown_until > now:
                remaining = int(cooldown_until - now)
                raise HTTPException(status_code=429, detail=f"账号请求已冷却，请 {remaining} 秒后重试")

            last_request_at = self._last_request_at.get(account_id)
            delay = 0.0
            if last_request_at is not None:
                next_request_at = last_request_at + random.uniform(*REQUEST_INTERVAL_RANGE_SECONDS)
                delay = max(0.0, next_request_at - now)
            self._last_request_at[account_id] = now + delay

        if delay > 0:
            time.sleep(delay)

    def record_result(self, account_id: str, success: bool, msg: str = "") -> None:
        with self._lock:
            if success:
                self._failure_count[account_id] = 0
                return
            failures = self._failure_count.get(account_id, 0) + 1
            self._failure_count[account_id] = failures
            if failures >= FAILURE_COOLDOWN_THRESHOLD:
                self._cooldown_until[account_id] = time.time() + FAILURE_COOLDOWN_SECONDS

    def get_cookie_cache(self, account_id: str) -> tuple[bool, str] | None:
        cached = self._cookie_cache.get(account_id)
        if not cached:
            return None
        checked_at, is_valid, msg = cached
        if time.time() - checked_at > COOKIE_CHECK_TTL_SECONDS:
            return None
        return is_valid, msg

    def set_cookie_cache(self, account_id: str, is_valid: bool, msg: str) -> None:
        self._cookie_cache[account_id] = (time.time(), is_valid, msg)

    def clear_cookie_cache(self, account_id: str) -> None:
        self._cookie_cache.pop(account_id, None)


risk_guard = RiskGuard()
ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    cookies: str = Field(min_length=20)


class TopicSearchRequest(BaseModel):
    account_id: str
    keyword: str = Field(min_length=1, max_length=80)


class AccountRequest(BaseModel):
    account_id: str


class ProfileQueryRequest(BaseModel):
    account_id: str
    user_url_or_id: str = Field(min_length=1, max_length=300)


class SearchNotesRequest(BaseModel):
    account_id: str
    query: str = Field(min_length=1, max_length=80)
    require_num: int = Field(default=10, ge=1, le=100)
    sort_type_choice: int = Field(default=0, ge=0, le=4)
    note_type: int = Field(default=0, ge=0, le=2)
    note_time: int = Field(default=0, ge=0, le=3)


class NoteDetailRequest(BaseModel):
    account_id: str
    note_url: str = Field(min_length=20, max_length=500)
    note_id: str = Field(default="", max_length=80)
    xsec_token: str = Field(default="", max_length=300)
    xsec_source: str = Field(default="pc_search", max_length=80)


class ProfileNotesRequest(BaseModel):
    account_id: str
    user_id: str = Field(min_length=1, max_length=80)
    cursor: str = Field(default="", max_length=200)
    xsec_token: str = Field(default="", max_length=300)
    xsec_source: str = Field(default="pc_user", max_length=80)


class PublishTaskCreate(BaseModel):
    account_id: str
    title: str = Field(min_length=1, max_length=60)
    desc: str = ""
    topics: list[str] = []
    location: str = ""
    privacy_type: int = Field(default=1, ge=0, le=1)
    media_type: str = Field(default="image")
    media_names: list[str] = []
    scheduled_date: str = ""
    status: str = Field(default="pending")


class TaskStatusUpdate(BaseModel):
    status: str = Field(pattern="^(draft|pending|published|failed|cancelled)$")
    last_error: str = ""


class SearchMonitorCreate(BaseModel):
    account_id: str
    keyword: str = Field(min_length=1, max_length=80)
    require_num: int = Field(default=10, ge=1, le=50)
    sort_type_choice: int = Field(default=0, ge=0, le=4)
    note_type: int = Field(default=0, ge=0, le=2)
    note_time: int = Field(default=0, ge=0, le=3)
    interval_minutes: int = Field(default=60, ge=5, le=1440)
    enabled: bool = True


class ExternalPublishConfigRequest(BaseModel):
    api_key: str = Field(default="", max_length=500)
    base_url: str = Field(default="https://www.myaibot.vip", max_length=200)
    endpoint: str = Field(default="/api/rednote/publish-with-upload", max_length=120)


class ExternalPublishRequest(BaseModel):
    account_id: str = ""
    type: str = Field(pattern="^(normal|video)$")
    title: str = Field(default="", max_length=40)
    content: str = Field(default="", max_length=1000)
    images: list[str] = []
    video: str = ""
    cover: str = ""
    use_upload_endpoint: bool = True


def require_account(account_id: str) -> dict:
    account = store.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return account


def require_valid_account(account_id: str) -> dict:
    account = require_account(account_id)
    cached = risk_guard.get_cookie_cache(account_id)
    if cached:
        cookie_ok, cookie_msg = cached
    else:
        cookie_ok, cookie_msg, _ = check_creator_cookie(account_id)
    if not cookie_ok:
        raise HTTPException(status_code=400, detail=f"Cookie 不可用: {cookie_msg}")
    return account


def guarded_xhs_call(account_id: str, func, *args, **kwargs):
    risk_guard.before_request(account_id)
    try:
        result = func(*args, **kwargs)
    except Exception:
        risk_guard.record_result(account_id, False)
        raise
    success = bool(result[0]) if isinstance(result, tuple) and result else True
    msg = str(result[1]) if isinstance(result, tuple) and len(result) > 1 else ""
    risk_guard.record_result(account_id, success, msg)
    return result


def check_creator_cookie(account_id: str, force: bool = False) -> tuple[bool, str, dict | None]:
    account = require_account(account_id)
    if not force:
        cached = risk_guard.get_cookie_cache(account_id)
        if cached:
            is_valid, msg = cached
            return is_valid, msg, None
    try:
        success, msg, res_json = guarded_xhs_call(
            account_id,
            creator_api.get_publish_note_info,
            None,
            account["cookies"],
        )
    except Exception as exc:
        success, msg, res_json = False, str(exc), None

    data = res_json.get("data") if isinstance(res_json, dict) else None
    is_valid = bool(success and isinstance(data, dict) and "notes" in data)
    status = "valid" if is_valid else "invalid"
    store.update_check_status(account_id, status)
    if not is_valid and not msg:
        msg = "Cookie 无效或登录状态异常"
    final_msg = msg or "Cookie 可用"
    risk_guard.set_cookie_cache(account_id, is_valid, final_msg)
    return is_valid, final_msg, res_json


def parse_topics(raw_topics: str) -> list[str]:
    if not raw_topics.strip():
        return []
    try:
        parsed = json.loads(raw_topics)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="topics 必须是 JSON 字符串数组") from exc
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise HTTPException(status_code=400, detail="topics 必须是 JSON 字符串数组")
    return [item.strip() for item in parsed if item.strip()]


def extract_topics_from_text(value: str) -> list[str]:
    topics = re.findall(r"#([^#\s，,。.！!？?\n\r]+)", value or "")
    return list(dict.fromkeys(item.strip() for item in topics if item.strip()))


def parse_user_id(value: str) -> str:
    value = value.strip()
    if not value:
        raise HTTPException(status_code=400, detail="用户主页链接或 user_id 不能为空")
    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 3 and parts[0] == "user" and parts[1] == "profile":
            return parts[2]
        raise HTTPException(status_code=400, detail="无法从主页链接解析 user_id")
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", value):
        raise HTTPException(status_code=400, detail="user_id 格式不正确")
    return value


def normalize_gender(value: object) -> str:
    if value == 0 or value == "0" or value == "male":
        return "男"
    if value == 1 or value == "1" or value == "female":
        return "女"
    if isinstance(value, str) and value:
        return value
    return "未知"


def pick_count(interactions: list, index: int) -> str | int:
    try:
        item = interactions[index]
        if isinstance(item, dict):
            return item.get("count", "")
    except (IndexError, TypeError):
        pass
    return ""


def normalize_profile(data: dict, fallback_user_id: str | None = None) -> dict:
    basic = data.get("basic_info") or data.get("basicInfo") or data
    interactions = data.get("interactions") or []
    user_id = (
        fallback_user_id
        or basic.get("user_id")
        or basic.get("userId")
        or data.get("user_id")
        or data.get("userId")
        or ""
    )
    tags = []
    for tag in data.get("tags") or basic.get("tags") or []:
        if isinstance(tag, dict) and tag.get("name"):
            tags.append(tag["name"])
        elif isinstance(tag, str):
            tags.append(tag)
    return {
        "user_id": user_id,
        "home_url": f"https://www.xiaohongshu.com/user/profile/{user_id}" if user_id else "",
        "nickname": basic.get("nickname") or basic.get("nickName") or basic.get("userName") or "",
        "avatar": basic.get("imageb") or basic.get("avatar") or basic.get("image") or "",
        "red_id": basic.get("red_id") or basic.get("redId") or "",
        "gender": normalize_gender(basic.get("gender")),
        "ip_location": basic.get("ip_location") or basic.get("ipLocation") or "",
        "desc": basic.get("desc") or basic.get("description") or "",
        "follows": pick_count(interactions, 0),
        "fans": pick_count(interactions, 1),
        "interaction": pick_count(interactions, 2),
        "tags": tags,
    }


def normalize_media_url(url: str | None) -> str:
    if not url:
        return ""
    if url.startswith("http://"):
        return "https://" + url[len("http://"):]
    return url


def build_note_url(note_id: str, xsec_token: str = "", xsec_source: str = "pc_search") -> str:
    if not note_id:
        return ""
    params = {}
    if xsec_token:
        params["xsec_token"] = xsec_token
    if xsec_source:
        params["xsec_source"] = xsec_source
    query = urlencode(params)
    suffix = f"?{query}" if query else ""
    return f"https://www.xiaohongshu.com/explore/{note_id}{suffix}"


def normalize_search_note(item: dict) -> dict:
    note_card = item.get("note_card") or item.get("noteCard") or {}
    note_id = item.get("id") or item.get("note_id") or item.get("noteId") or note_card.get("note_id") or ""
    user = note_card.get("user") or item.get("user") or {}
    interact = note_card.get("interact_info") or note_card.get("interactInfo") or {}
    image_list = note_card.get("image_list") or note_card.get("imageList") or []
    cover_info = note_card.get("cover") or {}
    cover = cover_info.get("url_pre") or cover_info.get("url_default") or cover_info.get("url") or ""
    if image_list:
        first_image = image_list[0]
        if isinstance(first_image, dict):
            cover = first_image.get("url") or first_image.get("traceId") or cover
            info_list = first_image.get("info_list") or first_image.get("infoList") or []
            if info_list and isinstance(info_list[-1], dict):
                cover = info_list[-1].get("url") or cover
    xsec_token = item.get("xsec_token") or item.get("xsecToken") or ""
    xsec_source = item.get("xsec_source") or item.get("xsecSource") or "pc_search"
    note_type = note_card.get("type") or item.get("note_type") or item.get("noteType") or ""
    return {
        "note_id": note_id,
        "note_url": build_note_url(note_id, xsec_token, xsec_source),
        "title": note_card.get("display_title") or note_card.get("title") or item.get("title") or "无标题",
        "desc": note_card.get("desc") or "",
        "cover": normalize_media_url(cover),
        "note_type": "图文" if note_type == "normal" else ("视频" if note_type else ""),
        "user_id": user.get("user_id") or user.get("userId") or "",
        "nickname": user.get("nickname") or user.get("nickName") or "",
        "liked_count": interact.get("liked_count") or interact.get("likedCount") or "",
        "collected_count": interact.get("collected_count") or interact.get("collectedCount") or "",
        "comment_count": interact.get("comment_count") or interact.get("commentCount") or "",
        "xsec_token": xsec_token,
        "xsec_source": xsec_source,
        "image_list": [],
        "video_addr": "",
        "upload_time": "",
    }


def note_dedupe_key(note: dict) -> str:
    return str(note.get("note_id") or note.get("note_url") or "").strip()


def is_useful_note(note: dict) -> bool:
    if not note_dedupe_key(note):
        return False
    title = str(note.get("title") or "").strip()
    nickname = str(note.get("nickname") or "").strip()
    cover = str(note.get("cover") or "").strip()
    if title == "无标题" and not nickname and not cover:
        return False
    return True


def dedupe_notes(notes: list[dict]) -> list[dict]:
    seen = set()
    unique_notes = []
    for note in notes:
        key = note_dedupe_key(note)
        if not key or key in seen:
            continue
        seen.add(key)
        unique_notes.append(note)
    return unique_notes


def normalize_profile_note(item: dict, xsec_source: str = "pc_user") -> dict:
    note_id = item.get("note_id") or item.get("noteId") or item.get("id") or ""
    xsec_token = item.get("xsec_token") or item.get("xsecToken") or ""
    note_type = item.get("type") or item.get("note_type") or item.get("noteType") or ""
    cover_info = item.get("cover") or {}
    cover = ""
    if isinstance(cover_info, dict):
        cover = cover_info.get("url_pre") or cover_info.get("url_default") or cover_info.get("url") or ""
    return {
        "note_id": note_id,
        "note_url": build_note_url(note_id, xsec_token, xsec_source),
        "title": item.get("display_title") or item.get("title") or "无标题",
        "desc": "",
        "cover": normalize_media_url(cover),
        "note_type": "图文" if note_type == "normal" else ("视频" if note_type else "笔记"),
        "user_id": "",
        "nickname": "",
        "liked_count": item.get("liked_count") or item.get("likedCount") or "",
        "collected_count": item.get("collected_count") or item.get("collectedCount") or "",
        "comment_count": item.get("comment_count") or item.get("commentCount") or "",
        "xsec_token": xsec_token,
        "xsec_source": xsec_source,
        "image_list": [],
        "video_addr": "",
        "upload_time": "",
    }


def enrich_search_note(item: dict, cookies_str: str) -> dict:
    note = normalize_search_note(item)
    if not note["note_url"]:
        return note
    try:
        success, _, res_json = pc_api.get_note_info(note["note_url"], cookies_str)
        items = (((res_json or {}).get("data") or {}).get("items") or [])
        if not success or not items:
            return note
        detail = items[0]
        detail["url"] = note["note_url"]
        handled = handle_note_info(detail)
        note.update(
            {
                "title": handled.get("title") or note["title"],
                "desc": handled.get("desc") or "",
                "cover": normalize_media_url(handled.get("video_cover") or note["cover"]),
                "note_type": handled.get("note_type") or note["note_type"],
                "image_list": [normalize_media_url(url) for url in handled.get("image_list", [])],
                "video_addr": normalize_media_url(handled.get("video_addr")),
                "upload_time": handled.get("upload_time") or "",
            }
        )
    except Exception:
        return note
    return note


def validate_media_url(url: str) -> str:
    media_url = normalize_media_url(url.strip())
    parsed = urlparse(media_url)
    allowed_hosts = (
        "xhscdn.com",
        "xiaohongshu.com",
    )
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(allowed_hosts):
        raise HTTPException(status_code=400, detail="不支持的媒体地址")
    return media_url


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/accounts")
def list_accounts() -> dict:
    return {"accounts": store.list_accounts()}


@app.get("/api/ops/summary")
def get_ops_summary() -> dict:
    return {"summary": ops_store.summary()}


@app.get("/api/external-publish/config")
def get_external_publish_config() -> dict:
    return {"config": ops_store.get_external_publish_config()}


@app.post("/api/external-publish/config")
def save_external_publish_config(payload: ExternalPublishConfigRequest) -> dict:
    if not payload.api_key.strip() and not ops_store.get_external_publish_config(include_secret=True).get("api_key"):
        raise HTTPException(status_code=400, detail="请填写 API Key")
    config = ops_store.save_external_publish_config(payload.model_dump())
    return {"config": config}


@app.get("/api/external-publish/records")
def list_external_publish_records() -> dict:
    return {"records": ops_store.list_external_publish_records()}


@app.post("/api/external-publish/qrcode")
def create_external_publish_qrcode(payload: ExternalPublishRequest) -> dict:
    config = ops_store.get_external_publish_config(include_secret=True)
    api_key = config.get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="请先保存 API Key")
    if payload.account_id:
        require_account(payload.account_id)
    if payload.type == "normal" and not payload.images:
        raise HTTPException(status_code=400, detail="图文笔记请至少填写一个图片 URL")
    if payload.type == "video" and not payload.video:
        raise HTTPException(status_code=400, detail="视频笔记请填写视频 URL")

    endpoint = "/api/rednote/publish-with-upload" if payload.use_upload_endpoint else config["endpoint"]
    url = f"{config['base_url'].rstrip('/')}{endpoint}"
    request_data = {
        "api_key": api_key,
        "type": payload.type,
        "title": payload.title,
        "content": payload.content,
    }
    if payload.type == "normal":
        request_data["images"] = payload.images
    else:
        request_data["video"] = payload.video
        if payload.cover:
            request_data["cover"] = payload.cover

    try:
        response = requests.post(url, json=request_data, headers={"Content-Type": "application/json"}, timeout=REQUEST_TIMEOUT)
        res_json = response.json()
    except Exception as exc:
        ops_store.log("external_publish_failed", "扫码发布接口请求失败", {"error": str(exc)})
        raise HTTPException(status_code=400, detail=f"扫码发布接口请求失败: {exc}") from exc

    safe_request = {key: value for key, value in request_data.items() if key != "api_key"}
    record = ops_store.save_external_publish_record(
        {
            "title": payload.title,
            "note_type": payload.type,
            "provider": "myaibot",
            "request": safe_request,
            "response": res_json,
        }
    )
    if not response.ok or not res_json.get("success"):
        error = res_json.get("error") if isinstance(res_json, dict) else None
        message = (error or {}).get("message") if isinstance(error, dict) else response.text
        raise HTTPException(status_code=response.status_code, detail=message or "扫码发布接口返回失败")
    task = None
    if payload.account_id:
        task = ops_store.create_publish_task(
            {
                "account_id": payload.account_id,
                "title": payload.title or "扫码发布",
                "desc": payload.content,
                "topics": extract_topics_from_text(payload.content),
                "location": "",
                "privacy_type": 0,
                "media_type": "image" if payload.type == "normal" else "video",
                "media_names": payload.images if payload.type == "normal" else [payload.video],
                "scheduled_date": "",
                "status": "published",
            }
        )
    return {"result": res_json.get("data") or {}, "record": record, "task": task}


@app.post("/api/accounts")
def create_account(payload: AccountCreate) -> dict:
    account = store.create_account(payload.name, payload.cookies)
    return {"account": account}


@app.delete("/api/accounts/{account_id}")
def delete_account(account_id: str) -> dict:
    deleted = store.delete_account(account_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="账号不存在")
    risk_guard.clear_cookie_cache(account_id)
    return {"success": True}


@app.post("/api/accounts/{account_id}/check")
def check_account(account_id: str) -> dict:
    risk_guard.clear_cookie_cache(account_id)
    success, msg, _ = check_creator_cookie(account_id, force=True)
    return {"success": success, "msg": msg}


@app.get("/api/publish-tasks")
def list_publish_tasks() -> dict:
    return {"tasks": ops_store.list_publish_tasks()}


@app.get("/api/publish-history")
def list_publish_history() -> dict:
    return {"items": ops_store.list_publish_tasks()}


@app.post("/api/publish-tasks")
def create_publish_task(payload: PublishTaskCreate) -> dict:
    require_account(payload.account_id)
    if payload.media_type not in {"image", "video"}:
        raise HTTPException(status_code=400, detail="media_type 只能是 image 或 video")
    task = ops_store.create_publish_task(payload.model_dump())
    return {"task": task}


@app.patch("/api/publish-tasks/{task_id}")
def update_publish_task(task_id: str, payload: TaskStatusUpdate) -> dict:
    task = ops_store.update_publish_task_status(task_id, payload.status, payload.last_error)
    if not task:
        raise HTTPException(status_code=404, detail="发布历史不存在")
    return {"task": task}


@app.delete("/api/publish-tasks/{task_id}")
def delete_publish_task(task_id: str) -> dict:
    if not ops_store.delete_publish_task(task_id):
        raise HTTPException(status_code=404, detail="发布历史不存在")
    return {"success": True}


@app.get("/api/search-monitors")
def list_search_monitors() -> dict:
    return {"monitors": ops_store.list_search_monitors()}


@app.post("/api/search-monitors")
def create_search_monitor(payload: SearchMonitorCreate) -> dict:
    require_account(payload.account_id)
    monitor = ops_store.create_search_monitor(payload.model_dump())
    return {"monitor": monitor}


@app.delete("/api/search-monitors/{monitor_id}")
def delete_search_monitor(monitor_id: str) -> dict:
    if not ops_store.delete_search_monitor(monitor_id):
        raise HTTPException(status_code=404, detail="监控任务不存在")
    return {"success": True}


@app.post("/api/search-monitors/{monitor_id}/run")
def run_search_monitor(monitor_id: str) -> dict:
    monitor = ops_store.get_search_monitor(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="监控任务不存在")
    account = require_valid_account(monitor["account_id"])
    success, msg, notes = guarded_xhs_call(
        monitor["account_id"],
        pc_api.search_some_note,
        monitor["keyword"],
        monitor["require_num"],
        account["cookies"],
        monitor["sort_type_choice"],
        monitor["note_type"],
        monitor["note_time"],
    )
    if not success:
        ops_store.update_search_monitor_run(monitor_id, "failed", msg)
        raise HTTPException(status_code=400, detail=msg)
    normalized = dedupe_notes([note for note in (normalize_search_note(item) for item in notes) if is_useful_note(note)])
    saved = ops_store.save_search_results(monitor_id, monitor["keyword"], normalized)
    ops_store.update_search_monitor_run(monitor_id, "success", f"新增 {len(saved)} 条，返回 {len(normalized)} 条")
    return {"notes": normalized, "saved": saved}


@app.get("/api/search-results")
def list_saved_search_results(monitor_id: str | None = None) -> dict:
    return {"results": ops_store.list_search_results(monitor_id)}


@app.get("/api/analytics/snapshots")
def list_analytics_snapshots(account_id: str | None = None) -> dict:
    return {"snapshots": ops_store.list_analytics_snapshots(account_id)}


@app.post("/api/analytics/snapshots")
def create_analytics_snapshot(payload: AccountRequest) -> dict:
    account = require_valid_account(payload.account_id)
    success, msg, res_json = guarded_xhs_call(payload.account_id, pc_api.get_user_self_info2, account["cookies"])
    if not success:
        success, msg, res_json = guarded_xhs_call(payload.account_id, pc_api.get_user_self_info, account["cookies"])
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    profile = normalize_profile((res_json or {}).get("data") or {})
    recent_notes = []
    if profile.get("user_id"):
        notes_success, _, notes_json = guarded_xhs_call(
            payload.account_id,
            pc_api.get_user_note_info,
            profile["user_id"],
            "",
            account["cookies"],
            "",
            "pc_user",
        )
        if notes_success:
            recent_notes = [
                normalize_profile_note(item, "pc_user")
                for item in (((notes_json or {}).get("data") or {}).get("notes") or [])[:10]
            ]
    snapshot = ops_store.save_analytics_snapshot(
        {"account_id": payload.account_id, "profile": profile, "recent_notes": recent_notes}
    )
    return {"snapshot": snapshot}


@app.post("/api/topics/search")
def search_topics(payload: TopicSearchRequest) -> dict:
    account = require_account(payload.account_id)
    try:
        cookies = trans_cookies(account["cookies"])
        success, msg, res_json = guarded_xhs_call(
            payload.account_id,
            creator_api.get_topic,
            payload.keyword,
            cookies,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    topics = ((res_json or {}).get("data") or {}).get("topic_info_dtos") or []
    return {
        "topics": [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "link": item.get("link"),
            }
            for item in topics
        ]
    }


@app.post("/api/profile/self")
def get_self_profile(payload: AccountRequest) -> dict:
    account = require_valid_account(payload.account_id)
    success, msg, res_json = guarded_xhs_call(payload.account_id, pc_api.get_user_self_info2, account["cookies"])
    if not success:
        success, msg, res_json = guarded_xhs_call(payload.account_id, pc_api.get_user_self_info, account["cookies"])
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    data = (res_json or {}).get("data") or {}
    return {"profile": normalize_profile(data)}


@app.post("/api/profile/query")
def query_profile(payload: ProfileQueryRequest) -> dict:
    account = require_valid_account(payload.account_id)
    user_id = parse_user_id(payload.user_url_or_id)
    success, msg, res_json = guarded_xhs_call(
        payload.account_id,
        pc_api.get_user_info,
        user_id,
        account["cookies"],
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    data = (res_json or {}).get("data") or {}
    return {"profile": normalize_profile(data, user_id)}


@app.post("/api/profile/notes")
def get_profile_notes(payload: ProfileNotesRequest) -> dict:
    account = require_valid_account(payload.account_id)
    success, msg, res_json = guarded_xhs_call(
        payload.account_id,
        pc_api.get_user_note_info,
        payload.user_id,
        payload.cursor,
        account["cookies"],
        payload.xsec_token,
        payload.xsec_source or "pc_user",
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    data = (res_json or {}).get("data") or {}
    notes = data.get("notes") or []
    return {
        "notes": [normalize_profile_note(item, payload.xsec_source or "pc_user") for item in notes],
        "cursor": str(data.get("cursor") or ""),
        "has_more": bool(data.get("has_more")),
    }


@app.post("/api/search/notes")
def search_notes(payload: SearchNotesRequest) -> dict:
    account = require_valid_account(payload.account_id)
    success, msg, notes = guarded_xhs_call(
        payload.account_id,
        pc_api.search_some_note,
        payload.query,
        payload.require_num,
        account["cookies"],
        payload.sort_type_choice,
        payload.note_type,
        payload.note_time,
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    normalized = dedupe_notes([note for note in (normalize_search_note(item) for item in notes) if is_useful_note(note)])
    return {"notes": normalized, "detail_mode": "manual"}


@app.post("/api/search/note-detail")
def get_search_note_detail(payload: NoteDetailRequest) -> dict:
    account = require_valid_account(payload.account_id)
    note_url = payload.note_url
    if payload.note_id and not note_url:
        note_url = build_note_url(payload.note_id, payload.xsec_token, payload.xsec_source or "pc_search")
    note = {
        "note_url": note_url,
        "note_id": payload.note_id,
        "xsec_token": payload.xsec_token,
        "xsec_source": payload.xsec_source or "pc_search",
    }
    try:
        success, msg, res_json = guarded_xhs_call(
            payload.account_id,
            pc_api.get_note_info,
            note_url,
            account["cookies"],
        )
        items = (((res_json or {}).get("data") or {}).get("items") or [])
        if not success or not items:
            raise HTTPException(status_code=400, detail=msg or "笔记详情获取失败")
        detail = items[0]
        detail["url"] = note_url
        handled = handle_note_info(detail)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"笔记详情获取失败: {exc}") from exc

    note.update(
        {
            "title": handled.get("title") or "无标题",
            "desc": handled.get("desc") or "",
            "cover": normalize_media_url(handled.get("video_cover")),
            "note_type": handled.get("note_type") or "",
            "user_id": handled.get("user_id") or "",
            "nickname": handled.get("nickname") or "",
            "liked_count": handled.get("liked_count") or "",
            "collected_count": handled.get("collected_count") or "",
            "comment_count": handled.get("comment_count") or "",
            "note_url": note_url,
            "image_list": [normalize_media_url(url) for url in handled.get("image_list", [])],
            "video_addr": normalize_media_url(handled.get("video_addr")),
            "upload_time": handled.get("upload_time") or "",
        }
    )
    return {"note": note}


@app.get("/api/media/proxy")
def proxy_media(url: str):
    media_url = validate_media_url(url)
    try:
        response = requests.get(
            media_url,
            headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "referer": "https://www.xiaohongshu.com/",
            },
            stream=True,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"媒体加载失败: {exc}") from exc

    def iter_content():
        try:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    yield chunk
        finally:
            response.close()

    return StreamingResponse(
        iter_content(),
        media_type=response.headers.get("content-type") or "application/octet-stream",
    )


@app.post("/api/publish")
async def publish_note(
    account_id: Annotated[str, Form()],
    title: Annotated[str, Form()],
    desc: Annotated[str, Form()] = "",
    topics: Annotated[str, Form()] = "[]",
    location: Annotated[str | None, Form()] = None,
    privacy_type: Annotated[int, Form()] = 1,
    media_type: Annotated[str, Form()] = "image",
    images: Annotated[list[UploadFile], File()] = [],
    video: Annotated[UploadFile | None, File()] = None,
) -> dict:
    account = require_valid_account(account_id)

    topic_list = parse_topics(topics)
    note_info = {
        "title": title.strip(),
        "desc": desc,
        "postTime": None,
        "location": location.strip() if location else None,
        "type": privacy_type,
        "media_type": media_type,
        "topics": topic_list,
    }

    if not note_info["title"]:
        raise HTTPException(status_code=400, detail="标题不能为空")
    if media_type == "image":
        if video is not None:
            raise HTTPException(status_code=400, detail="图文发布不能同时上传视频")
        image_bytes = [await item.read() for item in images if item.filename]
        if not image_bytes:
            raise HTTPException(status_code=400, detail="请至少上传一张图片")
        note_info["images"] = image_bytes
    elif media_type == "video":
        if images:
            raise HTTPException(status_code=400, detail="视频发布不能同时上传图片")
        if video is None:
            raise HTTPException(status_code=400, detail="请上传一个视频")
        note_info["video"] = await video.read()
    else:
        raise HTTPException(status_code=400, detail="media_type 只能是 image 或 video")

    try:
        success, msg, res_json = guarded_xhs_call(
            account_id,
            creator_api.post_note,
            note_info,
            account["cookies"],
        )
    except Exception as exc:
        ops_store.log("publish_failed", "发布接口异常", {"account_id": account_id, "error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ops_store.create_publish_task(
        {
            "account_id": account_id,
            "title": note_info["title"],
            "desc": note_info["desc"],
            "topics": topic_list,
            "location": note_info["location"] or "",
            "privacy_type": privacy_type,
            "media_type": media_type,
            "media_names": [item.filename for item in images if item.filename] if media_type == "image" else [video.filename if video else ""],
            "scheduled_date": "",
            "status": "published" if success else "failed",
        }
    )
    return {"success": success, "msg": msg, "data": res_json}


if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    def serve_frontend_app(full_path: str):
        requested_path = FRONTEND_DIST / full_path
        if requested_path.is_file():
            return FileResponse(requested_path)
        return FileResponse(FRONTEND_DIST / "index.html")
