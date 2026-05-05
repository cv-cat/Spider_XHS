import React, { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BarChart3,
  CalendarCheck,
  Languages,
  LayoutDashboard,
  LineChart,
  QrCode,
  Search,
  Send,
  ShieldCheck,
  Smartphone,
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

type LoginPlatform = "pc";

type LoginQrSession = {
  session_id: string;
  platform: LoginPlatform;
  qr_url: string;
  qr_image: string;
  expires_in_seconds: number;
  msg: string;
};

type LoginQrCheckResult = {
  status: "pending" | "waiting_scan" | "confirm" | "success" | "expired" | "error";
  msg: string;
  account?: Account | null;
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
    records: "调用记录",
    notSelected: "未选择",
    statusLabel: "状态",
    unchecked: "未校验",
    refresh: "刷新",
    dashboardPublishHistory: "发布历史",
    dashboardPublished: "已发布记录",
    enabledMonitors: "启用监控",
    monitorResults: "监控结果",
    accountSnapshots: "账号快照",
    recentOps: "最近操作",
    noOps: "暂无操作记录。",
    pcQrLogin: "PC 扫码登录",
    pcQrLoginDesc: "用于搜索、主页查询、关键词监控和账号分析。",
    recommended: "推荐",
    accountName: "账号名",
    autoNameAfterLogin: "可留空，登录成功后自动取昵称",
    generateLoginQr: "生成二维码",
    checkStatus: "检查状态",
    scanQrAlt: "小红书登录二维码",
    scanQrConfirm: "请使用小红书 App 扫码，并在手机端确认登录。",
    scanQrUsage: "扫码保存的 Cookie 用于搜索、主页查询、关键词监控和账号分析。",
    qrExpires: "二维码约 {seconds} 秒内有效。",
    manualCookie: "手动 Cookie",
    manualCookieDesc: "备用入口。账号名可留空，保存时会尝试自动获取昵称。",
    autoNameAfterSave: "可留空，保存成功后自动取昵称",
    saveAccount: "保存账号",
    accountTools: "当前账号",
    noAccount: "尚未选择账号。",
    checkAccount: "校验账号",
    deleteAccount: "删除账号",
    location: "地点",
    visibility: "可见性",
    private: "私密",
    public: "公开",
    mediaType: "媒体类型",
    image: "图片",
    video: "视频",
    saved: "已保存",
    noApiKey: "尚未保存 API Key",
    publishHistory: "发布历史",
    reusePublish: "带入发布",
    delete: "删除",
    noPublishHistory: "还没有发布历史。成功发布或生成二维码后会记录在这里。",
    profileQuery: "主页查询",
    getSelfProfile: "获取当前账号主页",
    profileInput: "用户主页链接或 user_id",
    queryProfile: "查询主页",
    profileNotes: "主页笔记",
    loadNextPage: "加载下一页",
    noMore: "没有更多",
    keywordSearch: "关键词查询",
    keyword: "关键词",
    count: "数量",
    sort: "排序",
    comprehensive: "综合",
    latest: "最新",
    mostLiked: "最多点赞",
    mostCommented: "最多评论",
    mostCollected: "最多收藏",
    type: "类型",
    unlimited: "不限",
    time: "时间",
    oneDay: "一天内",
    oneWeek: "一周内",
    halfYear: "半年内",
    searchNotes: "搜索笔记",
    keywordMonitor: "关键词监控",
    intervalMinutes: "间隔分钟",
    saveMonitor: "保存监控",
    monitorList: "监控列表",
    everyMinutes: "每 {minutes} 分钟",
    enabled: "启用",
    disabled: "停用",
    notRun: "未执行",
    runOnce: "执行一次",
    noMonitors: "还没有关键词监控。",
    analytics: "账号分析",
    collectSnapshot: "采集当前账号快照",
    unknownAccount: "未知账号",
    fans: "粉丝",
    likesCollects: "获赞收藏",
    recentNotesCount: "最近笔记 {count} 条",
    noSnapshots: "还没有账号快照。",
    unknownAuthor: "未知作者",
    note: "笔记",
    publishTime: "发布时间",
    likeShort: "赞",
    collectShort: "藏",
    commentShort: "评",
    collapse: "收起",
    expand: "展开",
    refreshDetail: "刷新详情",
    loadDetail: "加载详情",
    openNote: "打开笔记",
    openAfterDetail: "加载详情后可打开",
    imageViewer: "图片查看器",
    picture: "图片",
    close: "关闭",
    previousImage: "上一张",
    nextImage: "下一张",
    thumbnail: "缩略图",
    largeImage: "大图",
    profileData: "主页资料",
    profileEmpty: "查询后会在这里显示头像、昵称、主页链接和基础指标。",
    unknownUser: "未知用户",
    redId: "小红书号",
    unknown: "未知",
    openProfile: "打开主页",
    noBio: "暂无简介",
    follows: "关注",
    queryProfileNotes: "查询主页笔记",
    selectAccountRequired: "请先选择账号",
    savingAccount: "正在保存账号...",
    accountSaved: "账号已保存",
    generatingLoginQr: "正在生成登录二维码...",
    loginQrReady: "二维码已生成，请用小红书 App 扫码",
    checkingLogin: "正在检查扫码状态...",
    qrLoginSaved: "扫码登录成功，账号已保存",
    qrExpired: "二维码已过期",
    deletingAccount: "正在删除账号...",
    accountDeleted: "账号已删除",
    checkingCookie: "正在校验 Cookie...",
    localPublishOnly: "直接发布需要选择本地上传文件；链接媒体请使用扫码发布",
    publishing: "正在校验账号并发布...",
    loadingSelfProfile: "正在获取当前账号主页...",
    profileLoaded: "主页资料获取成功",
    queryingProfile: "正在查询主页...",
    searchingNotes: "正在搜索笔记...",
    searchDone: "找到 {count} 条笔记。为降低请求频率，正文和媒体请按需加载。",
    monitorIntervalInvalid: "监控间隔不能小于 5 分钟",
    savingMonitor: "正在保存关键词监控...",
    monitorSaved: "关键词监控已保存",
    runningMonitor: "正在执行关键词监控...",
    monitorDone: "监控完成，返回 {returned} 条，新增 {saved} 条",
    deletingMonitor: "正在删除关键词监控...",
    monitorDeleted: "关键词监控已删除",
    deletingHistory: "正在删除发布历史...",
    historyDeleted: "发布历史已删除",
    collectingSnapshot: "正在采集账号快照...",
    snapshotSaved: "账号快照已保存",
    loadingProfileNotes: "正在查询主页笔记...",
    loadingMoreProfileNotes: "正在加载下一页主页笔记...",
    profileNotesLoaded: "已加载 {count} 条主页笔记",
    loadingNoteDetail: "正在按需加载笔记详情...",
    noteDetailLoaded: "笔记详情已加载",
    savingApiKey: "正在保存 API Key...",
    apiKeySaved: "API Key 已保存",
    qrPublishNeedsUrl: "扫码发布需要选择链接媒体，并填写公网可访问的 URL",
    generatingQr: "正在生成二维码...",
    qrGenerated: "二维码已生成",
    publishReused: "已带入发布内容，可在发布页继续编辑"
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
    records: "Records",
    notSelected: "Not selected",
    statusLabel: "Status",
    unchecked: "Unchecked",
    refresh: "Refresh",
    dashboardPublishHistory: "Publish history",
    dashboardPublished: "Published records",
    enabledMonitors: "Enabled monitors",
    monitorResults: "Monitor results",
    accountSnapshots: "Account snapshots",
    recentOps: "Recent activity",
    noOps: "No activity yet.",
    pcQrLogin: "PC QR Login",
    pcQrLoginDesc: "Used for search, profile lookup, keyword monitors, and account analytics.",
    recommended: "Recommended",
    accountName: "Account name",
    autoNameAfterLogin: "Optional. Nickname is fetched after login.",
    generateLoginQr: "Generate QR Code",
    checkStatus: "Check Status",
    scanQrAlt: "XHS login QR code",
    scanQrConfirm: "Scan with the XHS app and confirm login on your phone.",
    scanQrUsage: "The saved cookie is used for search, profile lookup, keyword monitors, and analytics.",
    qrExpires: "QR code expires in about {seconds} seconds.",
    manualCookie: "Manual Cookie",
    manualCookieDesc: "Fallback entry. Account name is optional; the backend will try to fetch the nickname.",
    autoNameAfterSave: "Optional. Nickname is fetched after saving.",
    saveAccount: "Save Account",
    accountTools: "Current Account",
    noAccount: "No account selected.",
    checkAccount: "Check Account",
    deleteAccount: "Delete Account",
    location: "Location",
    visibility: "Visibility",
    private: "Private",
    public: "Public",
    mediaType: "Media Type",
    image: "Image",
    video: "Video",
    saved: "Saved",
    noApiKey: "No API Key saved",
    publishHistory: "Publish History",
    reusePublish: "Reuse",
    delete: "Delete",
    noPublishHistory: "No publish history yet. Successful publishes and generated QR codes will appear here.",
    profileQuery: "Profile Lookup",
    getSelfProfile: "Get Current Profile",
    profileInput: "Profile URL or user_id",
    queryProfile: "Query Profile",
    profileNotes: "Profile Notes",
    loadNextPage: "Load Next Page",
    noMore: "No More",
    keywordSearch: "Keyword Search",
    keyword: "Keyword",
    count: "Count",
    sort: "Sort",
    comprehensive: "Comprehensive",
    latest: "Latest",
    mostLiked: "Most liked",
    mostCommented: "Most commented",
    mostCollected: "Most collected",
    type: "Type",
    unlimited: "Any",
    time: "Time",
    oneDay: "Past day",
    oneWeek: "Past week",
    halfYear: "Past six months",
    searchNotes: "Search Notes",
    keywordMonitor: "Keyword Monitor",
    intervalMinutes: "Interval minutes",
    saveMonitor: "Save Monitor",
    monitorList: "Monitor List",
    everyMinutes: "Every {minutes} minutes",
    enabled: "Enabled",
    disabled: "Disabled",
    notRun: "Not run",
    runOnce: "Run Once",
    noMonitors: "No keyword monitors yet.",
    analytics: "Analytics",
    collectSnapshot: "Collect Snapshot",
    unknownAccount: "Unknown account",
    fans: "Fans",
    likesCollects: "Likes and collects",
    recentNotesCount: "{count} recent notes",
    noSnapshots: "No account snapshots yet.",
    unknownAuthor: "Unknown author",
    note: "Note",
    publishTime: "Published",
    likeShort: "Likes",
    collectShort: "Collects",
    commentShort: "Comments",
    collapse: "Collapse",
    expand: "Expand",
    refreshDetail: "Refresh Detail",
    loadDetail: "Load Detail",
    openNote: "Open Note",
    openAfterDetail: "Load detail to open",
    imageViewer: "Image viewer",
    picture: "Image",
    close: "Close",
    previousImage: "Previous image",
    nextImage: "Next image",
    thumbnail: "Thumbnail",
    largeImage: "Large image",
    profileData: "Profile Data",
    profileEmpty: "Avatar, nickname, profile link, and basic metrics will appear here after lookup.",
    unknownUser: "Unknown user",
    redId: "XHS ID",
    unknown: "Unknown",
    openProfile: "Open Profile",
    noBio: "No bio",
    follows: "Following",
    queryProfileNotes: "Query Profile Notes",
    selectAccountRequired: "Select an account first",
    savingAccount: "Saving account...",
    accountSaved: "Account saved",
    generatingLoginQr: "Generating login QR code...",
    loginQrReady: "QR code generated. Scan with the XHS app.",
    checkingLogin: "Checking scan status...",
    qrLoginSaved: "QR login succeeded. Account saved.",
    qrExpired: "QR code expired",
    deletingAccount: "Deleting account...",
    accountDeleted: "Account deleted",
    checkingCookie: "Checking cookie...",
    localPublishOnly: "Direct publish requires local files. Use QR publish for URL media.",
    publishing: "Checking account and publishing...",
    loadingSelfProfile: "Loading current profile...",
    profileLoaded: "Profile loaded",
    queryingProfile: "Querying profile...",
    searchingNotes: "Searching notes...",
    searchDone: "Found {count} notes. To reduce requests, details and media load on demand.",
    monitorIntervalInvalid: "Monitor interval cannot be less than 5 minutes",
    savingMonitor: "Saving keyword monitor...",
    monitorSaved: "Keyword monitor saved",
    runningMonitor: "Running keyword monitor...",
    monitorDone: "Monitor finished. Returned {returned}, new {saved}",
    deletingMonitor: "Deleting keyword monitor...",
    monitorDeleted: "Keyword monitor deleted",
    deletingHistory: "Deleting publish history...",
    historyDeleted: "Publish history deleted",
    collectingSnapshot: "Collecting account snapshot...",
    snapshotSaved: "Account snapshot saved",
    loadingProfileNotes: "Loading profile notes...",
    loadingMoreProfileNotes: "Loading next page of profile notes...",
    profileNotesLoaded: "Loaded {count} profile notes",
    loadingNoteDetail: "Loading note detail on demand...",
    noteDetailLoaded: "Note detail loaded",
    savingApiKey: "Saving API Key...",
    apiKeySaved: "API Key saved",
    qrPublishNeedsUrl: "QR publish requires URL media with publicly accessible URLs",
    generatingQr: "Generating QR code...",
    qrGenerated: "QR code generated",
    publishReused: "Publish content loaded for editing"
  }
};

