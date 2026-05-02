# -*- coding: utf-8 -*-
"""
小红书评论采集可视化界面
- 输入笔记 URL（多行，每行一个）
- 实时展示总体进度 / 当前笔记进度 / 已采集评论数 / 日志
- 完成后可导出为 Excel
"""
import os
import queue
import threading
import time
import tkinter as tk
import urllib.parse
from tkinter import filedialog, messagebox, scrolledtext, ttk

from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env
from xhs_utils.data_util import handle_comment_info, save_to_xlsx


STATE_IDLE = "idle"
STATE_RUNNING = "running"
STATE_STOPPING = "stopping"


def _parse_note_id_token(url: str):
    parsed = urllib.parse.urlparse(url)
    note_id = parsed.path.rstrip("/").split("/")[-1]
    qs = urllib.parse.parse_qs(parsed.query)
    xsec_token = qs.get("xsec_token", [""])[0]
    return note_id, xsec_token


class CommentFetcher:
    """对 XHS_Apis 评论接口的薄封装，按页拉取并通过回调上报进度。"""

    def __init__(self, cookies_str: str, proxies: dict = None):
        self.api = XHS_Apis()
        self.cookies_str = cookies_str
        self.proxies = proxies
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self) -> bool:
        return self._stop.is_set()

    def fetch_one_note(self, url: str, fetch_sub: bool, progress_cb):
        """
        progress_cb(event: str, payload: dict) 事件:
          - 'note_start' {url, note_id}
          - 'page' {kind: 'out'|'inner', count, root_id?}
          - 'note_done' {count}
          - 'log' {msg}
          - 'error' {msg}
        返回扁平化后的评论 dict 列表（已经经过 handle_comment_info）
        """
        flat = []
        try:
            note_id, xsec_token = _parse_note_id_token(url)
            progress_cb("note_start", {"url": url, "note_id": note_id})

            # ---- 一级评论分页 ----
            cursor = ""
            out_comments = []
            while not self._stop.is_set():
                ok, msg, res = self.api.get_note_out_comment(
                    note_id, cursor, xsec_token, self.cookies_str, self.proxies
                )
                if not ok:
                    progress_cb("error", {"msg": f"一级评论失败: {msg}"})
                    return flat
                data = res.get("data", {}) if res else {}
                page = data.get("comments", []) or []
                out_comments.extend(page)
                progress_cb("page", {"kind": "out", "count": len(out_comments)})
                cursor = str(data.get("cursor", ""))
                if not data.get("has_more") or not cursor:
                    break

            if self._stop.is_set():
                return flat

            # ---- 二级评论分页（可选）----
            if fetch_sub:
                for idx, c in enumerate(out_comments, 1):
                    if self._stop.is_set():
                        break
                    if not c.get("sub_comment_has_more"):
                        continue
                    sub_cursor = c.get("sub_comment_cursor", "")
                    while not self._stop.is_set():
                        ok, msg, res = self.api.get_note_inner_comment(
                            c, sub_cursor, xsec_token, self.cookies_str, self.proxies
                        )
                        if not ok:
                            progress_cb("error", {"msg": f"二级评论失败: {msg}"})
                            break
                        data = res.get("data", {}) if res else {}
                        sub_page = data.get("comments", []) or []
                        c.setdefault("sub_comments", []).extend(sub_page)
                        progress_cb(
                            "page",
                            {
                                "kind": "inner",
                                "count": idx,
                                "total": len(out_comments),
                                "root_id": c.get("id"),
                            },
                        )
                        sub_cursor = str(data.get("cursor", ""))
                        if not data.get("has_more") or not sub_cursor:
                            break

            # ---- 扁平化并归一化 ----
            for c in out_comments:
                c["note_id"] = note_id
                c["note_url"] = url
                try:
                    flat.append(handle_comment_info(c))
                except Exception as e:
                    progress_cb("error", {"msg": f"评论解析失败: {e}"})
                for sc in c.get("sub_comments", []) or []:
                    sc["note_id"] = note_id
                    sc["note_url"] = url
                    try:
                        flat.append(handle_comment_info(sc))
                    except Exception as e:
                        progress_cb("error", {"msg": f"子评论解析失败: {e}"})

            progress_cb("note_done", {"count": len(flat)})
        except Exception as e:
            progress_cb("error", {"msg": f"异常: {e}"})
        return flat


