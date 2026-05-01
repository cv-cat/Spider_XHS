import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Account = {
  id: string;
  name: string;
  cookie_preview: string;
  created_at?: string;
  updated_at?: string;
  last_check_at?: string | null;
  last_check_status?: string | null;
};

type Topic = {
  id?: string;
  name?: string;
  link?: string;
};

type Profile = {
  user_id: string;
  home_url: string;
  nickname: string;
  avatar: string;
  red_id: string;
  gender: string;
  ip_location: string;
  desc: string;
  follows: string | number;
  fans: string | number;
  interaction: string | number;
  tags: string[];
};

type SearchNote = {
  note_id: string;
  note_url: string;
  title: string;
  desc: string;
  cover: string;
  note_type: string;
  user_id: string;
  nickname: string;
  liked_count: string | number;
  collected_count: string | number;
  comment_count: string | number;
  xsec_token: string;
  xsec_source?: string;
  image_list: string[];
  video_addr: string;
  upload_time: string;
};

type OperationSummary = {
  publish_total: number;
  publish_pending: number;
  publish_done: number;
  publish_failed: number;
  monitor_total: number;
  monitor_enabled: number;
  search_result_total: number;
  analytics_snapshot_total: number;
  latest_logs: OperationLog[];
};

type OperationLog = {
  id: string;
  event_type: string;
  message: string;
  created_at: string;
};

type PublishTask = {
  id: string;
  account_id: string;
  title: string;
  desc: string;
  topics: string[];
  media_type: string;
  media_names: string[];
  scheduled_date: string;
  status: string;
  last_error: string;
  created_at: string;
  updated_at: string;
};

type SearchMonitor = {
  id: string;
  account_id: string;
  keyword: string;
  require_num: number;
  sort_type_choice: number;
  note_type: number;
  note_time: number;
  interval_minutes: number;
  enabled: boolean;
  last_run_at?: string | null;
  last_run_status?: string;
  last_run_message?: string;
};

type SavedSearchResult = {
  id: string;
  monitor_id: string;
  keyword: string;
  note: SearchNote;
  status: string;
  created_at: string;
};

type AnalyticsSnapshot = {
  id: string;
  account_id: string;
  profile: Profile;
  recent_notes: SearchNote[];
  created_at: string;
};

type Status = {
  type: "idle" | "loading" | "success" | "error";
  text: string;
};

type TabKey = "dashboard" | "accounts" | "publish" | "tasks" | "profile" | "search" | "monitors" | "analytics";

const initialStatus: Status = { type: "idle", text: "" };
const tabs: Array<{ key: TabKey; label: string }> = [
  { key: "dashboard", label: "运营概览" },
  { key: "accounts", label: "账号管理" },
  { key: "publish", label: "发布笔记" },
  { key: "tasks", label: "发布任务" },
  { key: "profile", label: "主页查询" },
  { key: "search", label: "关键词查询" },
  { key: "monitors", label: "关键词监控" },
  { key: "analytics", label: "账号分析" }
];

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();
  if (!response.ok) {
    const detail = typeof body === "object" && body && "detail" in body ? body.detail : body;
    throw new Error(String(detail || response.statusText));
  }
  return body as T;
}

