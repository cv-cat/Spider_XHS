import json
import os
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from apis.xhs_creator_apis import XHS_Creator_Apis
from server.account_store import AccountStore
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
creator_api = XHS_Creator_Apis()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
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


def require_account(account_id: str) -> dict:
    account = store.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return account


def check_creator_cookie(account_id: str) -> tuple[bool, str, dict | None]:
    account = require_account(account_id)
    try:
        success, msg, res_json = creator_api.get_publish_note_info(None, account["cookies"])
    except Exception as exc:
        success, msg, res_json = False, str(exc), None

    data = res_json.get("data") if isinstance(res_json, dict) else None
    is_valid = bool(success and isinstance(data, dict) and "notes" in data)
    status = "valid" if is_valid else "invalid"
    store.update_check_status(account_id, status)
    if not is_valid and not msg:
        msg = "Cookie 无效或登录状态异常"
    return is_valid, msg or "Cookie 可用", res_json


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


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/accounts")
def list_accounts() -> dict:
    return {"accounts": store.list_accounts()}


@app.post("/api/accounts")
def create_account(payload: AccountCreate) -> dict:
    account = store.create_account(payload.name, payload.cookies)
    return {"account": account}


@app.delete("/api/accounts/{account_id}")
def delete_account(account_id: str) -> dict:
    deleted = store.delete_account(account_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="账号不存在")
    return {"success": True}


@app.post("/api/accounts/{account_id}/check")
def check_account(account_id: str) -> dict:
    success, msg, _ = check_creator_cookie(account_id)
    return {"success": success, "msg": msg}


@app.post("/api/topics/search")
def search_topics(payload: TopicSearchRequest) -> dict:
    account = require_account(payload.account_id)
    try:
        cookies = trans_cookies(account["cookies"])
        success, msg, res_json = creator_api.get_topic(payload.keyword, cookies)
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
    account = require_account(account_id)
    cookie_ok, cookie_msg, _ = check_creator_cookie(account_id)
    if not cookie_ok:
        raise HTTPException(status_code=400, detail=f"Cookie 不可用: {cookie_msg}")

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
        success, msg, res_json = creator_api.post_note(note_info, account["cookies"])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": success, "msg": msg, "data": res_json}