class CommentGUI:
    POLL_MS = 80

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("小红书评论采集 · 可视化")
        self.root.geometry("980x720")

        self.event_q: "queue.Queue[tuple]" = queue.Queue()
        self.state = STATE_IDLE
        self.worker: threading.Thread = None
        self.fetcher: CommentFetcher = None
        self.results: list = []
        self.start_time = 0.0
        self.note_total = 0
        self.note_done = 0
        self.cur_out = 0
        self.cur_inner = 0  # 已处理一级评论数（按子评论展开维度）
        self.cur_inner_total = 0

        self._build_ui()
        self.root.after(self.POLL_MS, self._poll_events)

    # ---------------- UI ----------------
    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        # 顶部：Cookie + 选项
        top = ttk.LabelFrame(self.root, text="配置")
        top.pack(fill="x", **pad)

        ttk.Label(top, text="Cookie：").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.cookie_var = tk.StringVar(value=load_env() or "")
        self.cookie_entry = ttk.Entry(top, textvariable=self.cookie_var, show="*")
        self.cookie_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        self.show_cookie_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            top, text="显示", variable=self.show_cookie_var, command=self._toggle_cookie
        ).grid(row=0, column=2, padx=6)
        self.fetch_sub_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="包含二级评论", variable=self.fetch_sub_var).grid(
            row=0, column=3, padx=6
        )
        top.columnconfigure(1, weight=1)

        # 中部：URL 输入
        mid = ttk.LabelFrame(self.root, text="笔记 URL（每行一个）")
        mid.pack(fill="both", expand=False, **pad)
        self.url_text = scrolledtext.ScrolledText(mid, height=6, wrap="none")
        self.url_text.pack(fill="both", expand=True, padx=6, pady=6)

        # 操作按钮
        ops = ttk.Frame(self.root)
        ops.pack(fill="x", **pad)
        self.start_btn = ttk.Button(ops, text="开始采集", command=self.start)
        self.start_btn.pack(side="left", padx=4)
        self.stop_btn = ttk.Button(ops, text="停止", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=4)
        self.save_btn = ttk.Button(
            ops, text="导出 Excel", command=self.export_excel, state="disabled"
        )
        self.save_btn.pack(side="left", padx=4)
        self.clear_btn = ttk.Button(ops, text="清空日志", command=self._clear_log)
        self.clear_btn.pack(side="left", padx=4)

        # 进度面板
        prog = ttk.LabelFrame(self.root, text="进度")
        prog.pack(fill="x", **pad)

        ttk.Label(prog, text="总体：").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.overall_pb = ttk.Progressbar(prog, length=600, mode="determinate")
        self.overall_pb.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        self.overall_lbl = ttk.Label(prog, text="0 / 0")
        self.overall_lbl.grid(row=0, column=2, sticky="w", padx=6)

        ttk.Label(prog, text="当前笔记：").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.cur_pb = ttk.Progressbar(prog, length=600, mode="indeterminate")
        self.cur_pb.grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        self.cur_lbl = ttk.Label(prog, text="—")
        self.cur_lbl.grid(row=1, column=2, sticky="w", padx=6)

        stats = ttk.Frame(prog)
        stats.grid(row=2, column=0, columnspan=3, sticky="we", padx=6, pady=4)
        self.stat_total = ttk.Label(stats, text="已采集评论：0")
        self.stat_total.pack(side="left", padx=10)
        self.stat_pages = ttk.Label(stats, text="一级评论页累计：0")
        self.stat_pages.pack(side="left", padx=10)
        self.stat_sub = ttk.Label(stats, text="子评论展开：0/0")
        self.stat_sub.pack(side="left", padx=10)
        self.stat_time = ttk.Label(stats, text="耗时：0.0s")
        self.stat_time.pack(side="left", padx=10)
        prog.columnconfigure(1, weight=1)

        # 日志
        logf = ttk.LabelFrame(self.root, text="日志")
        logf.pack(fill="both", expand=True, **pad)
        self.log = scrolledtext.ScrolledText(logf, height=12, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, padx=6, pady=6)

        # 底部状态
        self.status = ttk.Label(self.root, text="就绪", anchor="w")
        self.status.pack(fill="x", padx=8, pady=4)

    def _toggle_cookie(self):
        self.cookie_entry.config(show="" if self.show_cookie_var.get() else "*")

    def _clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    def _append_log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.log.config(state="normal")
        self.log.insert("end", f"[{ts}] {msg}\n")
        self.log.see("end")
        self.log.config(state="disabled")

    # ---------------- 控制 ----------------
    def start(self):
        if self.state != STATE_IDLE:
            return
        cookies_str = self.cookie_var.get().strip()
        if not cookies_str:
            messagebox.showwarning("缺少 Cookie", "请填入 Cookie 后再开始")
            return
        urls = [
            line.strip()
            for line in self.url_text.get("1.0", "end").splitlines()
            if line.strip()
        ]
        if not urls:
            messagebox.showwarning("缺少 URL", "请至少输入一个笔记 URL")
            return

        self.results = []
        self.note_total = len(urls)
        self.note_done = 0
        self.cur_out = 0
        self.cur_inner = 0
        self.cur_inner_total = 0
        self.start_time = time.time()

        self.overall_pb.config(maximum=self.note_total, value=0)
        self.overall_lbl.config(text=f"0 / {self.note_total}")
        self.cur_pb.config(mode="indeterminate")
        self.cur_pb.start(80)
        self.cur_lbl.config(text="准备中…")
        self.stat_total.config(text="已采集评论：0")
        self.stat_pages.config(text="一级评论页累计：0")
        self.stat_sub.config(text="子评论展开：0/0")
        self.stat_time.config(text="耗时：0.0s")

        self.state = STATE_RUNNING
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.save_btn.config(state="disabled")
        self.status.config(text="采集中…")

        self.fetcher = CommentFetcher(cookies_str)
        self.worker = threading.Thread(
            target=self._run_worker,
            args=(urls, self.fetch_sub_var.get()),
            daemon=True,
        )
        self.worker.start()

    def stop(self):
        if self.state != STATE_RUNNING:
            return
        self.state = STATE_STOPPING
        if self.fetcher:
            self.fetcher.stop()
        self.stop_btn.config(state="disabled")
        self.status.config(text="正在停止…")
        self._post("log", {"msg": "用户请求停止，等待当前请求结束…"})

    def export_excel(self):
        if not self.results:
            messagebox.showinfo("无数据", "没有可导出的评论")
            return
        default = f"comments_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default,
            filetypes=[("Excel", "*.xlsx")],
        )
        if not path:
            return
        try:
            save_to_xlsx(self.results, path, type="comment")
            self._append_log(f"已导出 {len(self.results)} 条评论 → {path}")
            messagebox.showinfo("导出成功", f"共 {len(self.results)} 条评论\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    # ---------------- 工作线程 ----------------
    def _run_worker(self, urls, fetch_sub):
        try:
            for i, url in enumerate(urls, 1):
                if self.fetcher.stopped():
                    break
                self._post("note_index", {"i": i, "total": len(urls), "url": url})
                comments = self.fetcher.fetch_one_note(url, fetch_sub, self._post)
                self._post("note_collected", {"items": comments})
        finally:
            self._post("done", {})

    def _post(self, event: str, payload: dict):
        self.event_q.put((event, payload))

    # ---------------- 事件循环 ----------------
    def _poll_events(self):
        try:
            while True:
                event, payload = self.event_q.get_nowait()
                self._handle_event(event, payload)
        except queue.Empty:
            pass

        if self.state == STATE_RUNNING:
            elapsed = time.time() - self.start_time
            self.stat_time.config(text=f"耗时：{elapsed:.1f}s")

        self.root.after(self.POLL_MS, self._poll_events)

    def _handle_event(self, event: str, payload: dict):
        if event == "note_index":
            self.cur_out = 0
            self.cur_inner = 0
            self.cur_inner_total = 0
            self.cur_pb.config(mode="indeterminate")
            self.cur_pb.start(80)
            short = payload["url"]
            if len(short) > 70:
                short = short[:67] + "..."
            self.cur_lbl.config(text=f"[{payload['i']}/{payload['total']}] {short}")
            self._append_log(f"开始第 {payload['i']}/{payload['total']} 条：{payload['url']}")

        elif event == "note_start":
            self._append_log(f"  note_id={payload['note_id']}")

        elif event == "page":
            if payload["kind"] == "out":
                self.cur_out = payload["count"]
                self.stat_pages.config(text=f"一级评论页累计：{self.cur_out}")
            else:
                self.cur_inner = payload["count"]
                self.cur_inner_total = payload.get("total", self.cur_inner_total)
                # 切换为确定模式展示子评论扫描进度
                if self.cur_inner_total:
                    self.cur_pb.stop()
                    self.cur_pb.config(
                        mode="determinate",
                        maximum=self.cur_inner_total,
                        value=self.cur_inner,
                    )
                self.stat_sub.config(
                    text=f"子评论展开：{self.cur_inner}/{self.cur_inner_total}"
                )

        elif event == "note_done":
            self._append_log(f"  ✓ 完成，共 {payload['count']} 条")

        elif event == "note_collected":
            self.note_done += 1
            self.results.extend(payload.get("items", []))
            self.overall_pb.config(value=self.note_done)
            self.overall_lbl.config(text=f"{self.note_done} / {self.note_total}")
            self.stat_total.config(text=f"已采集评论：{len(self.results)}")
            self.cur_pb.stop()
            self.cur_pb.config(mode="determinate", maximum=1, value=1)

        elif event == "error":
            self._append_log(f"  ✗ {payload['msg']}")

        elif event == "log":
            self._append_log(payload["msg"])

        elif event == "done":
            self.cur_pb.stop()
            self.cur_pb.config(mode="determinate", value=0)
            elapsed = time.time() - self.start_time
            self.stat_time.config(text=f"耗时：{elapsed:.1f}s")
            self.state = STATE_IDLE
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.save_btn.config(state="normal" if self.results else "disabled")
            self.status.config(
                text=f"完成：{self.note_done}/{self.note_total} 条笔记，{len(self.results)} 条评论"
            )
            self._append_log(
                f"全部完成，共 {len(self.results)} 条评论，用时 {elapsed:.1f}s"
            )


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    CommentGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
