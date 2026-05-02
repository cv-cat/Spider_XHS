# -*- coding: utf-8 -*-
"""
小红书采集工具 — Web 后端
- 三种采集类型（comments / homepage / search）
- 每个任务可被多次「追加运行」，持久化到 data/tasks/<id>/
- SSE 实时上报当前 run 的事件流
"""
import json
import os
import shutil
import tempfile
import threading
import time
import urllib.parse
import uuid
from typing import Any, Dict, List, Optional

import requests
from flask import Flask, Response, jsonify, render_template, request, send_file

from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env
from xhs_utils.data_util import handle_comment_info, handle_note_info, save_to_xlsx


app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static",
    static_url_path="/assets",
)
app.config["JSON_AS_ASCII"] = False

XHS = XHS_Apis()
TASKS: Dict[str, "Task"] = {}
TASKS_LOCK = threading.Lock()

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "tasks"))
os.makedirs(STORAGE_DIR, exist_ok=True)


# ───────────────────────────── helpers ─────────────────────────────


def _parse_note_id_token(url: str):
    parsed = urllib.parse.urlparse(url)
    note_id = parsed.path.rstrip("/").split("/")[-1]
    qs = urllib.parse.parse_qs(parsed.query)
    return note_id, qs.get("xsec_token", [""])[0]


def _flatten_note_card(item: dict, fallback_url: str = "") -> dict:
    note_id = item.get("id") or item.get("note_id") or ""
    xsec = item.get("xsec_token", "")
    url = (
        fallback_url
        or (
            f"https://www.xiaohongshu.com/explore/{note_id}"
            + (f"?xsec_token={xsec}" if xsec else "")
        )
    )
    card = item.get("note_card") or {}
    user = card.get("user") or {}
    interact = card.get("interact_info") or {}
    cover = ""
    images = card.get("image_list") or []
    if images:
        try:
            cover = (
                images[0].get("info_list", [{}])[1].get("url")
                or images[0].get("url_default")
                or images[0].get("url")
                or ""
            )
        except Exception:
            cover = images[0].get("url_default", "") or images[0].get("url", "")
    raw_type = card.get("type", "")
    type_cn = "图集" if raw_type == "normal" else ("视频" if raw_type == "video" else raw_type)
    user_id = user.get("user_id", "")
    return {
        "note_id": note_id,
        "note_url": url,
        "xsec_token": xsec,
        "note_type": type_cn,
        "title": card.get("display_title") or card.get("title") or "",
        "desc": "",
        "user_id": user_id,
        "home_url": (f"https://www.xiaohongshu.com/user/profile/{user_id}" if user_id else ""),
        "nickname": user.get("nickname") or user.get("nick_name") or "",
        "avatar": user.get("avatar", ""),
        "liked_count": interact.get("liked_count", ""),
        "collected_count": interact.get("collected_count", ""),
        "comment_count": interact.get("comment_count", ""),
        "share_count": interact.get("share_count", ""),
        "video_cover": "",
        "video_addr": "",
        "image_list": [cover] if cover else [],
        "tags": [],
        "upload_time": "",
        "ip_location": "",
        "cover": cover,
        "_detailed": False,
    }


def _strip_cookies(params: dict) -> dict:
    return {k: v for k, v in (params or {}).items() if k != "cookies"}


def _atomic_write(path: str, content: str):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, path)


# ───────────────────────────── task model ─────────────────────────────


