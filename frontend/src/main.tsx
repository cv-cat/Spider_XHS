import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BarChart3,
  CalendarCheck,
  Languages,
  LayoutDashboard,
  LineChart,
  Search,
  Send,
  ShieldCheck,
  UserRound
} from "lucide-react";
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

type PublishHistoryItem = {
  id: string;
  account_id: string;
  title: string;
  desc: string;
  topics: string[];
  location?: string;
  privacy_type?: number;
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

type ExternalPublishConfig = {
  api_key_preview: string;
  has_api_key: boolean;
  base_url: string;
  endpoint: string;
  updated_at?: string | null;
};

type ExternalPublishRecord = {
  id: string;
  title: string;
  note_type: string;
  response: { data?: { id?: string; url?: string; qrcode?: string }; success?: boolean };
  created_at: string;
};

type Status = {
  type: "idle" | "loading" | "success" | "error";
  text: string;
};

type ApiValidationError = {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
};

type Lang = "zh" | "en";
type TabKey = "dashboard" | "accounts" | "publish" | "tasks" | "profile" | "search" | "monitors" | "analytics";

const initialStatus: Status = { type: "idle", text: "" };
const tabs: Array<{ key: TabKey; zh: string; en: string }> = [
  { key: "dashboard", zh: "运营概览", en: "Dashboard" },
  { key: "accounts", zh: "账号管理", en: "Accounts" },
  { key: "publish", zh: "发布笔记", en: "Publish" },
  { key: "tasks", zh: "发布历史", en: "History" },
  { key: "profile", zh: "主页查询", en: "Profiles" },
  { key: "search", zh: "关键词查询", en: "Search" },
  { key: "monitors", zh: "关键词监控", en: "Monitors" },
  { key: "analytics", zh: "账号分析", en: "Analytics" }
];

const tabIcons: Record<TabKey, React.ComponentType<{ "aria-hidden"?: boolean }>> = {
  dashboard: LayoutDashboard,
  accounts: ShieldCheck,
  publish: Send,
  tasks: CalendarCheck,
  profile: UserRound,
  search: Search,
  monitors: LineChart,
  analytics: BarChart3
};

const labels = {
  zh: {
    appTitle: "Spider XHS Publisher",
    appSubtitle: "本地多账号小红书运营工作台",
    language: "语言",
    currentAccount: "当前账号",
    standby: "待命",
    qrPublish: "扫码发布",
    apiConfig: "API Key 配置",
    apiKey: "API Key",
    saveConfig: "保存配置",
    noteType: "笔记类型",
    imageNote: "图文",
    videoNote: "视频",
    title: "标题",
    content: "正文",
    imageUrls: "图片 URL",
    videoUrl: "视频 URL",
    coverUrl: "封面 URL",
    localMedia: "本地上传",
    urlMedia: "链接",
    mediaSource: "媒体来源",
    directPublish: "直接发布",
    localPublishTip: "本地文件用于直接发布；扫码发布需要可公开访问的图片/视频 URL。",
    generateQr: "生成二维码",
    qrResult: "二维码结果",
    openSharePage: "打开分享页",
    records: "调用记录"
  },
  en: {
    appTitle: "Spider XHS Publisher",
    appSubtitle: "Local multi-account XHS operations console",
    language: "Language",
    currentAccount: "Account",
    standby: "Idle",
    qrPublish: "QR Publish",
    apiConfig: "API Key Config",
    apiKey: "API Key",
    saveConfig: "Save Config",
    noteType: "Type",
    imageNote: "Image Note",
    videoNote: "Video Note",
    title: "Title",
    content: "Content",
    imageUrls: "Image URLs",
    videoUrl: "Video URL",
    coverUrl: "Cover URL",
    localMedia: "Local Upload",
    urlMedia: "URL",
    mediaSource: "Media Source",
    directPublish: "Direct Publish",
    localPublishTip: "Local files are used for direct publish. QR publish requires public image/video URLs.",
    generateQr: "Generate QR Code",
    qrResult: "QR Result",
    openSharePage: "Open Share Page",
    records: "Records"
  }
};

function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const error = item as ApiValidationError;
          const field = (error.loc || []).filter((part) => part !== "body").join(".");
          return [field, error.msg].filter(Boolean).join(": ");
        }
        return String(item);
      })
      .filter(Boolean)
      .join("\n");
  }
  if (detail && typeof detail === "object") {
    return JSON.stringify(detail, null, 2);
  }
  return fallback;
}

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();
  if (!response.ok) {
    const detail = typeof body === "object" && body && "detail" in body ? body.detail : body;
    throw new Error(formatApiError(detail, response.statusText));
  }
  return body as T;
}

