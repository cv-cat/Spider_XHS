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

type Status = {
  type: "idle" | "loading" | "success" | "error";
  text: string;
};

const initialStatus: Status = { type: "idle", text: "" };

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

function App() {
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

  useEffect(() => {
    loadAccounts().catch((error) => setStatus({ type: "error", text: error.message }));
  }, []);

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
    if (!selectedAccountId) return;
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
    if (!selectedAccountId) return;
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
    if (!selectedAccountId || !topicKeyword.trim()) return;
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
    if (!selectedAccountId) {
      setStatus({ type: "error", text: "请先选择账号" });
      return;
    }
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
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <h1>Spider XHS Publisher</h1>
          <p>本地多账号小红书创作者发布台</p>
        </div>
        <div className={`status-pill ${status.type}`}>{status.type === "idle" ? "待命" : status.type}</div>
      </section>

      <section className="layout">
        <aside className="panel account-panel">
          <h2>账号</h2>
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
                rows={5}
                required
              />
            </label>
            <button type="submit">保存账号</button>
          </form>

          <div className="divider" />
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
            <div className="account-summary">
              <strong>{selectedAccount.name}</strong>
              <span>{selectedAccount.cookie_preview}</span>
              <span>状态：{selectedAccount.last_check_status || "未校验"}</span>
            </div>
          )}
          <div className="button-row">
            <button type="button" onClick={checkAccount} disabled={!selectedAccountId}>
              校验
            </button>
            <button type="button" className="danger" onClick={deleteAccount} disabled={!selectedAccountId}>
              删除
            </button>
          </div>
        </aside>

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

      {status.text && (
        <section className={`message ${status.type}`}>
          <pre>{status.text}</pre>
        </section>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