class Task:
    def __init__(self, kind: str, params: dict, name: Optional[str] = None, tid: Optional[str] = None):
        self.id = tid or uuid.uuid4().hex[:10]
        self.kind = kind  # 首次运行的类型，仅作展示参考
        self.name = name or self._default_name(kind, params)
        self.params: Dict[str, Any] = dict(params or {})
        self.notes: List[dict] = []
        self.comments: List[dict] = []
        self.runs: List[dict] = []  # {kind, params, started, finished, state, added_notes, added_comments}
        self.created = time.time()
        self.updated = self.created

        # 实时态（不持久化）
        self.events: List[dict] = []
        self.cond = threading.Condition()
        self.state = "idle"  # idle | running | stopped
        self.run_lock = threading.Lock()
        self.stop_event = threading.Event()
        self._cur_run: Optional[dict] = None
        self._cur_run_idx: int = 0  # events 在本次 run 起始的位置

        self.dir = os.path.join(STORAGE_DIR, self.id)

    @staticmethod
    def _default_name(kind: str, params: dict) -> str:
        if kind == "search":
            return f"搜索 · {params.get('query','')}"
        if kind == "homepage":
            url = params.get("user_url", "")
            uid = url.rstrip("/").split("/")[-1].split("?")[0][:10]
            return f"主页 · {uid}"
        if kind == "comments":
            urls = params.get("urls") or []
            return f"评论 · {len(urls)} 条"
        return kind

    # ── persistence ───────────────────────
    def _ensure_dir(self):
        os.makedirs(self.dir, exist_ok=True)

    def persist_meta(self):
        self._ensure_dir()
        meta = {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "params": _strip_cookies(self.params),
            "created": self.created,
            "updated": self.updated,
            "runs": [
                {**r, "params": _strip_cookies(r.get("params") or {})} for r in self.runs
            ],
            "counts": {"notes": len(self.notes), "comments": len(self.comments)},
        }
        _atomic_write(os.path.join(self.dir, "meta.json"), json.dumps(meta, ensure_ascii=False, indent=2))

    def rewrite_notes(self):
        self._ensure_dir()
        path = os.path.join(self.dir, "notes.jsonl")
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            for n in self.notes:
                f.write(json.dumps(n, ensure_ascii=False) + "\n")
        os.replace(path + ".tmp", path)

    def append_comments(self, items: List[dict]):
        if not items:
            return
        self._ensure_dir()
        with open(os.path.join(self.dir, "comments.jsonl"), "a", encoding="utf-8") as f:
            for c in items:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")

    @classmethod
    def load(cls, tid: str) -> Optional["Task"]:
        d = os.path.join(STORAGE_DIR, tid)
        meta_path = os.path.join(d, "meta.json")
        if not os.path.exists(meta_path):
            return None
        try:
            meta = json.loads(open(meta_path, "r", encoding="utf-8").read())
        except Exception:
            return None
        t = cls(meta.get("kind", "comments"), meta.get("params") or {}, name=meta.get("name"), tid=meta["id"])
        t.created = meta.get("created", t.created)
        t.updated = meta.get("updated", t.updated)
        t.runs = meta.get("runs", []) or []
        # notes
        notes_path = os.path.join(d, "notes.jsonl")
        if os.path.exists(notes_path):
            with open(notes_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        t.notes.append(json.loads(line))
                    except Exception:
                        pass
        # comments
        cms_path = os.path.join(d, "comments.jsonl")
        if os.path.exists(cms_path):
            with open(cms_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        t.comments.append(json.loads(line))
                    except Exception:
                        pass
        return t

    def delete_storage(self):
        try:
            shutil.rmtree(self.dir, ignore_errors=True)
        except Exception:
            pass

    # ── runtime ───────────────────────────
    def emit(self, t: str, p: Optional[dict] = None):
        evt = {"t": t, "p": p or {}, "ts": time.time(), "i": len(self.events)}
        with self.cond:
            self.events.append(evt)
            self.cond.notify_all()

    def stop(self):
        if self.state == "running":
            self.stop_event.set()
            self.emit("log", {"msg": "停止指令已发出"})

    def stopped(self) -> bool:
        return self.stop_event.is_set()

    def begin_run(self, kind: str, params: dict):
        with self.run_lock:
            if self.state == "running":
                raise RuntimeError("task is already running")
            self.state = "running"
            self.stop_event.clear()
            self.params = dict(params or {})
            self._cur_run = {
                "kind": kind,
                "params": _strip_cookies(params),
                "started": time.time(),
                "finished": None,
                "state": "running",
                "added_notes_start": len(self.notes),
                "added_comments_start": len(self.comments),
            }
            self._cur_run_idx = len(self.events)
            self.runs.append(self._cur_run)
            self.persist_meta()

    def end_run(self):
        run = self._cur_run
        if run is None:
            return
        run["finished"] = time.time()
        run["added_notes"] = len(self.notes) - run.pop("added_notes_start", len(self.notes))
        run["added_comments"] = len(self.comments) - run.pop("added_comments_start", len(self.comments))
        run["state"] = "stopped" if self.stopped() else "done"
        # 状态切换 + 通知必须在 cond 内，否则 SSE 生成器可能在 done 事件 emit 之前看到 idle 而提前关闭流
        with self.cond:
            self.state = "idle"
            self.updated = time.time()
            self.cond.notify_all()
        self.persist_meta()
        self._cur_run = None

    def to_summary(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "state": self.state,
            "params": _strip_cookies(self.params),
            "notes": len(self.notes),
            "comments": len(self.comments),
            "created": self.created,
            "updated": self.updated,
            "runs": [{**r, "params": _strip_cookies(r.get("params") or {})} for r in self.runs],
        }


# ───────────────────────────── enrichment / runners ─────────────────────────────


def _enrich_note_details(task: Task):
    cookies_str = task.params["cookies"]
    notes = task.notes
    target_ids = task.params.get("note_ids")
    if target_ids:
        target_set = set(target_ids)
        pending = [i for i, n in enumerate(notes)
                   if not n.get("_detailed") and n.get("note_id") in target_set]
    else:
        pending = [i for i, n in enumerate(notes) if not n.get("_detailed")]
    if not pending:
        return
    task.emit("phase", {"name": "details", "total": len(pending)})
    for k, idx in enumerate(pending, 1):
        if task.stopped():
            break
        n = notes[idx]
        url = n.get("note_url") or ""
        if not url:
            continue
        task.emit("note_index", {"i": k, "total": len(pending), "url": url})
        try:
            ok, msg, res = XHS.get_note_info(url, cookies_str)
            if not ok:
                task.emit("error", {"msg": f"详情失败: {msg}"})
                continue
            note_item = res["data"]["items"][0]
            note_item["url"] = url
            full = handle_note_info(note_item)
            full["xsec_token"] = n.get("xsec_token", "")
            full["cover"] = (
                full.get("video_cover")
                or (full.get("image_list") or [None])[0]
                or n.get("cover", "")
            )
            full["_detailed"] = True
            notes[idx] = full
            task.emit("note_done", {"count": idx + 1, "kind": "detail"})
        except Exception as e:
            task.emit("error", {"msg": f"详情异常: {e}"})
    task.rewrite_notes()
    task.emit("notes_collected", {"count": len(notes)})


def _fetch_comments_for_url(task: Task, url: str, fetch_sub: bool, cookies_str: str):
    note_id, xsec_token = _parse_note_id_token(url)
    task.emit("note_start", {"url": url, "note_id": note_id})

    cursor = ""
    out_comments: List[dict] = []
    while not task.stopped():
        ok, msg, res = XHS.get_note_out_comment(note_id, cursor, xsec_token, cookies_str)
        if not ok:
            task.emit("error", {"msg": f"一级评论失败: {msg}"})
            return []
        data = (res or {}).get("data", {}) or {}
        page = data.get("comments", []) or []
        out_comments.extend(page)
        task.emit("page", {"kind": "out", "count": len(out_comments)})
        cursor = str(data.get("cursor", ""))
        if not data.get("has_more") or not cursor:
            break
    if task.stopped():
        return []

    if fetch_sub:
        for idx, c in enumerate(out_comments, 1):
            if task.stopped():
                break
            if not c.get("sub_comment_has_more"):
                continue
            sub_cursor = c.get("sub_comment_cursor", "")
            while not task.stopped():
                ok, msg, res = XHS.get_note_inner_comment(c, sub_cursor, xsec_token, cookies_str)
                if not ok:
                    task.emit("error", {"msg": f"二级评论失败: {msg}"})
                    break
                data = (res or {}).get("data", {}) or {}
                sub_page = data.get("comments", []) or []
                c.setdefault("sub_comments", []).extend(sub_page)
                task.emit(
                    "page",
                    {"kind": "inner", "count": idx, "total": len(out_comments), "root_id": c.get("id")},
                )
                sub_cursor = str(data.get("cursor", ""))
                if not data.get("has_more") or not sub_cursor:
                    break

    flat: List[dict] = []
    for c in out_comments:
        c["note_id"] = note_id
        c["note_url"] = url
        root_id = c.get("id", "")
        try:
            flat.append(handle_comment_info(c, parent_comment_id="", level=1))
        except Exception as e:
            task.emit("error", {"msg": f"评论解析失败: {e}"})
        for sc in c.get("sub_comments", []) or []:
            sc["note_id"] = note_id
            sc["note_url"] = url
            try:
                flat.append(handle_comment_info(sc, parent_comment_id=root_id, level=2))
            except Exception as e:
                task.emit("error", {"msg": f"子评论解析失败: {e}"})

    task.emit("note_done", {"count": len(flat)})
    return flat


def run_comments_task(task: Task):
    p = task.params
    cookies_str = p["cookies"]
    urls: List[str] = p["urls"]
    fetch_sub: bool = p.get("fetch_sub", True)

    task.emit("phase", {"name": "comments", "total": len(urls)})
    for i, url in enumerate(urls, 1):
        if task.stopped():
            break
        task.emit("note_index", {"i": i, "total": len(urls), "url": url})
        comments = _fetch_comments_for_url(task, url, fetch_sub, cookies_str)
        task.comments.extend(comments)
        task.append_comments(comments)
        task.emit("comments_progress", {"total": len(task.comments)})


def _enqueue_comments_followup(task: Task, urls: List[str]):
    p = task.params
    if not p.get("with_comments"):
        return
    fetch_sub = p.get("fetch_sub", True)
    task.emit("phase", {"name": "comments", "total": len(urls)})
    for i, url in enumerate(urls, 1):
        if task.stopped():
            break
        task.emit("note_index", {"i": i, "total": len(urls), "url": url})
        comments = _fetch_comments_for_url(task, url, fetch_sub, p["cookies"])
        task.comments.extend(comments)
        task.append_comments(comments)
        task.emit("comments_progress", {"total": len(task.comments)})


def run_homepage_task(task: Task):
    p = task.params
    cookies_str = p["cookies"]
    user_url: str = p["user_url"]

    task.emit("phase", {"name": "homepage"})
    task.emit("log", {"msg": f"拉取主页 {user_url}"})

    parsed = urllib.parse.urlparse(user_url)
    user_id = parsed.path.rstrip("/").split("/")[-1]
    qs = urllib.parse.parse_qs(parsed.query)
    xsec_token = qs.get("xsec_token", [""])[0]
    xsec_source = qs.get("xsec_source", ["pc_search"])[0]

    cursor = ""
    raw_notes: List[dict] = []
    while not task.stopped():
        ok, msg, res = XHS.get_user_note_info(user_id, cursor, cookies_str, xsec_token, xsec_source)
        if not ok:
            task.emit("error", {"msg": f"主页拉取失败: {msg}"})
            return
        data = (res or {}).get("data", {}) or {}
        page = data.get("notes", []) or []
        raw_notes.extend(page)
        task.emit("page", {"kind": "user_posts", "count": len(raw_notes)})
        cursor = str(data.get("cursor", ""))
        if not page or not data.get("has_more") or not cursor:
            break

    note_urls: List[str] = []
    existing_ids = {n.get("note_id") for n in task.notes}
    for it in raw_notes:
        nid = it.get("note_id") or it.get("id")
        if nid in existing_ids:
            continue
        xt = it.get("xsec_token", "")
        url = (
            f"https://www.xiaohongshu.com/explore/{nid}"
            + (f"?xsec_token={xt}" if xt else "")
        )
        flat = _flatten_note_card({"id": nid, "xsec_token": xt, "note_card": it}, fallback_url=url)
        task.notes.append(flat)
        note_urls.append(url)
    task.rewrite_notes()
    task.emit("notes_collected", {"count": len(task.notes)})

    if p.get("fetch_detail"):
        _enrich_note_details(task)
    _enqueue_comments_followup(task, note_urls)


def run_search_task(task: Task):
    p = task.params
    cookies_str = p["cookies"]
    query: str = p["query"]
    require_num: int = int(p.get("require_num", 20))
    sort_type_choice = int(p.get("sort_type", 0))
    note_type = int(p.get("note_type", 0))
    note_time = int(p.get("note_time", 0))

    task.emit("phase", {"name": "search", "target": require_num})
    task.emit("log", {"msg": f"关键词「{query}」目标 {require_num} 条"})

    from xhs_utils.xhs_util import generate_search_id

    page = 1
    raw_notes: List[dict] = []
    root_search_id = generate_search_id()
    while not task.stopped():
        search_id = generate_search_id(root_search_id)
        ok, msg, res = XHS.search_note(
            query, cookies_str, page, sort_type_choice, note_type, note_time, 0, 0, "", search_id
        )
        if not ok:
            task.emit("error", {"msg": f"搜索失败: {msg}"})
            return
        data = (res or {}).get("data", {}) or {}
        items = data.get("items", []) or []
        items = [x for x in items if x.get("model_type") == "note"]
        raw_notes.extend(items)
        task.emit("page", {"kind": "search", "count": len(raw_notes), "total": require_num, "page": page})
        page += 1
        if len(raw_notes) >= require_num or not data.get("has_more"):
            break

    if len(raw_notes) > require_num:
        raw_notes = raw_notes[:require_num]

    note_urls: List[str] = []
    existing_ids = {n.get("note_id") for n in task.notes}
    for item in raw_notes:
        flat = _flatten_note_card(item)
        if flat["note_id"] in existing_ids:
            continue
        task.notes.append(flat)
        note_urls.append(flat["note_url"])
    task.rewrite_notes()
    task.emit("notes_collected", {"count": len(task.notes)})

    if p.get("fetch_detail"):
        _enrich_note_details(task)
    _enqueue_comments_followup(task, note_urls)


def run_task_thread(task: Task, kind: str):
    task.emit("task_start", {"kind": kind, "tid": task.id, "name": task.name})
    try:
        if kind == "comments":
            run_comments_task(task)
        elif kind == "homepage":
            run_homepage_task(task)
        elif kind == "search":
            run_search_task(task)
        elif kind == "details":
            # 补全笔记详情：扫描 task.notes 中 _detailed=False 的项
            if not task.notes:
                task.emit("error", {"msg": "当前任务没有笔记，无法补全详情"})
            else:
                _enrich_note_details(task)
        else:
            task.emit("error", {"msg": f"未知任务类型 {kind}"})
    except Exception as e:
        task.emit("error", {"msg": f"任务异常: {e}"})
    finally:
        cur = task._cur_run or {}
        started = cur.get("started") or time.time()
        notes_start = cur.get("added_notes_start", len(task.notes))
        comments_start = cur.get("added_comments_start", len(task.comments))
        final_state = "stopped" if task.stopped() else "done"
        # done 必须先发，再 end_run 切 state，否则 SSE 流可能错过 done 事件
        task.emit(
            "done",
            {
                "state": final_state,
                "notes": len(task.notes),
                "comments": len(task.comments),
                "added_notes": len(task.notes) - notes_start,
                "added_comments": len(task.comments) - comments_start,
                "elapsed": time.time() - started,
            },
        )
        task.end_run()


# ───────────────────────────── routes ─────────────────────────────


def _build_run_params(kind: str, body: dict) -> Dict[str, Any]:
    cookies_str = (body.get("cookies") or load_env() or "").strip()
    if not cookies_str:
        raise ValueError("missing cookies")
    params: Dict[str, Any] = {"cookies": cookies_str}
    if kind == "details":
        # 可选 note_ids：限定要补抓的笔记；为空时补全所有 _detailed=False 的笔记
        ids = body.get("note_ids")
        if isinstance(ids, list) and ids:
            params["note_ids"] = [str(x) for x in ids]
        return params
    if kind == "comments":
        urls = [u.strip() for u in (body.get("urls") or []) if u and u.strip()]
        if not urls:
            raise ValueError("no urls")
        params["urls"] = urls
        params["fetch_sub"] = bool(body.get("fetch_sub", True))
    elif kind == "homepage":
        user_url = (body.get("user_url") or "").strip()
        if not user_url:
            raise ValueError("missing user_url")
        params["user_url"] = user_url
        params["fetch_detail"] = bool(body.get("fetch_detail", True))
        params["with_comments"] = bool(body.get("with_comments", False))
        params["fetch_sub"] = bool(body.get("fetch_sub", True))
    elif kind == "search":
        query = (body.get("query") or "").strip()
        if not query:
            raise ValueError("missing query")
        params["query"] = query
        params["require_num"] = int(body.get("require_num", 20))
        params["sort_type"] = int(body.get("sort_type", 0))
        params["note_type"] = int(body.get("note_type", 0))
        params["note_time"] = int(body.get("note_time", 0))
        params["fetch_detail"] = bool(body.get("fetch_detail", True))
        params["with_comments"] = bool(body.get("with_comments", False))
        params["fetch_sub"] = bool(body.get("fetch_sub", True))
    else:
        raise ValueError("invalid kind")
    return params


# 工具集首页 — 添加新工具只需在这里追加一项
TOOLS = [
    {
        "id": "xhs",
        "name": "小红书采集工具",
        "desc": "笔记 / 评论批量采集，支持历史任务追加、详情补全、多任务管理",
        "icon": "📕",
        "color": "#E13A2C",
        "color_soft": "#FEE2DD",
        "url": "/xhs",
    },
    # 添加更多工具：
    # { "id": "douyin", "name": "抖音采集", "desc": "...", "icon": "🎵",
    #   "color": "#000000", "color_soft": "#F5F5F5", "url": "/douyin" },
]


@app.route("/")
def home():
    return render_template("home.html", tools=TOOLS)


@app.route("/xhs")
def xhs_index():
    return render_template("index.html")


@app.route("/api/cookie")
def api_cookie():
    cookie = load_env() or ""
    return jsonify(
        {
            "has_cookie": bool(cookie),
            "preview": (cookie[:10] + "…" + cookie[-6:]) if cookie else "",
            "length": len(cookie),
        }
    )


@app.route("/api/run", methods=["POST"])
def api_run():
    body = request.get_json(force=True) or {}
    kind = body.get("kind")
    if kind == "details":
        return jsonify({"error": "details 仅支持追加到现有任务"}), 400
    try:
        params = _build_run_params(kind, body)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    task = Task(kind, params, name=body.get("name"))
    with TASKS_LOCK:
        TASKS[task.id] = task
    task.persist_meta()
    try:
        task.begin_run(kind, params)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 409
    threading.Thread(target=run_task_thread, args=(task, kind), daemon=True).start()
    return jsonify({"task_id": task.id, "name": task.name, "cursor": task._cur_run_idx})


@app.route("/api/append/<tid>", methods=["POST"])
def api_append(tid):
    """对已有任务追加一次运行（kind 自定）。"""
    body = request.get_json(force=True) or {}
    kind = body.get("kind")
    task = TASKS.get(tid)
    if not task:
        return jsonify({"error": "not found"}), 404
    if task.state == "running":
        return jsonify({"error": "task is running"}), 409
    try:
        params = _build_run_params(kind, body)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    try:
        task.begin_run(kind, params)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 409
    threading.Thread(target=run_task_thread, args=(task, kind), daemon=True).start()
    return jsonify({"task_id": task.id, "name": task.name, "cursor": task._cur_run_idx})


@app.route("/api/tasks")
def api_tasks():
    with TASKS_LOCK:
        items = [t.to_summary() for t in TASKS.values()]
    items.sort(key=lambda x: x.get("updated", 0), reverse=True)
    return jsonify({"items": items})


@app.route("/api/task/<tid>")
def api_task(tid):
    t = TASKS.get(tid)
    if not t:
        return jsonify({"error": "not found"}), 404
    return jsonify(t.to_summary())


@app.route("/api/task/<tid>/rename", methods=["POST"])
def api_rename(tid):
    body = request.get_json(force=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "empty name"}), 400
    t = TASKS.get(tid)
    if not t:
        return jsonify({"error": "not found"}), 404
    t.name = name[:80]
    t.updated = time.time()
    t.persist_meta()
    return jsonify({"ok": True, "name": t.name})


@app.route("/api/task/<tid>", methods=["DELETE"])
def api_delete(tid):
    t = TASKS.get(tid)
    if not t:
        return jsonify({"error": "not found"}), 404
    if t.state == "running":
        return jsonify({"error": "task is running"}), 409
    with TASKS_LOCK:
        TASKS.pop(tid, None)
    t.delete_storage()
    return jsonify({"ok": True})


@app.route("/api/notes/<tid>")
def api_notes(tid):
    t = TASKS.get(tid)
    if not t:
        return jsonify({"error": "not found"}), 404
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 200))
    return jsonify({"total": len(t.notes), "items": t.notes[offset : offset + limit]})