function extractTopicsFromText(value: string): string[] {
  const matches = value.matchAll(/#([^#\s，,。.！!？?\n\r]+)/g);
  return Array.from(new Set(Array.from(matches).map((match) => match[1].trim()).filter(Boolean)));
}

function appendTopicsToContent(value: string, topicList: string[]): string {
  const existing = extractTopicsFromText(value);
  const missing = topicList.filter((topic) => !existing.includes(topic));
  if (missing.length === 0) return value;
  const suffix = missing.map((topic) => `#${topic}`).join(" ");
  return [value.trim(), suffix].filter(Boolean).join("\n\n");
}

function mediaProxyUrl(url?: string): string {
  return url ? `/api/media/proxy?url=${encodeURIComponent(url)}` : "";
}

function App() {
  const [lang, setLang] = useState<Lang>("zh");
  const [activeTab, setActiveTab] = useState<TabKey>("dashboard");
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState("");
  const [accountName, setAccountName] = useState("");
  const [accountCookies, setAccountCookies] = useState("");
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [location, setLocation] = useState("");
  const [privacyType, setPrivacyType] = useState("1");
  const [mediaType, setMediaType] = useState<"image" | "video">("image");
  const [mediaSource, setMediaSource] = useState<"local" | "url">("local");
  const [images, setImages] = useState<FileList | null>(null);
  const [video, setVideo] = useState<File | null>(null);
  const [imageUrls, setImageUrls] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [coverUrl, setCoverUrl] = useState("");
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
  const [publishHistory, setPublishHistory] = useState<PublishHistoryItem[]>([]);
  const [searchMonitors, setSearchMonitors] = useState<SearchMonitor[]>([]);
  const [monitorKeyword, setMonitorKeyword] = useState("");
  const [monitorInterval, setMonitorInterval] = useState("60");
  const [savedSearchResults, setSavedSearchResults] = useState<SavedSearchResult[]>([]);
  const [analyticsSnapshots, setAnalyticsSnapshots] = useState<AnalyticsSnapshot[]>([]);
  const [externalConfig, setExternalConfig] = useState<ExternalPublishConfig | null>(null);
  const [externalApiKey, setExternalApiKey] = useState("");
  const [externalQr, setExternalQr] = useState("");
  const [externalUrl, setExternalUrl] = useState("");
  const [externalRecords, setExternalRecords] = useState<ExternalPublishRecord[]>([]);
  const [status, setStatus] = useState<Status>(initialStatus);
  const text = labels[lang];

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
    const [summaryData, historyData, monitorsData, resultsData, snapshotsData, externalConfigData, externalRecordsData] = await Promise.all([
      apiFetch<{ summary: OperationSummary }>("/api/ops/summary"),
      apiFetch<{ items: PublishHistoryItem[] }>("/api/publish-history"),
      apiFetch<{ monitors: SearchMonitor[] }>("/api/search-monitors"),
      apiFetch<{ results: SavedSearchResult[] }>("/api/search-results"),
      apiFetch<{ snapshots: AnalyticsSnapshot[] }>("/api/analytics/snapshots"),
      apiFetch<{ config: ExternalPublishConfig }>("/api/external-publish/config"),
      apiFetch<{ records: ExternalPublishRecord[] }>("/api/external-publish/records")
    ]);
    setSummary(summaryData.summary);
    setPublishHistory(historyData.items);
    setSearchMonitors(monitorsData.monitors);
    setSavedSearchResults(resultsData.results);
    setAnalyticsSnapshots(snapshotsData.snapshots);
    setExternalConfig(externalConfigData.config);
    setExternalRecords(externalRecordsData.records);
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

  async function publish(event: FormEvent) {
    event.preventDefault();
    if (!requireSelectedAccount()) return;
    const formData = new FormData();
    formData.append("account_id", selectedAccountId);
    formData.append("title", title);
    formData.append("desc", desc);
    formData.append("topics", JSON.stringify(extractTopicsFromText(desc)));
    formData.append("location", location);
    formData.append("privacy_type", privacyType);
    formData.append("media_type", mediaType);
    if (mediaSource !== "local") {
      setStatus({ type: "error", text: "直接发布需要选择本地上传文件；链接媒体请使用扫码发布" });
      return;
    }
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
    const intervalMinutes = Number(monitorInterval);
    if (!Number.isFinite(intervalMinutes) || intervalMinutes < 5) {
      setStatus({ type: "error", text: "监控间隔不能小于 5 分钟" });
      return;
    }
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
          interval_minutes: intervalMinutes,
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

  async function deletePublishHistoryItem(taskId: string) {
    setStatus({ type: "loading", text: "正在删除发布历史..." });
    try {
      await apiFetch(`/api/publish-tasks/${taskId}`, { method: "DELETE" });
      await loadOperations();
      setStatus({ type: "success", text: "发布历史已删除" });
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
    const matcher = (item: SearchNote) =>
      Boolean(note.note_id && item.note_id === note.note_id) ||
      Boolean(note.note_url && item.note_url === note.note_url);
    setSearchResults((current) => current.map((item) => (matcher(item) ? { ...item, ...note } : item)));
    setProfileNotes((current) => current.map((item) => (matcher(item) ? { ...item, ...note } : item)));
    setSavedSearchResults((current) =>
      current.map((item) => (matcher(item.note) ? { ...item, note: { ...item.note, ...note } } : item))
    );
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

  async function saveExternalConfig(event: FormEvent) {
    event.preventDefault();
    setStatus({ type: "loading", text: lang === "zh" ? "正在保存 API Key..." : "Saving API Key..." });
    try {
      await apiFetch<{ config: ExternalPublishConfig }>("/api/external-publish/config", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          api_key: externalApiKey,
          base_url: externalConfig?.base_url || "https://www.myaibot.vip",
          endpoint: externalConfig?.endpoint || "/api/rednote/publish-with-upload"
        })
      });
      setExternalApiKey("");
      await loadOperations();
      setStatus({ type: "success", text: lang === "zh" ? "API Key 已保存" : "API Key saved" });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function generateExternalQr(event?: FormEvent) {
    event?.preventDefault();
    if (!requireSelectedAccount()) return;
    if (mediaSource !== "url") {
      setStatus({ type: "error", text: lang === "zh" ? "扫码发布需要选择链接媒体，并填写公网可访问的 URL" : "QR publish requires URL media with public URLs" });
      return;
    }
    setStatus({ type: "loading", text: lang === "zh" ? "正在生成二维码..." : "Generating QR code..." });
    try {
      const extractedTopics = extractTopicsFromText(desc);
      const data = await apiFetch<{ result: { qrcode?: string; url?: string; id?: string } }>("/api/external-publish/qrcode", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          account_id: selectedAccountId,
          type: mediaType === "image" ? "normal" : "video",
          title,
          content: appendTopicsToContent(desc, extractedTopics),
          images: imageUrls.split(/[\n,，]/).map((item) => item.trim()).filter(Boolean),
          video: videoUrl.trim(),
          cover: coverUrl.trim(),
          use_upload_endpoint: true
        })
      });
      setExternalQr(data.result.qrcode || "");
      setExternalUrl(data.result.url || "");
      await loadOperations();
      setStatus({ type: "success", text: lang === "zh" ? "二维码已生成" : "QR code generated" });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  function reusePublishHistoryItem(task: PublishHistoryItem) {
    setTitle(task.title || "");
    setDesc(task.desc || "");
    setLocation(task.location || "");
    setPrivacyType(String(task.privacy_type ?? 1));
    setMediaType(task.media_type === "video" ? "video" : "image");
    setImages(null);
    setVideo(null);
    if ((task.media_names || []).some((item) => /^https?:\/\//i.test(item))) {
      setMediaSource("url");
      if (task.media_type === "video") {
        setVideoUrl(task.media_names[0] || "");
        setImageUrls("");
      } else {
        setImageUrls((task.media_names || []).join("\n"));
        setVideoUrl("");
      }
    } else {
      setMediaSource("local");
      setImageUrls("");
      setVideoUrl("");
    }
    setCoverUrl("");
    setActiveTab("publish");
    setStatus({ type: "success", text: "已带入发布内容，可在发布页继续编辑" });
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <h1>{text.appTitle}</h1>
          <p>{text.appSubtitle}</p>
        </div>
        <div className="topbar-actions">
          <label>
            <span className="inline-flex items-center gap-1.5">
              <Languages aria-hidden />
              {text.language}
            </span>
            <select value={lang} onChange={(event) => setLang(event.target.value as Lang)}>
              <option value="zh">中文</option>
              <option value="en">English</option>
            </select>
          </label>
          <div className={`status-pill ${status.type}`}>{status.type === "idle" ? text.standby : status.type}</div>
        </div>
      </section>

      <nav className="tabs" aria-label="功能导航">
        {tabs.map((tab) => {
          const Icon = tabIcons[tab.key];
          return (
            <button
              key={tab.key}
              type="button"
              className={activeTab === tab.key ? "active" : ""}
              onClick={() => setActiveTab(tab.key)}
            >
              <Icon aria-hidden />
              {tab[lang]}
            </button>
          );
        })}
      </nav>

      <section className="context-bar">
        <label>
          {text.currentAccount}
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
              <strong>{summary?.publish_total || 0}</strong>
              <span>发布历史</span>
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
              <label>
                地点
                <input value={location} onChange={(event) => setLocation(event.target.value)} />
              </label>
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
                      setImageUrls("");
                      setVideoUrl("");
                      setCoverUrl("");
                    }}
                  >
                    <option value="image">图文</option>
                    <option value="video">视频</option>
                  </select>
                </label>
              </div>
              <label>
                {text.mediaSource}
                <select value={mediaSource} onChange={(event) => setMediaSource(event.target.value as "local" | "url")}>
                  <option value="local">{text.localMedia}</option>
                  <option value="url">{text.urlMedia}</option>
                </select>
              </label>
              {mediaSource === "local" ? (
                mediaType === "image" ? (
                  <label>
                    图片
                    <input type="file" accept="image/*" multiple onChange={(event) => setImages(event.target.files)} />
                  </label>
                ) : (
                  <label>
                    视频
                    <input type="file" accept="video/*" onChange={(event) => setVideo(event.target.files?.[0] || null)} />
                  </label>
                )
              ) : (
                mediaType === "image" ? (
                  <label>
                    {text.imageUrls}
                    <textarea
                      value={imageUrls}
                      onChange={(event) => setImageUrls(event.target.value)}
                      rows={5}
                      placeholder="https://example.com/1.jpg&#10;https://example.com/2.jpg"
                    />
                  </label>
                ) : (
                  <>
                    <label>
                      {text.videoUrl}
                      <input value={videoUrl} onChange={(event) => setVideoUrl(event.target.value)} />
                    </label>
                    <label>
                      {text.coverUrl}
                      <input value={coverUrl} onChange={(event) => setCoverUrl(event.target.value)} />
                    </label>
                  </>
                )
              )}
              <p className="empty-state">{text.localPublishTip}</p>
              <button type="submit" className="primary">
                {text.directPublish}
              </button>
              <button type="button" onClick={() => generateExternalQr()} disabled={!selectedAccountId || !externalConfig?.has_api_key || mediaSource !== "url"}>
                {text.generateQr}
              </button>
            </form>
          </section>

          <aside className="panel topic-panel">
            <h2>{text.apiConfig}</h2>
            <form onSubmit={saveExternalConfig} className="stack">
              <label>
                {text.apiKey}
                <input
                  value={externalApiKey}
                  onChange={(event) => setExternalApiKey(event.target.value)}
                  placeholder={externalConfig?.has_api_key ? externalConfig.api_key_preview : "sk-..."}
                />
              </label>
              <p className="empty-state">
                {externalConfig?.has_api_key
                  ? `${lang === "zh" ? "已保存" : "Saved"}：${externalConfig.api_key_preview}`
                  : lang === "zh" ? "尚未保存 API Key" : "No API Key saved"}
              </p>
              <button type="submit" className="primary">{text.saveConfig}</button>
            </form>
          </aside>
          {(externalQr || externalRecords.length > 0) && (
            <section className="panel wide-panel">
              <div className="section-head">
                <h2>{text.qrResult}</h2>
                {externalUrl && <a href={externalUrl} target="_blank" rel="noreferrer">{text.openSharePage}</a>}
              </div>
              {externalQr && (
                <div className="qr-result">
                  <img src={externalQr} alt="XHS publish QR code" />
                </div>
              )}
              <div className="table-list">
                {externalRecords.slice(0, 5).map((record) => (
                  <div className="list-row" key={record.id}>
                    <strong>{record.title || "Untitled"}</strong>
                    <span>{record.note_type} · {record.created_at}</span>
                    {record.response?.data?.url && (
                      <a href={record.response.data.url} target="_blank" rel="noreferrer">{text.openSharePage}</a>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}
        </section>
      )}

      {activeTab === "tasks" && (
        <section className="panel">
          <div className="section-head">
            <h2>发布历史</h2>
            <button type="button" onClick={loadOperations}>刷新</button>
          </div>
          <div className="table-list">
            {publishHistory.map((task) => (
              <div className="list-row" key={task.id}>
                <strong>{task.title}</strong>
                <span>{task.status}</span>
                <span>{task.created_at} · {task.media_type}</span>
                <span>{(task.topics || []).map((topic) => `#${topic}`).join(" ")}</span>
                {task.last_error && <span>{task.last_error}</span>}
                <div className="row-actions">
                  <button type="button" onClick={() => reusePublishHistoryItem(task)}>带入发布</button>
                  <button type="button" className="danger" onClick={() => deletePublishHistoryItem(task.id)}>删除</button>
                </div>
              </div>
            ))}
            {publishHistory.length === 0 && <p className="empty-state">还没有发布历史。成功发布或生成二维码后会记录在这里。</p>}
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
                  <input
                    type="number"
                    min="5"
                    max="1440"
                    value={monitorInterval}
                    onChange={(event) => setMonitorInterval(event.target.value)}
                  />
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
  const [expandedDescKeys, setExpandedDescKeys] = useState<string[]>([]);
  const [viewer, setViewer] = useState<{ images: string[]; index: number; title: string } | null>(null);

  function toggleDesc(key: string) {
    setExpandedDescKeys((current) =>
      current.includes(key) ? current.filter((item) => item !== key) : [...current, key]
    );
  }

  function openViewer(images: string[], index: number, title: string) {
    setViewer({ images, index, title });
  }

  function closeViewer() {
    setViewer(null);
  }

  function shiftViewer(direction: number) {
    setViewer((current) => {
      if (!current || current.images.length <= 1) return current;
      const nextIndex = (current.index + direction + current.images.length) % current.images.length;
      return { ...current, index: nextIndex };
    });
  }

  useEffect(() => {
    if (!viewer) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") closeViewer();
      if (event.key === "ArrowLeft") shiftViewer(-1);
      if (event.key === "ArrowRight") shiftViewer(1);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [viewer]);

  return (
    <>
      <div className="results-grid">
        {notes.map((note) => {
          const detailLoaded = Boolean(note.desc || note.upload_time || note.video_addr || (note.image_list || []).length > 0);
          const key = `${note.note_id}-${note.xsec_token}`;
          const descExpanded = expandedDescKeys.includes(key);
          const canToggleDesc = (note.desc || "").length > 140;
          const noteImages = (note.image_list || []).filter(Boolean);
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
              {note.desc && (
                <div className="note-desc-wrap">
                  <p className={descExpanded ? "note-desc expanded" : "note-desc"}>{note.desc}</p>
                  {canToggleDesc && (
                    <button type="button" className="text-button" onClick={() => toggleDesc(key)}>
                      {descExpanded ? "收起" : "展开"}
                    </button>
                  )}
                </div>
              )}
              {noteImages.length > 0 && (
                <div className="note-media-grid">
                  {noteImages.map((imageUrl, index) => (
                    <button
                      type="button"
                      className="note-image-button"
                      key={`${note.note_id}-image-${index}`}
                      onClick={() => openViewer(noteImages, index, note.title)}
                    >
                      <img
                        src={mediaProxyUrl(imageUrl)}
                        alt={`${note.title} 图片 ${index + 1}`}
                        loading="lazy"
                      />
                    </button>
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
      {viewer && (
        <div className="image-viewer" role="dialog" aria-modal="true" aria-label="图片查看器" onClick={closeViewer}>
          <div className="image-viewer-inner" onClick={(event) => event.stopPropagation()}>
            <div className="image-viewer-head">
              <span>{viewer.title || "图片"} · {viewer.index + 1}/{viewer.images.length}</span>
              <button type="button" onClick={closeViewer}>关闭</button>
            </div>
            <div className="image-viewer-stage">
              {viewer.images.length > 1 && (
                <button type="button" className="image-viewer-nav left" onClick={() => shiftViewer(-1)} aria-label="上一张">
                  ‹
                </button>
              )}
              <img src={mediaProxyUrl(viewer.images[viewer.index])} alt={`${viewer.title} 大图 ${viewer.index + 1}`} />
              {viewer.images.length > 1 && (
                <button type="button" className="image-viewer-nav right" onClick={() => shiftViewer(1)} aria-label="下一张">
                  ›
                </button>
              )}
            </div>
            {viewer.images.length > 1 && (
              <div className="image-viewer-thumbs">
                {viewer.images.map((imageUrl, index) => (
                  <button
                    type="button"
                    key={`${imageUrl}-${index}`}
                    className={index === viewer.index ? "active" : ""}
                    onClick={() => setViewer((current) => current ? { ...current, index } : current)}
                  >
                    <img src={mediaProxyUrl(imageUrl)} alt={`缩略图 ${index + 1}`} />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
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