function splitTopics(value: string): string[] {
  return value
    .split(/[,\n，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function mediaProxyUrl(url?: string): string {
  return url ? `/api/media/proxy?url=${encodeURIComponent(url)}` : "";
}

function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("dashboard");
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState("");
  const [accountName, setAccountName] = useState("");
  const [accountCookies, setAccountCookies] = useState("");
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [topics, setTopics] = useState("");
  const [topicKeyword, setTopicKeyword] = useState("");
  const [topicResults, setTopicResults] = useState<Topic[]>([]);
  const [location, setLocation] = useState("");
  const [privacyType, setPrivacyType] = useState("1");
  const [mediaType, setMediaType] = useState<"image" | "video">("image");
  const [images, setImages] = useState<FileList | null>(null);
  const [video, setVideo] = useState<File | null>(null);
  const [profileInput, setProfileInput] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchCount, setSearchCount] = useState("10");
  const [sortType, setSortType] = useState("0");
  const [noteType, setNoteType] = useState("0");
  const [noteTime, setNoteTime] = useState("0");
  const [searchResults, setSearchResults] = useState<SearchNote[]>([]);
  const [profileNotes, setProfileNotes] = useState<SearchNote[]>([]);
  const [profileCursor, setProfileCursor] = useState("");
  const [profileHasMore, setProfileHasMore] = useState(false);
  const [profileNotesUserId, setProfileNotesUserId] = useState("");
  const [detailLoadingIds, setDetailLoadingIds] = useState<string[]>([]);
  const [summary, setSummary] = useState<OperationSummary | null>(null);
  const [publishTasks, setPublishTasks] = useState<PublishTask[]>([]);
  const [taskDate, setTaskDate] = useState("");
  const [searchMonitors, setSearchMonitors] = useState<SearchMonitor[]>([]);
  const [monitorKeyword, setMonitorKeyword] = useState("");
  const [monitorInterval, setMonitorInterval] = useState("60");
  const [savedSearchResults, setSavedSearchResults] = useState<SavedSearchResult[]>([]);
  const [analyticsSnapshots, setAnalyticsSnapshots] = useState<AnalyticsSnapshot[]>([]);
  const [status, setStatus] = useState<Status>(initialStatus);

  const selectedAccount = useMemo(
    () => accounts.find((account) => account.id === selectedAccountId),
    [accounts, selectedAccountId]
  );

  async function loadAccounts() {
    const data = await apiFetch<{ accounts: Account[] }>("/api/accounts");
    setAccounts(data.accounts);
    if (!selectedAccountId && data.accounts.length > 0) {
      setSelectedAccountId(data.accounts[0].id);
    }
  }

  async function loadOperations() {
    const [summaryData, tasksData, monitorsData, resultsData, snapshotsData] = await Promise.all([
      apiFetch<{ summary: OperationSummary }>("/api/ops/summary"),
      apiFetch<{ tasks: PublishTask[] }>("/api/publish-tasks"),
      apiFetch<{ monitors: SearchMonitor[] }>("/api/search-monitors"),
      apiFetch<{ results: SavedSearchResult[] }>("/api/search-results"),
      apiFetch<{ snapshots: AnalyticsSnapshot[] }>("/api/analytics/snapshots")
    ]);
    setSummary(summaryData.summary);
    setPublishTasks(tasksData.tasks);
    setSearchMonitors(monitorsData.monitors);
    setSavedSearchResults(resultsData.results);
    setAnalyticsSnapshots(snapshotsData.snapshots);
  }

  useEffect(() => {
    loadAccounts().catch((error) => setStatus({ type: "error", text: error.message }));
    loadOperations().catch((error) => setStatus({ type: "error", text: error.message }));
  }, []);

  function requireSelectedAccount(): boolean {
    if (!selectedAccountId) {
      setStatus({ type: "error", text: "请先选择账号" });
      return false;
    }
    return true;
  }

  async function addAccount(event: FormEvent) {
    event.preventDefault();
    setStatus({ type: "loading", text: "正在保存账号..." });
    try {
      const data = await apiFetch<{ account: Account }>("/api/accounts", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: accountName, cookies: accountCookies })
      });
      setAccountName("");
      setAccountCookies("");
      await loadAccounts();
      setSelectedAccountId(data.account.id);
      setStatus({ type: "success", text: "账号已保存" });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function deleteAccount() {
    if (!requireSelectedAccount()) return;
    setStatus({ type: "loading", text: "正在删除账号..." });
    try {
      await apiFetch(`/api/accounts/${selectedAccountId}`, { method: "DELETE" });
      setSelectedAccountId("");
      await loadAccounts();
      setStatus({ type: "success", text: "账号已删除" });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function checkAccount() {
    if (!requireSelectedAccount()) return;
    setStatus({ type: "loading", text: "正在校验 Cookie..." });
    try {
      const data = await apiFetch<{ success: boolean; msg: string }>(
        `/api/accounts/${selectedAccountId}/check`,
        { method: "POST" }
      );
      await loadAccounts();
      setStatus({ type: data.success ? "success" : "error", text: data.msg });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function searchTopics(event: FormEvent) {
    event.preventDefault();
    if (!requireSelectedAccount() || !topicKeyword.trim()) return;
    setStatus({ type: "loading", text: "正在搜索话题..." });
    try {
      const data = await apiFetch<{ topics: Topic[] }>("/api/topics/search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ account_id: selectedAccountId, keyword: topicKeyword })
      });
      setTopicResults(data.topics);
      setStatus({ type: "success", text: `找到 ${data.topics.length} 个话题` });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  function addTopic(name?: string) {
    if (!name) return;
    const next = Array.from(new Set([...splitTopics(topics), name]));
    setTopics(next.join(", "));
  }

  async function publish(event: FormEvent) {
    event.preventDefault();
    if (!requireSelectedAccount()) return;
    const formData = new FormData();
    formData.append("account_id", selectedAccountId);
    formData.append("title", title);
    formData.append("desc", desc);
    formData.append("topics", JSON.stringify(splitTopics(topics)));
    formData.append("location", location);
    formData.append("privacy_type", privacyType);
    formData.append("media_type", mediaType);
    if (mediaType === "image") {
      Array.from(images || []).forEach((file) => formData.append("images", file));
    } else if (video) {
      formData.append("video", video);
    }

    setStatus({ type: "loading", text: "正在校验账号并发布..." });
    try {
      const data = await apiFetch<{ success: boolean; msg: string; data: unknown }>("/api/publish", {
        method: "POST",
        body: formData
      });
      setStatus({
        type: data.success ? "success" : "error",
        text: `${data.msg}\n${JSON.stringify(data.data, null, 2)}`
      });
      await loadOperations();
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function savePublishTask() {
    if (!requireSelectedAccount() || !title.trim()) return;
    setStatus({ type: "loading", text: "正在保存发布任务..." });
    try {
      await apiFetch<{ task: PublishTask }>("/api/publish-tasks", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          account_id: selectedAccountId,
          title,
          desc,
          topics: splitTopics(topics),
          location,
          privacy_type: Number(privacyType),
          media_type: mediaType,
          media_names: mediaType === "image" ? Array.from(images || []).map((file) => file.name) : [video?.name || ""].filter(Boolean),
          scheduled_date: taskDate,
          status: "pending"
        })
      });
      await loadOperations();
      setStatus({ type: "success", text: "发布任务已保存" });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function getSelfProfile() {
    if (!requireSelectedAccount()) return;
    setStatus({ type: "loading", text: "正在获取当前账号主页..." });
    try {
      const data = await apiFetch<{ profile: Profile }>("/api/profile/self", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ account_id: selectedAccountId })
      });
      setProfile(data.profile);
      setProfileNotes([]);
      setProfileCursor("");
      setProfileHasMore(false);
      setProfileNotesUserId("");
      setStatus({ type: "success", text: "主页资料获取成功" });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function queryProfile(event: FormEvent) {
    event.preventDefault();
    if (!requireSelectedAccount() || !profileInput.trim()) return;
    setStatus({ type: "loading", text: "正在查询主页..." });
    try {
      const data = await apiFetch<{ profile: Profile }>("/api/profile/query", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ account_id: selectedAccountId, user_url_or_id: profileInput })
      });
      setProfile(data.profile);
      setProfileNotes([]);
      setProfileCursor("");
      setProfileHasMore(false);
      setProfileNotesUserId("");
      setStatus({ type: "success", text: "主页资料获取成功" });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function searchNotes(event: FormEvent) {
    event.preventDefault();
    if (!requireSelectedAccount() || !searchQuery.trim()) return;
    setStatus({ type: "loading", text: "正在搜索笔记..." });
    try {
      const data = await apiFetch<{ notes: SearchNote[] }>("/api/search/notes", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          account_id: selectedAccountId,
          query: searchQuery,
          require_num: Number(searchCount),
          sort_type_choice: Number(sortType),
          note_type: Number(noteType),
          note_time: Number(noteTime)
        })
      });
      setSearchResults(data.notes);
      setStatus({ type: "success", text: `找到 ${data.notes.length} 条笔记。为降低请求频率，正文和媒体请按需加载。` });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function createMonitor(event: FormEvent) {
    event.preventDefault();
    if (!requireSelectedAccount() || !monitorKeyword.trim()) return;
    setStatus({ type: "loading", text: "正在保存关键词监控..." });
    try {
      await apiFetch<{ monitor: SearchMonitor }>("/api/search-monitors", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          account_id: selectedAccountId,
          keyword: monitorKeyword,
          require_num: Number(searchCount),
          sort_type_choice: Number(sortType),
          note_type: Number(noteType),
          note_time: Number(noteTime),
          interval_minutes: Number(monitorInterval),
          enabled: true
        })
      });
      setMonitorKeyword("");
      await loadOperations();
      setStatus({ type: "success", text: "关键词监控已保存" });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function runMonitor(monitorId: string) {
    setStatus({ type: "loading", text: "正在执行关键词监控..." });
    try {
      const data = await apiFetch<{ notes: SearchNote[]; saved: SavedSearchResult[] }>(
        `/api/search-monitors/${monitorId}/run`,
        { method: "POST" }
      );
      await loadOperations();
      setStatus({ type: "success", text: `监控完成，返回 ${data.notes.length} 条，新增 ${data.saved.length} 条` });
    } catch (error) {
      await loadOperations().catch(() => undefined);
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function deleteMonitor(monitorId: string) {
    setStatus({ type: "loading", text: "正在删除关键词监控..." });
    try {
      await apiFetch(`/api/search-monitors/${monitorId}`, { method: "DELETE" });
      await loadOperations();
      setStatus({ type: "success", text: "关键词监控已删除" });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function deletePublishTask(taskId: string) {
    setStatus({ type: "loading", text: "正在删除发布任务..." });
    try {
      await apiFetch(`/api/publish-tasks/${taskId}`, { method: "DELETE" });
      await loadOperations();
      setStatus({ type: "success", text: "发布任务已删除" });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function createAnalyticsSnapshot() {
    if (!requireSelectedAccount()) return;
    setStatus({ type: "loading", text: "正在采集账号快照..." });
    try {
      await apiFetch<{ snapshot: AnalyticsSnapshot }>("/api/analytics/snapshots", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ account_id: selectedAccountId })
      });
      await loadOperations();
      setStatus({ type: "success", text: "账号快照已保存" });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function loadProfileNotes(reset = false) {
    if (!requireSelectedAccount() || !profile?.user_id) return;
    setStatus({ type: "loading", text: reset ? "正在查询主页笔记..." : "正在加载下一页主页笔记..." });
    try {
      const data = await apiFetch<{ notes: SearchNote[]; cursor: string; has_more: boolean }>("/api/profile/notes", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          account_id: selectedAccountId,
          user_id: profile.user_id,
          cursor: reset || profileNotesUserId !== profile.user_id ? "" : profileCursor,
          xsec_source: "pc_user"
        })
      });
      setProfileNotes((current) =>
        reset || profileNotesUserId !== profile.user_id ? data.notes : [...current, ...data.notes]
      );
      setProfileCursor(data.cursor);
      setProfileHasMore(data.has_more);
      setProfileNotesUserId(profile.user_id);
      setStatus({ type: "success", text: `已加载 ${data.notes.length} 条主页笔记` });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  function updateNote(note: SearchNote) {
    const matcher = (item: SearchNote) => item.note_id === note.note_id && item.xsec_token === note.xsec_token;
    setSearchResults((current) => current.map((item) => (matcher(item) ? { ...item, ...note } : item)));
    setProfileNotes((current) => current.map((item) => (matcher(item) ? { ...item, ...note } : item)));
  }

  async function loadNoteDetail(note: SearchNote) {
    if (!requireSelectedAccount()) return;
    const key = `${note.note_id}-${note.xsec_token}`;
    setDetailLoadingIds((current) => Array.from(new Set([...current, key])));
    setStatus({ type: "loading", text: "正在按需加载笔记详情..." });
    try {
      const data = await apiFetch<{ note: SearchNote }>("/api/search/note-detail", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          account_id: selectedAccountId,
          note_url: note.note_url,
          note_id: note.note_id,
          xsec_token: note.xsec_token,
          xsec_source: note.xsec_source || "pc_search"
        })
      });
      updateNote(data.note);
      setStatus({ type: "success", text: "笔记详情已加载" });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    } finally {
      setDetailLoadingIds((current) => current.filter((item) => item !== key));
    }
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <h1>Spider XHS Publisher</h1>
          <p>本地多账号小红书运营工作台</p>
        </div>
        <div className={`status-pill ${status.type}`}>{status.type === "idle" ? "待命" : status.type}</div>
      </section>

      <nav className="tabs" aria-label="功能导航">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={activeTab === tab.key ? "active" : ""}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <section className="context-bar">
        <label>
          当前账号
          <select value={selectedAccountId} onChange={(event) => setSelectedAccountId(event.target.value)}>
            <option value="">未选择</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
        </label>
        {selectedAccount && (
          <div className="account-summary compact">
            <strong>{selectedAccount.name}</strong>
            <span>{selectedAccount.cookie_preview}</span>
            <span>状态：{selectedAccount.last_check_status || "未校验"}</span>
          </div>
        )}
      </section>

      {activeTab === "dashboard" && (
        <section className="layout">
          <section className="stats-grid">
            <div className="stat-card">
              <strong>{summary?.publish_pending || 0}</strong>
              <span>待发布任务</span>
            </div>
            <div className="stat-card">
              <strong>{summary?.publish_done || 0}</strong>
              <span>已发布记录</span>
            </div>
            <div className="stat-card">
              <strong>{summary?.monitor_enabled || 0}</strong>
              <span>启用监控</span>
            </div>
            <div className="stat-card">
              <strong>{summary?.search_result_total || 0}</strong>
              <span>监控结果</span>
            </div>
            <div className="stat-card">
              <strong>{summary?.analytics_snapshot_total || 0}</strong>
              <span>账号快照</span>
            </div>
          </section>
          <section className="panel">
            <div className="section-head">
              <h2>最近操作</h2>
              <button type="button" onClick={loadOperations}>刷新</button>
            </div>
            <div className="table-list">
              {(summary?.latest_logs || []).map((log) => (
                <div className="list-row" key={log.id}>
                  <strong>{log.message}</strong>
                  <span>{log.event_type}</span>
                  <span>{log.created_at}</span>
                </div>
              ))}
              {(!summary || summary.latest_logs.length === 0) && <p className="empty-state">暂无操作记录。</p>}
            </div>
          </section>
        </section>
      )}

      {activeTab === "accounts" && (
        <section className="panel narrow-panel">
          <h2>账号管理</h2>
          <form onSubmit={addAccount} className="stack">
            <label>
              账号名
              <input value={accountName} onChange={(event) => setAccountName(event.target.value)} required />
            </label>
            <label>
              Cookie
              <textarea
                value={accountCookies}
                onChange={(event) => setAccountCookies(event.target.value)}
                rows={6}
                required
              />
            </label>
            <button type="submit">保存账号</button>
          </form>
          <div className="button-row">
            <button type="button" onClick={checkAccount} disabled={!selectedAccountId}>
              校验当前账号
            </button>
            <button type="button" className="danger" onClick={deleteAccount} disabled={!selectedAccountId}>
              删除当前账号
            </button>
          </div>
        </section>
      )}

      {activeTab === "publish" && (
        <section className="layout two-panel-layout">
          <section className="panel publisher-panel">
            <h2>发布笔记</h2>
            <form onSubmit={publish} className="publisher-form">
              <label>
                标题
                <input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={60} required />
              </label>
              <label>
                正文
                <textarea value={desc} onChange={(event) => setDesc(event.target.value)} rows={7} />
              </label>
              <div className="two-col">
                <label>
                  话题
                  <input
                    value={topics}
                    onChange={(event) => setTopics(event.target.value)}
                    placeholder="用逗号分隔，如 太原, 钟楼街"
                  />
                </label>
                <label>
                  地点
                  <input value={location} onChange={(event) => setLocation(event.target.value)} />
                </label>
              </div>
              <div className="two-col">
                <label>
                  可见性
                  <select value={privacyType} onChange={(event) => setPrivacyType(event.target.value)}>
                    <option value="1">私密</option>
                    <option value="0">公开</option>
                  </select>
                </label>
                <label>
                  媒体类型
                  <select
                    value={mediaType}
                    onChange={(event) => {
                      setMediaType(event.target.value as "image" | "video");
                      setImages(null);
                      setVideo(null);
                    }}
                  >
                    <option value="image">图文</option>
                    <option value="video">视频</option>
                  </select>
                </label>
              </div>
              <label>
                计划日期
                <input type="date" value={taskDate} onChange={(event) => setTaskDate(event.target.value)} />
              </label>
              {mediaType === "image" ? (
                <label>
                  图片
                  <input type="file" accept="image/*" multiple onChange={(event) => setImages(event.target.files)} />
                </label>
              ) : (
                <label>
                  视频
                  <input type="file" accept="video/*" onChange={(event) => setVideo(event.target.files?.[0] || null)} />
                </label>
              )}
              <button type="submit" className="primary">
                发布
              </button>
              <button type="button" onClick={savePublishTask}>
                保存为发布任务
              </button>
            </form>
          </section>

          <aside className="panel topic-panel">
            <h2>话题搜索</h2>
            <form onSubmit={searchTopics} className="topic-search">
              <input value={topicKeyword} onChange={(event) => setTopicKeyword(event.target.value)} />
              <button type="submit" disabled={!selectedAccountId}>
                搜索
              </button>
            </form>
            <div className="topic-list">
              {topicResults.map((topic) => (
                <button key={topic.id || topic.name} type="button" onClick={() => addTopic(topic.name)}>
                  #{topic.name}
                </button>
              ))}
            </div>
          </aside>
        </section>
      )}

      {activeTab === "tasks" && (
        <section className="panel">
          <div className="section-head">
            <h2>发布任务</h2>
            <button type="button" onClick={loadOperations}>刷新</button>
          </div>
          <div className="table-list">
            {publishTasks.map((task) => (
              <div className="list-row" key={task.id}>
                <strong>{task.title}</strong>
                <span>{task.status}</span>
                <span>{task.scheduled_date || "未设日期"} · {task.media_type}</span>
                <span>{(task.topics || []).map((topic) => `#${topic}`).join(" ")}</span>
                {task.last_error && <span>{task.last_error}</span>}
                <div className="row-actions">
                  <button type="button" className="danger" onClick={() => deletePublishTask(task.id)}>删除</button>
                </div>
              </div>
            ))}
            {publishTasks.length === 0 && <p className="empty-state">还没有发布任务。可以在“发布笔记”里保存任务。</p>}
          </div>
        </section>
      )}

      {activeTab === "profile" && (
        <section className="layout two-panel-layout">
          <section className="panel">
            <h2>主页查询</h2>
            <div className="button-row">
              <button type="button" onClick={getSelfProfile} disabled={!selectedAccountId}>
                获取当前账号主页
              </button>
            </div>
            <form onSubmit={queryProfile} className="stack">
              <label>
                用户主页链接或 user_id
                <input
                  value={profileInput}
                  onChange={(event) => setProfileInput(event.target.value)}
                  placeholder="https://www.xiaohongshu.com/user/profile/..."
                />
              </label>
              <button type="submit" className="primary" disabled={!selectedAccountId}>
                查询主页
              </button>
            </form>
          </section>
          <ProfileCard
            profile={profile}
            onLoadNotes={() => loadProfileNotes(true)}
            canLoadNotes={Boolean(selectedAccountId && profile?.user_id)}
          />
          {profileNotes.length > 0 && (
            <section className="panel wide-panel">
              <div className="section-head">
                <h2>主页笔记</h2>
                <button type="button" onClick={() => loadProfileNotes(false)} disabled={!profileHasMore}>
                  {profileHasMore ? "加载下一页" : "没有更多"}
                </button>
              </div>
              <NoteResults notes={profileNotes} detailLoadingIds={detailLoadingIds} onLoadDetail={loadNoteDetail} />
            </section>
          )}
        </section>
      )}

      {activeTab === "search" && (
        <section className="panel">
          <h2>关键词查询</h2>
          <form onSubmit={searchNotes} className="search-form">
            <label>
              关键词
              <input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} required />
            </label>
            <label>
              数量
              <select value={searchCount} onChange={(event) => setSearchCount(event.target.value)}>
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
              </select>
            </label>
            <label>
              排序
              <select value={sortType} onChange={(event) => setSortType(event.target.value)}>
                <option value="0">综合</option>
                <option value="1">最新</option>
                <option value="2">最多点赞</option>
                <option value="3">最多评论</option>
                <option value="4">最多收藏</option>
              </select>
            </label>
            <label>
              类型
              <select value={noteType} onChange={(event) => setNoteType(event.target.value)}>
                <option value="0">不限</option>
                <option value="1">视频</option>
                <option value="2">图文</option>
              </select>
            </label>
            <label>
              时间
              <select value={noteTime} onChange={(event) => setNoteTime(event.target.value)}>
                <option value="0">不限</option>
                <option value="1">一天内</option>
                <option value="2">一周内</option>
                <option value="3">半年内</option>
              </select>
            </label>
            <button type="submit" className="primary" disabled={!selectedAccountId}>
              搜索笔记
            </button>
          </form>
          <NoteResults notes={searchResults} detailLoadingIds={detailLoadingIds} onLoadDetail={loadNoteDetail} />
        </section>
      )}

      {activeTab === "monitors" && (
        <section className="layout two-panel-layout">
          <section className="panel">
            <h2>关键词监控</h2>
            <form onSubmit={createMonitor} className="stack">
              <label>
                关键词
                <input value={monitorKeyword} onChange={(event) => setMonitorKeyword(event.target.value)} required />
              </label>
              <div className="two-col">
                <label>
                  数量
                  <select value={searchCount} onChange={(event) => setSearchCount(event.target.value)}>
                    <option value="10">10</option>
                    <option value="20">20</option>
                    <option value="50">50</option>
                  </select>
                </label>
                <label>
                  间隔分钟
                  <input value={monitorInterval} onChange={(event) => setMonitorInterval(event.target.value)} />
                </label>
              </div>
              <button type="submit" className="primary" disabled={!selectedAccountId}>保存监控</button>
            </form>
          </section>
          <section className="panel">
            <div className="section-head">
              <h2>监控列表</h2>
              <button type="button" onClick={loadOperations}>刷新</button>
            </div>
            <div className="table-list">
              {searchMonitors.map((monitor) => (
                <div className="list-row" key={monitor.id}>
                  <strong>{monitor.keyword}</strong>
                  <span>每 {monitor.interval_minutes} 分钟 · {monitor.enabled ? "启用" : "停用"}</span>
                  <span>{monitor.last_run_status || "未执行"} {monitor.last_run_message || ""}</span>
                  <div className="row-actions">
                    <button type="button" onClick={() => runMonitor(monitor.id)}>执行一次</button>
                    <button type="button" className="danger" onClick={() => deleteMonitor(monitor.id)}>删除</button>
                  </div>
                </div>
              ))}
              {searchMonitors.length === 0 && <p className="empty-state">还没有关键词监控。</p>}
            </div>
          </section>
          {savedSearchResults.length > 0 && (
            <section className="panel wide-panel">
              <h2>监控结果</h2>
              <NoteResults
                notes={savedSearchResults.map((item) => item.note)}
                detailLoadingIds={detailLoadingIds}
                onLoadDetail={loadNoteDetail}
              />
            </section>
          )}
        </section>
      )}

      {activeTab === "analytics" && (
        <section className="panel">
          <div className="section-head">
            <h2>账号分析</h2>
            <button type="button" className="primary" onClick={createAnalyticsSnapshot} disabled={!selectedAccountId}>
              采集当前账号快照
            </button>
          </div>
          <div className="table-list">
            {analyticsSnapshots.map((snapshot) => (
              <div className="list-row" key={snapshot.id}>
                <strong>{snapshot.profile?.nickname || "未知账号"}</strong>
                <span>粉丝 {snapshot.profile?.fans || 0} · 获赞收藏 {snapshot.profile?.interaction || 0}</span>
                <span>最近笔记 {snapshot.recent_notes?.length || 0} 条</span>
                <span>{snapshot.created_at}</span>
              </div>
            ))}
            {analyticsSnapshots.length === 0 && <p className="empty-state">还没有账号快照。</p>}
          </div>
        </section>
      )}

      {status.text && (
        <section className={`message ${status.type}`}>
          <pre>{status.text}</pre>
        </section>
      )}
    </main>
  );
}

function NoteResults({
  notes,
  detailLoadingIds,
  onLoadDetail
}: {
  notes: SearchNote[];
  detailLoadingIds: string[];
  onLoadDetail: (note: SearchNote) => void;
}) {
  return (
    <div className="results-grid">
      {notes.map((note) => {
        const detailLoaded = Boolean(note.desc || note.upload_time || note.video_addr || (note.image_list || []).length > 0);
        const key = `${note.note_id}-${note.xsec_token}`;
        return (
          <article className="note-card" key={key}>
            <div className="note-header">
              {note.cover && <img src={mediaProxyUrl(note.cover)} alt={note.title} />}
              <div>
                <h3>{note.title}</h3>
                <p>{note.nickname || "未知作者"} · {note.note_type || "笔记"}</p>
                {note.upload_time && <p>发布时间：{note.upload_time}</p>}
                <p>赞 {note.liked_count || 0} · 藏 {note.collected_count || 0} · 评 {note.comment_count || 0}</p>
              </div>
            </div>
            {note.desc && <p className="note-desc">{note.desc}</p>}
            {(note.image_list || []).length > 0 && (
              <div className="note-media-grid">
                {(note.image_list || []).map((imageUrl, index) => (
                  <img
                    key={`${note.note_id}-image-${index}`}
                    src={mediaProxyUrl(imageUrl)}
                    alt={`${note.title} 图片 ${index + 1}`}
                    loading="lazy"
                  />
                ))}
              </div>
            )}
            {note.video_addr && (
              <video className="note-video" controls preload="metadata" src={mediaProxyUrl(note.video_addr)} />
            )}
            <div className="note-actions">
              <button type="button" onClick={() => onLoadDetail(note)} disabled={detailLoadingIds.includes(key)}>
                {detailLoaded ? "刷新详情" : "加载详情"}
              </button>
              {detailLoaded && note.note_url ? (
                <a href={note.note_url} target="_blank" rel="noreferrer">
                  打开笔记
                </a>
              ) : (
                <span>加载详情后可打开</span>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}

function ProfileCard({
  profile,
  onLoadNotes,
  canLoadNotes
}: {
  profile: Profile | null;
  onLoadNotes: () => void;
  canLoadNotes: boolean;
}) {
  if (!profile) {
    return (
      <section className="panel empty-state">
        <h2>主页资料</h2>
        <p>查询后会在这里显示头像、昵称、主页链接和基础指标。</p>
      </section>
    );
  }
  return (
    <section className="panel profile-card">
      <div className="profile-head">
        {profile.avatar && <img src={profile.avatar} alt={profile.nickname} />}
        <div>
          <h2>{profile.nickname || "未知用户"}</h2>
          <p>小红书号：{profile.red_id || "未知"}</p>
          {profile.home_url && (
            <a href={profile.home_url} target="_blank" rel="noreferrer">
              打开主页
            </a>
          )}
        </div>
      </div>
      <p>{profile.desc || "暂无简介"}</p>
      <div className="metric-grid">
        <span>关注 {profile.follows || 0}</span>
        <span>粉丝 {profile.fans || 0}</span>
        <span>获赞收藏 {profile.interaction || 0}</span>
        <span>{profile.gender || "未知"} · {profile.ip_location || "未知"}</span>
      </div>
      <button type="button" className="primary" onClick={onLoadNotes} disabled={!canLoadNotes}>
        查询主页笔记
      </button>
      {profile.tags.length > 0 && (
        <div className="topic-list">
          {profile.tags.map((tag) => (
            <span key={tag}>#{tag}</span>
          ))}
        </div>
      )}
    </section>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