type LabelSet = (typeof labels)["zh"];

function template(value: string, params: Record<string, string | number>): string {
  return Object.entries(params).reduce(
    (current, [key, item]) => current.split(`{${key}}`).join(String(item)),
    value
  );
}

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
  const [loginPlatform] = useState<LoginPlatform>("pc");
  const [qrAccountName, setQrAccountName] = useState("");
  const [loginQrSession, setLoginQrSession] = useState<LoginQrSession | null>(null);
  const qrCheckInFlight = useRef(false);
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
      setStatus({ type: "error", text: text.selectAccountRequired });
      return false;
    }
    return true;
  }

  async function addAccount(event: FormEvent) {
    event.preventDefault();
    setStatus({ type: "loading", text: text.savingAccount });
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
      setStatus({ type: "success", text: text.accountSaved });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function startQrLogin(event?: FormEvent) {
    event?.preventDefault();
    setStatus({ type: "loading", text: text.generatingLoginQr });
    try {
      const data = await apiFetch<LoginQrSession>("/api/login/qrcode", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ platform: loginPlatform })
      });
      setLoginQrSession(data);
      setStatus({ type: "success", text: text.loginQrReady });
    } catch (error) {
      setLoginQrSession(null);
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function checkQrLogin(manual = true) {
    if (!loginQrSession || qrCheckInFlight.current) return;
    qrCheckInFlight.current = true;
    if (manual) {
      setStatus({ type: "loading", text: text.checkingLogin });
    }
    try {
      const data = await apiFetch<LoginQrCheckResult>(`/api/login/qrcode/${loginQrSession.session_id}/check`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ account_name: qrAccountName, save_account: true })
      });
      if (data.status === "success" && data.account) {
        setLoginQrSession(null);
        setQrAccountName("");
        await loadAccounts();
        setSelectedAccountId(data.account.id);
        setStatus({ type: "success", text: text.qrLoginSaved });
      } else if (data.status === "expired") {
        setLoginQrSession(null);
        setStatus({ type: "error", text: data.msg || text.qrExpired });
      } else if (manual || data.status === "confirm") {
        setStatus({ type: "loading", text: data.msg });
      }
    } catch (error) {
      setLoginQrSession(null);
      setStatus({ type: "error", text: (error as Error).message });
    } finally {
      qrCheckInFlight.current = false;
    }
  }

  async function deleteAccount() {
    if (!requireSelectedAccount()) return;
    setStatus({ type: "loading", text: text.deletingAccount });
    try {
      await apiFetch(`/api/accounts/${selectedAccountId}`, { method: "DELETE" });
      setSelectedAccountId("");
      await loadAccounts();
      setStatus({ type: "success", text: text.accountDeleted });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function checkAccount() {
    if (!requireSelectedAccount()) return;
    setStatus({ type: "loading", text: text.checkingCookie });
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
      setStatus({ type: "error", text: text.localPublishOnly });
      return;
    }
    if (mediaType === "image") {
      Array.from(images || []).forEach((file) => formData.append("images", file));
    } else if (video) {
      formData.append("video", video);
    }

    setStatus({ type: "loading", text: text.publishing });
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
    setStatus({ type: "loading", text: text.loadingSelfProfile });
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
      setStatus({ type: "success", text: text.profileLoaded });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function queryProfile(event: FormEvent) {
    event.preventDefault();
    if (!requireSelectedAccount() || !profileInput.trim()) return;
    setStatus({ type: "loading", text: text.queryingProfile });
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
      setStatus({ type: "success", text: text.profileLoaded });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function searchNotes(event: FormEvent) {
    event.preventDefault();
    if (!requireSelectedAccount() || !searchQuery.trim()) return;
    setStatus({ type: "loading", text: text.searchingNotes });
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
      setStatus({ type: "success", text: template(text.searchDone, { count: data.notes.length }) });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function createMonitor(event: FormEvent) {
    event.preventDefault();
    if (!requireSelectedAccount() || !monitorKeyword.trim()) return;
    const intervalMinutes = Number(monitorInterval);
    if (!Number.isFinite(intervalMinutes) || intervalMinutes < 5) {
      setStatus({ type: "error", text: text.monitorIntervalInvalid });
      return;
    }
    setStatus({ type: "loading", text: text.savingMonitor });
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
      setStatus({ type: "success", text: text.monitorSaved });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function runMonitor(monitorId: string) {
    setStatus({ type: "loading", text: text.runningMonitor });
    try {
      const data = await apiFetch<{ notes: SearchNote[]; saved: SavedSearchResult[] }>(
        `/api/search-monitors/${monitorId}/run`,
        { method: "POST" }
      );
      await loadOperations();
      setStatus({ type: "success", text: template(text.monitorDone, { returned: data.notes.length, saved: data.saved.length }) });
    } catch (error) {
      await loadOperations().catch(() => undefined);
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function deleteMonitor(monitorId: string) {
    setStatus({ type: "loading", text: text.deletingMonitor });
    try {
      await apiFetch(`/api/search-monitors/${monitorId}`, { method: "DELETE" });
      await loadOperations();
      setStatus({ type: "success", text: text.monitorDeleted });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function deletePublishHistoryItem(taskId: string) {
    setStatus({ type: "loading", text: text.deletingHistory });
    try {
      await apiFetch(`/api/publish-tasks/${taskId}`, { method: "DELETE" });
      await loadOperations();
      setStatus({ type: "success", text: text.historyDeleted });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function createAnalyticsSnapshot() {
    if (!requireSelectedAccount()) return;
    setStatus({ type: "loading", text: text.collectingSnapshot });
    try {
      await apiFetch<{ snapshot: AnalyticsSnapshot }>("/api/analytics/snapshots", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ account_id: selectedAccountId })
      });
      await loadOperations();
      setStatus({ type: "success", text: text.snapshotSaved });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function loadProfileNotes(reset = false) {
    if (!requireSelectedAccount() || !profile?.user_id) return;
    setStatus({ type: "loading", text: reset ? text.loadingProfileNotes : text.loadingMoreProfileNotes });
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
      setStatus({ type: "success", text: template(text.profileNotesLoaded, { count: data.notes.length }) });
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
    setStatus({ type: "loading", text: text.loadingNoteDetail });
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
      setStatus({ type: "success", text: text.noteDetailLoaded });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    } finally {
      setDetailLoadingIds((current) => current.filter((item) => item !== key));
    }
  }

  async function saveExternalConfig(event: FormEvent) {
    event.preventDefault();
    setStatus({ type: "loading", text: text.savingApiKey });
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
      setStatus({ type: "success", text: text.apiKeySaved });
    } catch (error) {
      setStatus({ type: "error", text: (error as Error).message });
    }
  }

  async function generateExternalQr(event?: FormEvent) {
    event?.preventDefault();
    if (!requireSelectedAccount()) return;
    if (mediaSource !== "url") {
      setStatus({ type: "error", text: text.qrPublishNeedsUrl });
      return;
    }
    setStatus({ type: "loading", text: text.generatingQr });
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
      setStatus({ type: "success", text: text.qrGenerated });
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
    setStatus({ type: "success", text: text.publishReused });
  }

  useEffect(() => {
    if (!loginQrSession) return;
    const timer = window.setInterval(() => {
      void checkQrLogin(false);
    }, 2000);
    return () => window.clearInterval(timer);
  }, [loginQrSession?.session_id, qrAccountName]);

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

      <nav className="tabs" aria-label={lang === "zh" ? "功能导航" : "Navigation"}>
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
            <option value="">{text.notSelected}</option>
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
            <span>{text.statusLabel}: {selectedAccount.last_check_status || text.unchecked}</span>
          </div>
        )}
      </section>

      {activeTab === "dashboard" && (
        <section className="layout">
          <section className="stats-grid">
            <div className="stat-card">
              <strong>{summary?.publish_total || 0}</strong>
              <span>{text.dashboardPublishHistory}</span>
            </div>
            <div className="stat-card">
              <strong>{summary?.publish_done || 0}</strong>
              <span>{text.dashboardPublished}</span>
            </div>
            <div className="stat-card">
              <strong>{summary?.monitor_enabled || 0}</strong>
              <span>{text.enabledMonitors}</span>
            </div>
            <div className="stat-card">
              <strong>{summary?.search_result_total || 0}</strong>
              <span>{text.monitorResults}</span>
            </div>
            <div className="stat-card">
              <strong>{summary?.analytics_snapshot_total || 0}</strong>
              <span>{text.accountSnapshots}</span>
            </div>
          </section>
          <section className="panel">
            <div className="section-head">
              <h2>{text.recentOps}</h2>
              <button type="button" onClick={loadOperations}>{text.refresh}</button>
            </div>
            <div className="table-list">
              {(summary?.latest_logs || []).map((log) => (
                <div className="list-row" key={log.id}>
                  <strong>{log.message}</strong>
                  <span>{log.event_type}</span>
                  <span>{log.created_at}</span>
                </div>
              ))}
              {(!summary || summary.latest_logs.length === 0) && <p className="empty-state">{text.noOps}</p>}
            </div>
          </section>
        </section>
      )}

      {activeTab === "accounts" && (
        <section className="layout account-layout">
          <section className="panel qr-login-panel">
            <div className="section-head">
              <div>
                <h2>{text.pcQrLogin}</h2>
                <p className="empty-state">{text.pcQrLoginDesc}</p>
              </div>
              <span className="soft-badge">{text.recommended}</span>
            </div>
            <form onSubmit={startQrLogin} className="stack">
              <label>
                {text.accountName}
                <input
                  value={qrAccountName}
                  onChange={(event) => setQrAccountName(event.target.value)}
                  placeholder={text.autoNameAfterLogin}
                />
              </label>
              <div className="button-row">
                <button type="submit" className="primary">
                  <QrCode aria-hidden />
                  {text.generateLoginQr}
                </button>
                <button type="button" onClick={() => checkQrLogin(true)} disabled={!loginQrSession}>
                  <Smartphone aria-hidden />
                  {text.checkStatus}
                </button>
              </div>
            </form>
            {loginQrSession && (
              <div className="login-qr-card">
                <img src={loginQrSession.qr_image} alt={text.scanQrAlt} />
                <div>
                  <strong>{text.pcQrLogin}</strong>
                  <span>{text.scanQrConfirm}</span>
                  <span>{text.scanQrUsage}</span>
                  <span>{template(text.qrExpires, { seconds: loginQrSession.expires_in_seconds })}</span>
                </div>
              </div>
            )}
          </section>

          <section className="panel manual-cookie-panel">
            <div>
              <h2>{text.manualCookie}</h2>
              <p className="empty-state">{text.manualCookieDesc}</p>
            </div>
            <form onSubmit={addAccount} className="stack">
              <label>
                {text.accountName}
                <input
                  value={accountName}
                  onChange={(event) => setAccountName(event.target.value)}
                  placeholder={text.autoNameAfterSave}
                />
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
              <button type="submit">{text.saveAccount}</button>
            </form>
          </section>

          <section className="panel account-tools-panel">
            <h2>{text.accountTools}</h2>
            {selectedAccount ? (
              <div className="account-summary">
                <strong>{selectedAccount.name}</strong>
                <span>{selectedAccount.cookie_preview}</span>
                <span>{text.statusLabel}: {selectedAccount.last_check_status || text.unchecked}</span>
              </div>
            ) : (
              <p className="empty-state">{text.noAccount}</p>
            )}
            <div className="button-row">
              <button type="button" onClick={checkAccount} disabled={!selectedAccountId}>{text.checkAccount}</button>
              <button type="button" className="danger" onClick={deleteAccount} disabled={!selectedAccountId}>{text.deleteAccount}</button>
            </div>
          </section>
        </section>
      )}

      {activeTab === "publish" && (
        <section className="layout two-panel-layout">
          <section className="panel publisher-panel">
            <h2>{text.directPublish}</h2>
            <form onSubmit={publish} className="publisher-form">
              <label>
                {text.title}
                <input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={60} required />
              </label>
              <label>
                {text.content}
                <textarea value={desc} onChange={(event) => setDesc(event.target.value)} rows={7} />
              </label>
              <label>
                {text.location}
                <input value={location} onChange={(event) => setLocation(event.target.value)} />
              </label>
              <div className="two-col">
                <label>
                  {text.visibility}
                  <select value={privacyType} onChange={(event) => setPrivacyType(event.target.value)}>
                    <option value="1">{text.private}</option>
                    <option value="0">{text.public}</option>
                  </select>
                </label>
                <label>
                  {text.mediaType}
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
                    <option value="image">{text.imageNote}</option>
                    <option value="video">{text.videoNote}</option>
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
                    {text.image}
                    <input type="file" accept="image/*" multiple onChange={(event) => setImages(event.target.files)} />
                  </label>
                ) : (
                  <label>
                    {text.video}
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
                  ? `${text.saved}: ${externalConfig.api_key_preview}`
                  : text.noApiKey}
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
            <h2>{text.publishHistory}</h2>
            <button type="button" onClick={loadOperations}>{text.refresh}</button>
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
                  <button type="button" onClick={() => reusePublishHistoryItem(task)}>{text.reusePublish}</button>
                  <button type="button" className="danger" onClick={() => deletePublishHistoryItem(task.id)}>{text.delete}</button>
                </div>
              </div>
            ))}
            {publishHistory.length === 0 && <p className="empty-state">{text.noPublishHistory}</p>}
          </div>
        </section>
      )}

      {activeTab === "profile" && (
        <section className="layout two-panel-layout">
          <section className="panel">
            <h2>{text.profileQuery}</h2>
            <div className="button-row">
              <button type="button" onClick={getSelfProfile} disabled={!selectedAccountId}>
                {text.getSelfProfile}
              </button>
            </div>
            <form onSubmit={queryProfile} className="stack">
              <label>
                {text.profileInput}
                <input
                  value={profileInput}
                  onChange={(event) => setProfileInput(event.target.value)}
                  placeholder="https://www.xiaohongshu.com/user/profile/..."
                />
              </label>
              <button type="submit" className="primary" disabled={!selectedAccountId}>
                {text.queryProfile}
              </button>
            </form>
          </section>
          <ProfileCard
            profile={profile}
            onLoadNotes={() => loadProfileNotes(true)}
            canLoadNotes={Boolean(selectedAccountId && profile?.user_id)}
            text={text}
          />
          {profileNotes.length > 0 && (
            <section className="panel wide-panel">
              <div className="section-head">
                <h2>{text.profileNotes}</h2>
                <button type="button" onClick={() => loadProfileNotes(false)} disabled={!profileHasMore}>
                  {profileHasMore ? text.loadNextPage : text.noMore}
                </button>
              </div>
              <NoteResults notes={profileNotes} detailLoadingIds={detailLoadingIds} onLoadDetail={loadNoteDetail} text={text} />
            </section>
          )}
        </section>
      )}

      {activeTab === "search" && (
        <section className="panel">
          <h2>{text.keywordSearch}</h2>
          <form onSubmit={searchNotes} className="search-form">
            <label>
              {text.keyword}
              <input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} required />
            </label>
            <label>
              {text.count}
              <select value={searchCount} onChange={(event) => setSearchCount(event.target.value)}>
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
              </select>
            </label>
            <label>
              {text.sort}
              <select value={sortType} onChange={(event) => setSortType(event.target.value)}>
                <option value="0">{text.comprehensive}</option>
                <option value="1">{text.latest}</option>
                <option value="2">{text.mostLiked}</option>
                <option value="3">{text.mostCommented}</option>
                <option value="4">{text.mostCollected}</option>
              </select>
            </label>
            <label>
              {text.type}
              <select value={noteType} onChange={(event) => setNoteType(event.target.value)}>
                <option value="0">{text.unlimited}</option>
                <option value="1">{text.videoNote}</option>
                <option value="2">{text.imageNote}</option>
              </select>
            </label>
            <label>
              {text.time}
              <select value={noteTime} onChange={(event) => setNoteTime(event.target.value)}>
                <option value="0">{text.unlimited}</option>
                <option value="1">{text.oneDay}</option>
                <option value="2">{text.oneWeek}</option>
                <option value="3">{text.halfYear}</option>
              </select>
            </label>
            <button type="submit" className="primary" disabled={!selectedAccountId}>
              {text.searchNotes}
            </button>
          </form>
          <NoteResults notes={searchResults} detailLoadingIds={detailLoadingIds} onLoadDetail={loadNoteDetail} text={text} />
        </section>
      )}

      {activeTab === "monitors" && (
        <section className="layout two-panel-layout">
          <section className="panel">
            <h2>{text.keywordMonitor}</h2>
            <form onSubmit={createMonitor} className="stack">
              <label>
                {text.keyword}
                <input value={monitorKeyword} onChange={(event) => setMonitorKeyword(event.target.value)} required />
              </label>
              <div className="two-col">
                <label>
                  {text.count}
                  <select value={searchCount} onChange={(event) => setSearchCount(event.target.value)}>
                    <option value="10">10</option>
                    <option value="20">20</option>
                    <option value="50">50</option>
                  </select>
                </label>
                <label>
                  {text.intervalMinutes}
                  <input
                    type="number"
                    min="5"
                    max="1440"
                    value={monitorInterval}
                    onChange={(event) => setMonitorInterval(event.target.value)}
                  />
                </label>
              </div>
              <button type="submit" className="primary" disabled={!selectedAccountId}>{text.saveMonitor}</button>
            </form>
          </section>
          <section className="panel">
            <div className="section-head">
              <h2>{text.monitorList}</h2>
              <button type="button" onClick={loadOperations}>{text.refresh}</button>
            </div>
            <div className="table-list">
              {searchMonitors.map((monitor) => (
                <div className="list-row" key={monitor.id}>
                  <strong>{monitor.keyword}</strong>
                  <span>{template(text.everyMinutes, { minutes: monitor.interval_minutes })} · {monitor.enabled ? text.enabled : text.disabled}</span>
                  <span>{monitor.last_run_status || text.notRun} {monitor.last_run_message || ""}</span>
                  <div className="row-actions">
                    <button type="button" onClick={() => runMonitor(monitor.id)}>{text.runOnce}</button>
                    <button type="button" className="danger" onClick={() => deleteMonitor(monitor.id)}>{text.delete}</button>
                  </div>
                </div>
              ))}
              {searchMonitors.length === 0 && <p className="empty-state">{text.noMonitors}</p>}
            </div>
          </section>
          {savedSearchResults.length > 0 && (
            <section className="panel wide-panel">
              <h2>{text.monitorResults}</h2>
              <NoteResults
                notes={savedSearchResults.map((item) => item.note)}
                detailLoadingIds={detailLoadingIds}
                onLoadDetail={loadNoteDetail}
                text={text}
              />
            </section>
          )}
        </section>
      )}

      {activeTab === "analytics" && (
        <section className="panel">
          <div className="section-head">
            <h2>{text.analytics}</h2>
            <button type="button" className="primary" onClick={createAnalyticsSnapshot} disabled={!selectedAccountId}>
              {text.collectSnapshot}
            </button>
          </div>
          <div className="table-list">
            {analyticsSnapshots.map((snapshot) => (
              <div className="list-row" key={snapshot.id}>
                <strong>{snapshot.profile?.nickname || text.unknownAccount}</strong>
                <span>{text.fans} {snapshot.profile?.fans || 0} · {text.likesCollects} {snapshot.profile?.interaction || 0}</span>
                <span>{template(text.recentNotesCount, { count: snapshot.recent_notes?.length || 0 })}</span>
                <span>{snapshot.created_at}</span>
              </div>
            ))}
            {analyticsSnapshots.length === 0 && <p className="empty-state">{text.noSnapshots}</p>}
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
  onLoadDetail,
  text
}: {
  notes: SearchNote[];
  detailLoadingIds: string[];
  onLoadDetail: (note: SearchNote) => void;
  text: LabelSet;
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
                  <p>{note.nickname || text.unknownAuthor} · {note.note_type || text.note}</p>
                  {note.upload_time && <p>{text.publishTime}: {note.upload_time}</p>}
                  <p>{text.likeShort} {note.liked_count || 0} · {text.collectShort} {note.collected_count || 0} · {text.commentShort} {note.comment_count || 0}</p>
                </div>
              </div>
              {note.desc && (
                <div className="note-desc-wrap">
                  <p className={descExpanded ? "note-desc expanded" : "note-desc"}>{note.desc}</p>
                  {canToggleDesc && (
                    <button type="button" className="text-button" onClick={() => toggleDesc(key)}>
                      {descExpanded ? text.collapse : text.expand}
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
                        alt={`${note.title} ${text.picture} ${index + 1}`}
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
                  {detailLoaded ? text.refreshDetail : text.loadDetail}
                </button>
                {detailLoaded && note.note_url ? (
                  <a href={note.note_url} target="_blank" rel="noreferrer">
                    {text.openNote}
                  </a>
                ) : (
                  <span>{text.openAfterDetail}</span>
                )}
              </div>
            </article>
          );
        })}
      </div>
      {viewer && (
        <div className="image-viewer" role="dialog" aria-modal="true" aria-label={text.imageViewer} onClick={closeViewer}>
          <div className="image-viewer-inner" onClick={(event) => event.stopPropagation()}>
            <div className="image-viewer-head">
              <span>{viewer.title || text.picture} · {viewer.index + 1}/{viewer.images.length}</span>
              <button type="button" onClick={closeViewer}>{text.close}</button>
            </div>
            <div className="image-viewer-stage">
              {viewer.images.length > 1 && (
                <button type="button" className="image-viewer-nav left" onClick={() => shiftViewer(-1)} aria-label={text.previousImage}>
                  ‹
                </button>
              )}
              <img src={mediaProxyUrl(viewer.images[viewer.index])} alt={`${viewer.title} ${text.largeImage} ${viewer.index + 1}`} />
              {viewer.images.length > 1 && (
                <button type="button" className="image-viewer-nav right" onClick={() => shiftViewer(1)} aria-label={text.nextImage}>
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
                    <img src={mediaProxyUrl(imageUrl)} alt={`${text.thumbnail} ${index + 1}`} />
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
  canLoadNotes,
  text
}: {
  profile: Profile | null;
  onLoadNotes: () => void;
  canLoadNotes: boolean;
  text: LabelSet;
}) {
  if (!profile) {
    return (
      <section className="panel empty-state">
        <h2>{text.profileData}</h2>
        <p>{text.profileEmpty}</p>
      </section>
    );
  }
  return (
    <section className="panel profile-card">
      <div className="profile-head">
        {profile.avatar && <img src={profile.avatar} alt={profile.nickname} />}
        <div>
          <h2>{profile.nickname || text.unknownUser}</h2>
          <p>{text.redId}: {profile.red_id || text.unknown}</p>
          {profile.home_url && (
            <a href={profile.home_url} target="_blank" rel="noreferrer">
              {text.openProfile}
            </a>
          )}
        </div>
      </div>
      <p>{profile.desc || text.noBio}</p>
      <div className="metric-grid">
        <span>{text.follows} {profile.follows || 0}</span>
        <span>{text.fans} {profile.fans || 0}</span>
        <span>{text.likesCollects} {profile.interaction || 0}</span>
        <span>{profile.gender || text.unknown} · {profile.ip_location || text.unknown}</span>
      </div>
      <button type="button" className="primary" onClick={onLoadNotes} disabled={!canLoadNotes}>
        {text.queryProfileNotes}
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