@app.route("/api/comments/<tid>")
def api_comments(tid):
    t = TASKS.get(tid)
    if not t:
        return jsonify({"error": "not found"}), 404
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 200))
    return jsonify({"total": len(t.comments), "items": t.comments[offset : offset + limit]})


@app.route("/api/stop/<tid>", methods=["POST"])
def api_stop(tid):
    t = TASKS.get(tid)
    if not t:
        return jsonify({"error": "not found"}), 404
    t.stop()
    return jsonify({"ok": True})


@app.route("/api/stream/<tid>")
def api_stream(tid):
    t = TASKS.get(tid)
    if not t:
        return jsonify({"error": "not found"}), 404
    cursor = int(request.args.get("cursor", 0))

    def gen(task: Task, idx: int):
        with task.cond:
            while True:
                while idx < len(task.events):
                    yield f"data: {json.dumps(task.events[idx], ensure_ascii=False)}\n\n"
                    idx += 1
                # 任务空闲 → 当前 run 结束，关闭流
                if task.state == "idle":
                    yield "event: end\ndata: {}\n\n"
                    return
                task.cond.wait(timeout=15)
                if idx >= len(task.events):
                    yield ": ping\n\n"

    return Response(gen(t, cursor), mimetype="text/event-stream")


_ALLOWED_IMG_HOSTS = (
    "xhscdn.com",
    "xiaohongshu.com",
    "xhsstatic.com",
)


@app.route("/api/img")
def api_img():
    """图片 / 视频代理，加 Referer 绕过 CDN 校验。"""
    url = request.args.get("u", "")
    if not url:
        return ("", 400)
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    if not any(host.endswith(d) for d in _ALLOWED_IMG_HOSTS):
        return ("forbidden host", 400)
    headers = {
        "Referer": "https://www.xiaohongshu.com/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
    }
    try:
        upstream = requests.get(url, headers=headers, timeout=20, stream=True)
    except Exception as e:
        return (f"upstream error: {e}", 502)
    ctype = upstream.headers.get("Content-Type", "application/octet-stream")
    resp = Response(
        upstream.iter_content(chunk_size=16 * 1024),
        status=upstream.status_code,
        content_type=ctype,
    )
    resp.headers["Cache-Control"] = "public, max-age=86400"
    cl = upstream.headers.get("Content-Length")
    if cl:
        resp.headers["Content-Length"] = cl
    return resp


@app.route("/api/note/<tid>/<note_id>")
def api_note_detail(tid, note_id):
    t = TASKS.get(tid)
    if not t:
        return jsonify({"error": "not found"}), 404
    note = next((n for n in t.notes if n.get("note_id") == note_id), None)
    if not note:
        return jsonify({"error": "note not in task"}), 404
    cms = [c for c in t.comments if c.get("note_id") == note_id]
    # 父评论先，子评论按 parent_comment_id 折叠
    return jsonify({"note": note, "comments": cms, "count": len(cms)})


@app.route("/api/export/<tid>")
def api_export(tid):
    t = TASKS.get(tid)
    if not t:
        return jsonify({"error": "not found"}), 404
    kind = request.args.get("kind", "comments")
    if kind == "comments":
        if not t.comments:
            return jsonify({"error": "no comments"}), 400
        items = t.comments
        sheet_kind = "comment"
        prefix = "comments"
    else:
        if not t.notes:
            return jsonify({"error": "no notes"}), 400
        items = t.notes
        sheet_kind = "note"
        prefix = "notes"

    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    try:
        save_to_xlsx(items, path, type=sheet_kind)
        return send_file(
            path,
            as_attachment=True,
            download_name=f"{prefix}_{t.id}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ───────────────────────────── boot ─────────────────────────────


def _load_persisted_tasks():
    if not os.path.isdir(STORAGE_DIR):
        return
    for name in os.listdir(STORAGE_DIR):
        d = os.path.join(STORAGE_DIR, name)
        if not os.path.isdir(d):
            continue
        t = Task.load(name)
        if t:
            TASKS[t.id] = t


_load_persisted_tasks()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    print(f"\n  小红书采集工具 → http://{args.host}:{args.port}")
    print(f"  数据目录       → {STORAGE_DIR}")
    print(f"  历史任务       → {len(TASKS)} 条已加载\n")
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
