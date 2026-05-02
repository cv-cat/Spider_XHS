/* XHS Field Console — frontend logic */
(() => {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const state = {
    mode: 'comments',
    rmode: 'notes',
    taskId: null,             // 当前正在跑的任务 id
    contextTaskId: null,      // 已载入的历史任务（"追加到该任务" 上下文）
    contextTaskName: '',
    history: [],              // 历史任务概要列表
    es: null,
    timer: null,
    startedAt: 0,
    overall: { value: 0, max: 0 },
    current: { value: 0, max: 0, indeterminate: false },
    notesCount: 0,
    commentsCount: 0,
    phase: '—',
    cachedNotes: [],
    displayedNotes: [],          // cachedNotes 经 filter + sort 后的视图
    checkedUrls: new Set(),
    notesFilter: '',
    notesSort: { col: null, dir: null },
    cachedComments: [],
    commentsFilter: '',
    commentsSort: { col: null, dir: null },
  };

  // 解析 "1.2万 / 1234 / 1k" 等中英文计数
  const parseCount = (s) => {
    s = String(s == null ? '' : s).trim();
    if (!s || s === '-') return 0;
    const m = s.match(/^([\d.]+)\s*([万w千k]?)/i);
    if (!m) return parseFloat(s) || 0;
    const n = parseFloat(m[1]);
    const u = (m[2] || '').toLowerCase();
    if (u === '万' || u === 'w') return n * 10000;
    if (u === '千' || u === 'k') return n * 1000;
    return n;
  };

  // ───────────── helpers ─────────────
  const fmtTime = (sec) => {
    sec = Math.max(0, sec);
    if (sec < 60) return sec.toFixed(1) + 's';
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}m ${s}s`;
  };

  const escHtml = (s) => String(s || '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));

  const truncate = (s, n) => {
    s = String(s || '');
    return s.length > n ? s.slice(0, n - 1) + '…' : s;
  };

  // 图片代理（绕 Referer 校验）
  const proxyImg = (url) => {
    if (!url) return '';
    if (/^\/?api\/img/.test(url)) return url;
    if (!/^https?:\/\//i.test(url)) return url;
    return `/api/img?u=${encodeURIComponent(url)}`;
  };

  // ───────────── clock ─────────────
  const tickClock = () => {
    const d = new Date();
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    const ss = String(d.getSeconds()).padStart(2, '0');
    $('#clock').textContent = `${hh}:${mm}:${ss}`;
  };
  setInterval(tickClock, 1000); tickClock();

  // ───────────── cookie 持久化 ─────────────
  const COOKIE_KEY = 'xhs_collector_cookie';
  const cookieInput = $('#cookie-input');

  // 1) 先从 localStorage 恢复
  const savedCookie = localStorage.getItem(COOKIE_KEY);
  if (savedCookie && cookieInput) cookieInput.value = savedCookie;

  // 2) 再读 .env 状态作为 placeholder 提示
  fetch('/api/cookie').then(r => r.json()).then(j => {
    if (cookieInput && !cookieInput.value) {
      cookieInput.placeholder = j.has_cookie
        ? `留空将使用 .env 中的 COOKIES（${j.preview}）`
        : '.env 未配置，请在此填入并自动保存';
    }
  }).catch(() => {});

  // 3) 输入即写回 localStorage（debounce）
  let cookieSaveTimer = null;
  cookieInput && cookieInput.addEventListener('input', () => {
    if (cookieSaveTimer) clearTimeout(cookieSaveTimer);
    cookieSaveTimer = setTimeout(() => {
      const v = cookieInput.value.trim();
      if (v) localStorage.setItem(COOKIE_KEY, v);
      else localStorage.removeItem(COOKIE_KEY);
    }, 400);
  });

  $('#cookie-toggle').addEventListener('click', () => {
    const inp = $('#cookie-input');
    const showing = inp.type === 'text';
    inp.type = showing ? 'password' : 'text';
    $('#cookie-toggle').textContent = showing ? '显示' : '隐藏';
  });

  // ───────────── tabs ─────────────
  $$('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('.tab').forEach(b => b.classList.toggle('is-active', b === btn));
      const mode = btn.dataset.mode;
      state.mode = mode;
      $$('.panel').forEach(p => p.classList.toggle('hidden', p.dataset.panel !== mode));
      if (mode === 'history') loadHistory();
    });
  });

  // ───────────── opt-sub deps ─────────────
  $$('.opt-toggle input[type="checkbox"]').forEach(cb => {
    const sync = () => {
      const sub = $(`.opt-sub[data-deps="${cb.id}"]`);
      if (sub) sub.classList.toggle('is-on', cb.checked);
    };
    cb.addEventListener('change', sync);
    sync();
  });

  // ───────────── result tabs ─────────────
  $$('.rtab').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('.rtab').forEach(b => b.classList.toggle('is-active', b === btn));
      const t = btn.dataset.rtab;
      state.rmode = t;
      $$('.rpane').forEach(p => p.classList.toggle('is-active', p.dataset.rpane === t));
    });
  });

  // ───────────── feed ─────────────
  const feedEl = $('#feed');
  const FEED_MAX = 400;

  const log = (msg, cls = '') => {
    const li = document.createElement('li');
    if (cls) li.className = cls;
    const ts = new Date().toLocaleTimeString('en-GB');
    li.innerHTML = `<span class="ts">${ts}</span>${msg}`;
    feedEl.appendChild(li);
    while (feedEl.children.length > FEED_MAX) feedEl.removeChild(feedEl.firstChild);
    feedEl.scrollTop = feedEl.scrollHeight;
  };
  $('#clear-feed').addEventListener('click', () => { feedEl.innerHTML = ''; });

  // ───────────── progress ─────────────
  const setOverall = (value, max) => {
    state.overall = { value, max };
    const pct = max ? Math.min(100, (value / max) * 100) : 0;
    const bar = $('#bar-overall');
    bar.classList.remove('indeterminate');
    bar.style.width = pct + '%';
    $('#bar-overall-pct').textContent = max ? `${value} / ${max}` : '—';
  };

  const setCurrent = (value, max, indeterminate = false) => {
    state.current = { value, max, indeterminate };
    const bar = $('#bar-current');
    if (indeterminate) {
      bar.classList.add('indeterminate');
      bar.style.width = '30%';
      $('#bar-current-pct').textContent = '进行中…';
    } else {
      bar.classList.remove('indeterminate');
      const pct = max ? Math.min(100, (value / max) * 100) : 0;
      bar.style.width = pct + '%';
      $('#bar-current-pct').textContent = max ? `${value} / ${max}` : (value ? `${value}` : '—');
    }
  };

  const setMetrics = () => {
    $('#m-phase').textContent = state.phase;
    $('#m-notes').textContent = state.overall.max
      ? `${state.overall.value} / ${state.overall.max}`
      : `${state.notesCount}`;
    $('#m-comments').textContent = String(state.commentsCount);
  };

  const setDockState = (txt, running) => {
    const el = $('#dock-state');
    el.textContent = txt;
    el.classList.toggle('is-running', !!running);
    setRunPill(txt, running);
  };

  const setRunPill = (txt, running, kind = '') => {
    const pill = $('#run-pill');
    if (!pill) return;
    if (running) {
      pill.hidden = false;
      pill.classList.remove('is-stopped', 'is-error');
      $('#run-pill-text').textContent = txt || '运行中';
    } else if (kind === 'stopped' || kind === 'error') {
      pill.hidden = false;
      pill.classList.toggle('is-stopped', kind === 'stopped');
      pill.classList.toggle('is-error', kind === 'error');
      $('#run-pill-text').textContent = txt;
      // 5 秒后自动消失
      setTimeout(() => {
        if ($('#dock-state').textContent.includes(txt)) pill.hidden = true;
      }, 5000);
    } else {
      pill.hidden = true;
    }
  };

  // ───────────── results render ─────────────
  const notesPane = $('.rpane[data-rpane="notes"]');
  const commentsPane = $('.rpane[data-rpane="comments"]');
  const notesTable = notesPane.querySelector('table tbody');
  const commentsTable = commentsPane.querySelector('table tbody');

  const computeDisplayedNotes = () => {
    let arr = state.cachedNotes;
    const q = (state.notesFilter || '').trim().toLowerCase();
    if (q) {
      arr = arr.filter(n =>
        String(n.title || '').toLowerCase().includes(q) ||
        String(n.nickname || '').toLowerCase().includes(q) ||
        String(n.desc || '').toLowerCase().includes(q)
      );
    }
    const { col, dir } = state.notesSort;
    if (col && dir) {
      const NUMERIC = new Set(['liked_count', 'collected_count', 'comment_count']);
      const sign = dir === 'asc' ? 1 : -1;
      arr = [...arr].sort((a, b) => {
        let av = a[col], bv = b[col];
        if (NUMERIC.has(col)) { av = parseCount(av); bv = parseCount(bv); }
        else { av = String(av || '').toLowerCase(); bv = String(bv || '').toLowerCase(); }
        if (av < bv) return -sign;
        if (av > bv) return sign;
        return 0;
      });
    }
    state.displayedNotes = arr;
    return arr;
  };

  const renderNotes = (items) => {
    if (items !== undefined) state.cachedNotes = items || [];
    const displayed = computeDisplayedNotes();
    const toolbar = notesPane.querySelector('.rpane-toolbar');
    if (state.cachedNotes.length === 0) {
      notesPane.querySelector('.empty').style.display = '';
      notesPane.querySelector('table').hidden = true;
      if (toolbar) toolbar.hidden = true;
      $('#rc-notes').textContent = '0';
      $('#export-notes').disabled = true;
      return;
    }
    notesPane.querySelector('.empty').style.display = 'none';
    notesPane.querySelector('table').hidden = false;
    if (toolbar) toolbar.hidden = false;
    notesTable.innerHTML = '';
    if (displayed.length === 0) {
      notesTable.innerHTML = `<tr><td colspan="9" style="text-align:center;color:var(--muted);padding:32px">无匹配（共 ${state.cachedNotes.length} 条）</td></tr>`;
      $('#rc-notes').textContent = state.cachedNotes.length;
      $('#export-notes').disabled = false;
      updateSelection();
      return;
    }
    displayed.forEach((n, i) => {
      const url = n.note_url || '';
      const checked = state.checkedUrls.has(url);
      const cover = n.cover || (Array.isArray(n.image_list) ? n.image_list[0] : '') || '';
      const title = n.title || '无标题';
      const desc = n.desc ? truncate(n.desc, 80) : '';
      const tr = document.createElement('tr');
      if (checked) tr.classList.add('is-checked');
      tr.dataset.noteId = n.note_id || '';
      tr.innerHTML = `
        <td class="w-check"><input type="checkbox" data-url="${escHtml(url)}" ${checked ? 'checked' : ''}></td>
        <td class="w-idx">${i + 1}</td>
        <td class="w-cover">${cover ? `<img src="${escHtml(proxyImg(cover))}" loading="lazy" alt="" referrerpolicy="no-referrer">` : ''}</td>
        <td>
          <div class="cell-title">
            <div class="t">${escHtml(title)}</div>
            <div class="u">@${escHtml(n.nickname || '匿名')} · ${escHtml(n.note_type || n.type || 'note')}</div>
            ${desc ? `<div class="u" style="-webkit-line-clamp:1;color:var(--text-2)">${escHtml(desc)}</div>` : ''}
          </div>
        </td>
        <td class="num">${escHtml(n.liked_count || '-')}</td>
        <td class="num">${escHtml(n.collected_count || '-')}</td>
        <td class="num">${escHtml(n.comment_count || '-')}</td>
        <td class="w-time" title="${escHtml(n.upload_time || '')}">${escHtml(n.upload_time || '-')}</td>
        <td class="w-action">
          <button class="btn-ghost xs" data-act="preview" data-note-id="${escHtml(n.note_id || '')}">预览</button>
          <a href="${escHtml(url)}" target="_blank" rel="noopener">原文</a>
        </td>
      `;
      notesTable.appendChild(tr);
    });
    $('#rc-notes').textContent = state.cachedNotes.length;
    $('#export-notes').disabled = state.cachedNotes.length === 0;
    updateSelection();
  };

  const updateSelection = () => {
    const total = state.cachedNotes.length;
    // 清掉不在当前 cachedNotes 中的勾选（防止跨次任务串扰）
    const validUrls = new Set(state.cachedNotes.map(n => n.note_url));
    Array.from(state.checkedUrls).forEach(u => { if (!validUrls.has(u)) state.checkedUrls.delete(u); });
    const sel = state.checkedUrls.size;
    $('#notes-sel-count').textContent = String(sel);
    $('#notes-total').textContent = String(total);
    const cmtCount = $('#comments-target-count');
    if (cmtCount) cmtCount.textContent = String(sel);
    $('#batch-comments').disabled = sel === 0 || !!state.es;
    const allCb = $('#notes-all'); const allTh = $('#notes-all-th');
    const allChecked = total > 0 && sel === total;
    const someChecked = sel > 0 && sel < total;
    [allCb, allTh].forEach(cb => {
      if (!cb) return;
      cb.checked = allChecked;
      cb.indeterminate = someChecked;
    });
    // 待补详情计数（按"选中"优先，无选中则按全部 undetailed）
    const allUndetailed = state.cachedNotes.filter(n => !n._detailed);
    const detailTargets = sel > 0
      ? allUndetailed.filter(n => state.checkedUrls.has(n.note_url))
      : allUndetailed;
    const undEl = $('#undetailed-count');
    const detBtn = $('#batch-details');
    const targetTid = state.contextTaskId || state.taskId;
    if (undEl) undEl.textContent = String(detailTargets.length);
    if (detBtn) {
      detBtn.disabled = detailTargets.length === 0 || !!state.es || !targetTid;
      detBtn.title = sel > 0
        ? `补抓选中且未补全的 ${detailTargets.length} 篇`
        : `补抓未补全的 ${detailTargets.length} 篇（全部）`;
    }
    // batch-comments 同样要求有任务上下文
    $('#batch-comments').disabled = sel === 0 || !!state.es || !targetTid;
  };

  const computeDisplayedComments = () => {
    let arr = state.cachedComments;
    const q = (state.commentsFilter || '').trim().toLowerCase();
    if (q) {
      arr = arr.filter(c =>
        String(c.content || '').toLowerCase().includes(q) ||
        String(c.nickname || '').toLowerCase().includes(q) ||
        String(c.ip_location || '').toLowerCase().includes(q)
      );
    }
    const { col, dir } = state.commentsSort;
    if (col && dir) {
      const NUMERIC = new Set(['like_count', 'level']);
      const sign = dir === 'asc' ? 1 : -1;
      arr = [...arr].sort((a, b) => {
        let av = a[col], bv = b[col];
        if (NUMERIC.has(col)) { av = parseCount(av); bv = parseCount(bv); }
        else { av = String(av || '').toLowerCase(); bv = String(bv || '').toLowerCase(); }
        if (av < bv) return -sign;
        if (av > bv) return sign;
        return 0;
      });
    } else {
      // 默认：根评论 + 紧随其子，与导出 xlsx 一致
      arr = [...arr].sort((a, b) => {
        const aKey = (a.level === 2) ? [String(a.parent_comment_id || ''), 1, String(a.comment_id || '')]
                                     : [String(a.comment_id || ''), 0, ''];
        const bKey = (b.level === 2) ? [String(b.parent_comment_id || ''), 1, String(b.comment_id || '')]
                                     : [String(b.comment_id || ''), 0, ''];
        for (let i = 0; i < 3; i++) {
          if (aKey[i] < bKey[i]) return -1;
          if (aKey[i] > bKey[i]) return 1;
        }
        return 0;
      });
    }
    return arr;
  };

  const renderComments = (items) => {
    if (items !== undefined) state.cachedComments = items || [];
    const total = state.cachedComments.length;
    const tbl = commentsPane.querySelector('table');
    const toolbar = commentsPane.querySelector('.comments-toolbar');
    if (total === 0) {
      commentsPane.querySelector('.empty').style.display = '';
      tbl.hidden = true;
      if (toolbar) toolbar.hidden = true;
      commentsTable.innerHTML = '';
      $('#rc-comments').textContent = '0';
      $('#export-comments').disabled = true;
      return;
    }
    commentsPane.querySelector('.empty').style.display = 'none';
    tbl.hidden = false;
    if (toolbar) toolbar.hidden = false;
    const displayed = computeDisplayedComments();
    const totalEl = $('#comments-total-count');
    if (totalEl) totalEl.textContent = String(total);
    commentsTable.innerHTML = '';
    if (displayed.length === 0) {
      commentsTable.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:32px">无匹配（共 ${total} 条）</td></tr>`;
    } else {
      displayed.forEach((c, i) => {
        const isSub = c.level === 2;
        const tr = document.createElement('tr');
        if (isSub) tr.classList.add('is-sub');
        const lvlTag = `<span class="lvl-tag l-${isSub ? 2 : 1}">${isSub ? '回复' : '根'}</span>`;
        tr.innerHTML = `
          <td class="w-idx">${i + 1}</td>
          <td class="w-level">${lvlTag}</td>
          <td>
            <div class="cell-title">
              <div class="t" style="-webkit-line-clamp:1">@${escHtml(c.nickname || '匿名')}</div>
              <div class="u">${escHtml(c.user_id || '')}</div>
            </div>
          </td>
          <td class="cell-content-wrap"><div class="cell-content">${escHtml(truncate(c.content, 280))}</div></td>
          <td class="num">${escHtml(c.like_count || '0')}</td>
          <td class="w-time">${escHtml(c.upload_time || '')}</td>
          <td>${escHtml(c.ip_location || '')}</td>
        `;
        commentsTable.appendChild(tr);
      });
    }
    $('#rc-comments').textContent = total;
    $('#export-comments').disabled = false;
  };

  // notes 表事件代理：勾选 / 全选
  notesTable.addEventListener('change', (e) => {
    if (e.target.matches('input[type="checkbox"][data-url]')) {
      const u = e.target.getAttribute('data-url');
      if (e.target.checked) state.checkedUrls.add(u);
      else state.checkedUrls.delete(u);
      e.target.closest('tr').classList.toggle('is-checked', e.target.checked);
      updateSelection();
    }
  });

  // 筛选输入：debounce 重渲染
  let filterTimer = null;
  $('#notes-filter') && $('#notes-filter').addEventListener('input', (e) => {
    if (filterTimer) clearTimeout(filterTimer);
    filterTimer = setTimeout(() => {
      state.notesFilter = e.target.value;
      renderNotes();
    }, 180);
  });

  // 通用列头排序工具
  const wireSort = (tableEl, sortStateKey, rerender) => {
    tableEl.addEventListener('click', (e) => {
      const th = e.target.closest('th[data-sort]');
      if (!th) return;
      const col = th.dataset.sort;
      const cur = state[sortStateKey];
      let dir;
      if (cur.col !== col) dir = 'asc';
      else if (cur.dir === 'asc') dir = 'desc';
      else if (cur.dir === 'desc') dir = null;
      else dir = 'asc';
      state[sortStateKey] = { col: dir ? col : null, dir };
      tableEl.querySelectorAll('th[data-sort]').forEach(h => h.classList.remove('sort-asc','sort-desc'));
      if (dir) th.classList.add(dir === 'asc' ? 'sort-asc' : 'sort-desc');
      rerender();
    });
  };

  const notesTableEl = notesPane.querySelector('table');
  wireSort(notesTableEl, 'notesSort', renderNotes);

  const commentsTableEl = commentsPane.querySelector('table');
  wireSort(commentsTableEl, 'commentsSort', renderComments);

  // 评论筛选输入
  let cmtFilterTimer = null;
  $('#comments-filter') && $('#comments-filter').addEventListener('input', (e) => {
    if (cmtFilterTimer) clearTimeout(cmtFilterTimer);
    cmtFilterTimer = setTimeout(() => {
      state.commentsFilter = e.target.value;
      renderComments();
    }, 180);
  });

  // 点击「预览」按钮打开抽屉（只接 data-act="preview"）
  notesTable.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-act="preview"]');
    if (!btn) return;
    const noteId = btn.dataset.noteId;
    if (!noteId) return;
    openNotePreview(noteId);
  });

  const toggleSelectAll = (checked) => {
    state.checkedUrls.clear();
    if (checked) state.cachedNotes.forEach(n => { if (n.note_url) state.checkedUrls.add(n.note_url); });
    notesTable.querySelectorAll('input[type="checkbox"][data-url]').forEach(cb => {
      cb.checked = checked;
      cb.closest('tr').classList.toggle('is-checked', checked);
    });
    updateSelection();
  };
  // 用 click 事件并显式翻转，避开 indeterminate / change 事件的歧义
  ['notes-all', 'notes-all-th'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const total = state.cachedNotes.length;
      const sel = state.checkedUrls.size;
      // 已全选 → 取消；否则 → 全选
      toggleSelectAll(sel < total);
    });
  });

  // 增量取数：每次拉全量列表（仅刷新当前正在跑的任务来源面板）
  const refreshResults = async (tid) => {
    tid = tid || state.taskId || state.contextTaskId;
    if (!tid) return;
    try {
      const [n, c] = await Promise.all([
        fetch(`/api/notes/${tid}?limit=1000`).then(r => r.json()),
        fetch(`/api/comments/${tid}?limit=2000`).then(r => r.json()),
      ]);
      if (n && Array.isArray(n.items)) {
        state.notesCount = n.total;
        renderNotes(n.items);
        $('#export-notes').disabled = n.total === 0;
      }
      if (c && Array.isArray(c.items)) {
        state.commentsCount = c.total;
        renderComments(c.items);
        $('#export-comments').disabled = c.total === 0;
      }
      setMetrics();
    } catch (_) {}
  };

  // ───────────── run task ─────────────
  const collectParams = (mode) => {
    const cookies = $('#cookie-input').value.trim();
    const base = { kind: mode };
    if (cookies) base.cookies = cookies;

    if (mode === 'comments') {
      const urls = $('#comments-urls').value
        .split('\n').map(s => s.trim()).filter(Boolean);
      const depth = ($$('input[name="cmt-depth"]').find(r => r.checked) || {}).value;
      base.urls = urls;
      base.fetch_sub = depth !== 'top';
    } else if (mode === 'homepage') {
      base.user_url = $('#homepage-url').value.trim();
      base.fetch_detail = $('#hp-fetch-detail').checked;
      base.with_comments = $('#hp-with-comments').checked;
      const depth = ($$('input[name="hp-depth"]').find(r => r.checked) || {}).value;
      base.fetch_sub = depth !== 'top';
    } else if (mode === 'search') {
      base.query = $('#search-query').value.trim();
      base.require_num = parseInt($('#search-num').value, 10) || 20;
      base.sort_type = parseInt($('#search-sort').value, 10);
      base.note_type = parseInt($('#search-type').value, 10);
      base.note_time = parseInt($('#search-time').value, 10);
      base.fetch_detail = $('#sr-fetch-detail').checked;
      base.with_comments = $('#sr-with-comments').checked;
      const depth = ($$('input[name="sr-depth"]').find(r => r.checked) || {}).value;
      base.fetch_sub = depth !== 'top';
    }
    return base;
  };

  const validate = (p) => {
    if (p.kind === 'comments' && (!p.urls || !p.urls.length)) return '请填入至少一个笔记 URL';
    if (p.kind === 'homepage' && !p.user_url) return '请填入用户主页 URL';
    if (p.kind === 'search' && !p.query) return '请填入关键词';
    return null;
  };

  const resetProgress = () => {
    state.phase = '—';
    setOverall(0, 0);
    setCurrent(0, 0, false);
    setMetrics();
  };

  const startElapsed = () => {
    state.startedAt = performance.now();
    if (state.timer) clearInterval(state.timer);
    state.timer = setInterval(() => {
      const sec = (performance.now() - state.startedAt) / 1000;
      $('#m-elapsed').textContent = fmtTime(sec);
    }, 200);
  };
  const stopElapsed = () => {
    if (state.timer) { clearInterval(state.timer); state.timer = null; }
  };

  const run = async (mode, override = null, opts = {}) => {
    if (state.es) {
      log('已有任务在运行', 'is-warn');
      return;
    }
    const params = override || collectParams(mode);
    const err = validate(params);
    if (err) { log(err, 'is-error'); return; }

    feedEl.innerHTML = '';
    resetProgress();

    // 决定追加目标：opts.appendTo > 显式 context > 无（创建新任务）
    const appendTo = opts.appendTo || state.contextTaskId;
    const isAppend = !!appendTo;
    const modeName = opts.label || (mode === 'comments' ? '评论采集' : mode === 'homepage' ? '主页采集' : '关键词搜索');
    log(isAppend ? `追加 · ${modeName} → ${state.contextTaskName || appendTo}` : `开始 · ${modeName}`, 'is-phase');

    const url = isAppend ? `/api/append/${appendTo}` : '/api/run';
    let res;
    try {
      const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      res = await r.json();
      if (!r.ok) throw new Error(res.error || 'run failed');
    } catch (e) {
      log(`派发失败：${e.message}`, 'is-error');
      return;
    }
    state.taskId = res.task_id;
    if (!isAppend) {
      // 全新任务：清空显示，绑定为当前任务（在上下文条里展示）
      state.cachedNotes = [];
      state.checkedUrls.clear();
      state.notesCount = 0;
      state.commentsCount = 0;
      renderNotes([]);
      renderComments([]);
      setContext(res.task_id, res.name);
    }
    log(`task_id = ${state.taskId}`);
    setDockState(isAppend ? '追加运行中' : '运行中', true);
    $('#stop-btn').disabled = false;
    setCurrent(0, 0, true);
    startElapsed();
    openStream(state.taskId, res.cursor || 0);
    updateSelection();
  };

  // 「补全详情」批量按钮 — 优先补"选中"中尚未补的，没选中时补全部
  $('#batch-details').addEventListener('click', () => {
    const targetTid = state.contextTaskId || state.taskId;
    if (!targetTid) { log('当前没有任务可补全', 'is-warn'); return; }
    const allUndetailed = state.cachedNotes.filter(n => !n._detailed);
    const targets = state.checkedUrls.size > 0
      ? allUndetailed.filter(n => state.checkedUrls.has(n.note_url))
      : allUndetailed;
    if (targets.length === 0) {
      log('选中的笔记已全部补全详情', 'is-warn');
      return;
    }
    const cookies = $('#cookie-input').value.trim();
    const params = { kind: 'details', note_ids: targets.map(n => n.note_id) };
    if (cookies) params.cookies = cookies;
    const label = state.checkedUrls.size > 0
      ? `补全详情 · 选中 ${targets.length} 篇`
      : `补全详情 · 全部 ${targets.length} 篇`;
    run('details', params, { appendTo: targetTid, label });
  });

  // 「采集选中评论」批量按钮 — 始终追加到当前显示的任务
  $('#batch-comments').addEventListener('click', () => {
    if (state.checkedUrls.size === 0) return;
    const targetTid = state.contextTaskId || state.taskId;
    if (!targetTid) {
      log('当前没有任务可追加，先采集笔记再来', 'is-warn');
      return;
    }
    const cookies = $('#cookie-input').value.trim();
    const depth = ($$('input[name="batch-depth"]').find(r => r.checked) || {}).value;
    const params = {
      kind: 'comments',
      urls: Array.from(state.checkedUrls),
      fetch_sub: depth !== 'top',
    };
    if (cookies) params.cookies = cookies;
    run('comments', params, { appendTo: targetTid, label: `批量评论 · ${state.checkedUrls.size} 篇` });
  });

  // ───────────── SSE ─────────────
  const openStream = (tid, cursor = 0) => {
    const es = new EventSource(`/api/stream/${tid}?cursor=${cursor}`);
    state.es = es;
    let pendingRefresh = null;
    const scheduleRefresh = () => {
      if (pendingRefresh) return;
      pendingRefresh = setTimeout(() => {
        pendingRefresh = null;
        refreshResults();
      }, 350);
    };

    es.onmessage = (msgEvt) => {
      let evt;
      try { evt = JSON.parse(msgEvt.data); } catch (_) { return; }
      handleEvent(evt, scheduleRefresh);
    };
    es.addEventListener('end', () => {
      es.close();
      state.es = null;
      stopElapsed();
      $('#stop-btn').disabled = true;
      refreshResults();
      updateSelection();
    });
    es.onerror = () => {
      // 连接关闭即视为终止；手动停止时不会再 reconnect
      try { es.close(); } catch (_) {}
      state.es = null;
      stopElapsed();
      $('#stop-btn').disabled = true;
      updateSelection();
    };
  };

  const handleEvent = (evt, scheduleRefresh) => {
    const t = evt.t, p = evt.p || {};
    if (t === 'task_start') {
      log(`任务启动`, 'is-success');
    } else if (t === 'phase') {
      const name = p.name === 'comments' ? '评论采集'
        : p.name === 'homepage' ? '主页采集'
        : p.name === 'search' ? '关键词搜索'
        : p.name === 'details' ? '采集详情'
        : p.name;
      state.phase = name;
      if (p.total) {
        setOverall(0, p.total);
      } else if (p.target) {
        setOverall(0, p.target);
      } else {
        setOverall(0, 0);
      }
      const tail = p.total ? ` · ${p.total} 条` : (p.target ? ` · 目标 ${p.target}` : '');
      log(`阶段：${name}${tail}`, 'is-phase');
      setMetrics();
    } else if (t === 'note_index') {
      setOverall(p.i - 1, p.total);
      setCurrent(0, 0, true);
      $('#run-pill-text').textContent = `${state.phase} ${p.i}/${p.total}`;
      log(`[${p.i}/${p.total}] ${escHtml(truncate(p.url, 88))}`);
    } else if (t === 'note_start') {
      log(`  note_id = ${escHtml(p.note_id)}`);
    } else if (t === 'page') {
      if (p.kind === 'out') {
        setCurrent(p.count, 0, true);
        $('#bar-current-pct').textContent = `一级 ${p.count} 条`;
      } else if (p.kind === 'inner') {
        setCurrent(p.count, p.total, false);
      } else if (p.kind === 'search') {
        setOverall(p.count, p.total || p.count);
        setCurrent(p.count, p.total || 0, !p.total);
        $('#run-pill-text').textContent = `搜索 ${p.count}/${p.total || '?'}`;
        log(`  搜索第 ${p.page} 页 · ${p.count}/${p.total || '?'}`);
      } else if (p.kind === 'user_posts') {
        setCurrent(p.count, 0, true);
        $('#bar-current-pct').textContent = `已拉 ${p.count} 条笔记`;
      }
    } else if (t === 'note_done') {
      if (p.kind === 'detail') {
        log(`  详情 · ${p.count}`, 'is-success');
      } else {
        log(`  完成 · ${p.count} 条评论`, 'is-success');
      }
      scheduleRefresh();
    } else if (t === 'comments_progress') {
      state.commentsCount = p.total;
      setMetrics();
    } else if (t === 'notes_collected') {
      state.notesCount = p.count;
      setMetrics();
      log(`已收集 ${p.count} 条笔记`, 'is-phase');
      scheduleRefresh();
    } else if (t === 'error') {
      log(escHtml(p.msg || 'error'), 'is-error');
    } else if (t === 'log') {
      log(escHtml(p.msg || ''));
    } else if (t === 'done') {
      const map = { done: ['完成', 'is-success', ''], stopped: ['已停止', 'is-warn', 'stopped'], error: ['错误', 'is-error', 'error'] };
      const [finalText, cls, pillKind] = map[p.state] || ['完成', 'is-success', ''];
      const added = (p.added_notes ? `+${p.added_notes} 笔记` : '') + (p.added_comments ? ` +${p.added_comments} 评论` : '');
      log(`${finalText} · 共 ${p.notes} 笔记 / ${p.comments} 评论 · ${added.trim() || '无新增'} · ${fmtTime(p.elapsed || 0)}`, cls);
      setDockState(finalText, false);
      setRunPill(finalText + ' · ' + (added.trim() || '无新增'), false, pillKind || 'done');
      if (state.overall.max) setOverall(state.overall.max, state.overall.max);
      setCurrent(1, 1, false);
      $('#export-notes').disabled = p.notes === 0;
      $('#export-comments').disabled = p.comments === 0;
      updateSelection();
      loadHistory();
    }
  };

  // ───────────── stop & export ─────────────
  $('#stop-btn').addEventListener('click', async () => {
    if (!state.taskId) return;
    try {
      await fetch(`/api/stop/${state.taskId}`, { method: 'POST' });
      log('已发出停止指令，等待当前请求结束', 'is-warn');
    } catch (_) {}
  });

  const currentResultsTaskId = () => state.contextTaskId || state.taskId;
  $('#export-notes').addEventListener('click', () => {
    const tid = currentResultsTaskId();
    if (tid) window.location.href = `/api/export/${tid}?kind=notes`;
  });
  $('#export-comments').addEventListener('click', () => {
    const tid = currentResultsTaskId();
    if (tid) window.location.href = `/api/export/${tid}?kind=comments`;
  });

  // ───────────── primary buttons ─────────────
  $$('button[data-run]').forEach(b => {
    b.addEventListener('click', () => run(b.dataset.run));
  });

  // ───────────── note preview drawer ─────────────
  const drawer = $('#note-drawer');
  const drawerBody = $('#drawer-body');

  const openLightbox = (src) => {
    const lb = document.createElement('div');
    lb.className = 'lightbox';
    lb.innerHTML = `<img src="${escHtml(src)}" referrerpolicy="no-referrer" alt="">`;
    lb.addEventListener('click', () => lb.remove());
    document.body.appendChild(lb);
  };

  drawer.addEventListener('click', (e) => {
    if (e.target.matches('[data-close], .drawer-mask')) closeNotePreview();
    const im = e.target.closest('.dr-images img, .dr-comment .pics img');
    if (im) openLightbox(im.src);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const lb = document.querySelector('.lightbox');
      if (lb) { lb.remove(); return; }
      if (!drawer.hidden) closeNotePreview();
    }
  });

  const closeNotePreview = () => { drawer.hidden = true; };

  const openNotePreview = async (noteId) => {
    const tid = state.contextTaskId || state.taskId;
    if (!tid) return;
    drawer.hidden = false;
    drawerBody.innerHTML = '<div class="empty">加载中…</div>';
    $('#dr-title').textContent = '笔记预览';
    $('#dr-open').removeAttribute('href');
    try {
      const r = await fetch(`/api/note/${tid}/${encodeURIComponent(noteId)}`).then(r => r.json());
      if (r.error) throw new Error(r.error);
      drawerBody.innerHTML = renderNotePreview(r.note, r.comments || []);
      $('#dr-title').textContent = r.note.title || '无标题';
      if (r.note.note_url) $('#dr-open').setAttribute('href', r.note.note_url);
    } catch (e) {
      drawerBody.innerHTML = `<div class="empty" style="color:var(--danger)">加载失败：${escHtml(e.message)}</div>`;
    }
  };


  // 渲染笔记预览
  const renderNotePreview = (n, comments) => {
    const meta = [
      ['作者', `@${escHtml(n.nickname || '匿名')}`],
      ['类型', escHtml(n.note_type || n.type || '—')],
      ['上传', escHtml(n.upload_time || '—')],
      ['IP', escHtml(n.ip_location || '—')],
      ['点赞', escHtml(String(n.liked_count || '0'))],
      ['收藏', escHtml(String(n.collected_count || '0'))],
      ['评论', escHtml(String(n.comment_count || '0'))],
      ['分享', escHtml(String(n.share_count || '0'))],
    ];

    const metaHtml = meta.map(([k, v]) => `<div><span class="k">${k}</span><span class="v">${v}</span></div>`).join('');

    const desc = n.desc ? `<section class="dr-section"><h4>描述</h4><div class="dr-desc">${escHtml(n.desc)}</div></section>` : '';

    let media = '';
    if (n.note_type === '视频' && n.video_addr) {
      const poster = n.video_cover ? proxyImg(n.video_cover) : '';
      media = `<section class="dr-section"><h4>视频</h4><video class="dr-video" controls preload="metadata" ${poster ? `poster="${escHtml(poster)}"` : ''} src="${escHtml(proxyImg(n.video_addr))}"></video></section>`;
    } else if (Array.isArray(n.image_list) && n.image_list.length) {
      const imgs = n.image_list.filter(Boolean).map(u =>
        `<img src="${escHtml(proxyImg(u))}" loading="lazy" referrerpolicy="no-referrer" alt="">`
      ).join('');
      media = `<section class="dr-section"><h4>图集（${n.image_list.length}）</h4><div class="dr-images">${imgs}</div></section>`;
    }

    const tags = (n.tags && n.tags.length)
      ? `<section class="dr-section"><h4>标签</h4><div class="dr-tags">${n.tags.map(t => `<span class="dr-tag">#${escHtml(t)}</span>`).join('')}</div></section>`
      : '';

    // 评论：根 + 子评论嵌套展示
    const renderOneComment = (c) => {
      const av = c.avatar
        ? `<img class="av" src="${escHtml(proxyImg(c.avatar))}" referrerpolicy="no-referrer" alt="">`
        : '<div class="av"></div>';
      const pics = (c.pictures && c.pictures.length)
        ? `<div class="pics">${c.pictures.map(p => `<img src="${escHtml(proxyImg(p))}" referrerpolicy="no-referrer" alt="">`).join('')}</div>`
        : '';
      const showTags = (c.show_tags && c.show_tags.length) ? ` · ${escHtml(c.show_tags.join('/'))}` : '';
      return `
        <div class="dr-comment">
          ${av}
          <div class="body">
            <div class="top">
              <span class="nick">@${escHtml(c.nickname || '匿名')}</span>
              <span class="info">${escHtml(c.upload_time || '')} · ${escHtml(c.ip_location || '')} · ♥ ${escHtml(String(c.like_count || 0))}${showTags}</span>
            </div>
            <div class="text">${escHtml(c.content || '')}</div>
            ${pics}
          </div>
        </div>`;
    };

    const roots = [];
    const childMap = {};
    comments.forEach(c => {
      if (c.level === 2 && c.parent_comment_id) {
        (childMap[c.parent_comment_id] = childMap[c.parent_comment_id] || []).push(c);
      } else {
        roots.push(c);
      }
    });
    // 时间升序
    const byTime = (a, b) => String(a.upload_time || '').localeCompare(String(b.upload_time || ''));
    roots.sort(byTime);
    Object.values(childMap).forEach(arr => arr.sort(byTime));

    const cmtHtml = comments.length === 0
      ? '<div class="dr-comments-empty">暂无该笔记的评论 — 可在结果页勾选这条笔记后「采集评论」</div>'
      : roots.map(c => {
          let html = renderOneComment(c);
          const subs = childMap[c.comment_id] || [];
          if (subs.length) {
            html += `<div class="dr-subs">${subs.map(renderOneComment).join('')}</div>`;
          }
          return html;
        }).join('') +
        // 兜底：归属错乱的子评论（root 不在当前列表）也单独显示
        Object.entries(childMap)
          .filter(([rid]) => !roots.some(r => r.comment_id === rid))
          .map(([, arr]) => arr.map(renderOneComment).join(''))
          .join('');

    return `
      <section class="dr-section">
        <h4>元信息</h4>
        <div class="dr-meta">${metaHtml}</div>
      </section>
      ${desc}
      ${media}
      ${tags}
      <section class="dr-section">
        <h4>评论 (${comments.length})</h4>
        ${cmtHtml}
      </section>
    `;
  };

  // ───────────── history & context ─────────────
  const fmtTimeAgo = (ts) => {
    if (!ts) return '—';
    const sec = Date.now() / 1000 - ts;
    if (sec < 60) return Math.floor(sec) + ' 秒前';
    if (sec < 3600) return Math.floor(sec / 60) + ' 分钟前';
    if (sec < 86400) return Math.floor(sec / 3600) + ' 小时前';
    return Math.floor(sec / 86400) + ' 天前';
  };
  const kindCn = (k) => ({ comments: '评论', homepage: '主页', search: '搜索' }[k] || k);

  const setContext = (tid, name) => {
    state.contextTaskId = tid;
    state.contextTaskName = name || '';
    const bar = $('#context-bar');
    if (tid) {
      bar.hidden = false;
      $('#ctx-name').textContent = name;
      $('#ctx-meta').textContent = `id ${tid}`;
    } else {
      bar.hidden = true;
    }
    updateRunButtonLabels();
    updateBatchButtonHint();
    // 高亮历史表格中已加载的行
    $$('#history-tbody tr').forEach(tr => {
      tr.classList.toggle('is-loaded', tr.dataset.tid === tid);
    });
  };

  const updateRunButtonLabels = () => {
    const text = state.contextTaskId ? '追加到该任务' : '开始采集';
    $$('button[data-run]').forEach(b => { b.textContent = text; });
  };

  const updateBatchButtonHint = () => {
    const btn = $('#batch-comments');
    if (!btn) return;
    if (state.contextTaskId) {
      btn.textContent = '采集选中评论 → 追加';
      btn.title = `追加到任务 ${state.contextTaskName}`;
    } else {
      btn.textContent = '采集选中评论';
      btn.title = '本次任务结束后自动设为上下文，可继续追加';
    }
  };

  // 完整重置 UI 到空闲状态（保留日志、保留 cookie）
  const resetUI = () => {
    state.taskId = null;
    state.cachedNotes = [];
    state.displayedNotes = [];
    state.notesFilter = '';
    state.notesSort = { col: null, dir: null };
    state.cachedComments = [];
    state.commentsFilter = '';
    state.commentsSort = { col: null, dir: null };
    const fi = $('#notes-filter'); if (fi) fi.value = '';
    const cfi = $('#comments-filter'); if (cfi) cfi.value = '';
    notesPane.querySelectorAll('th[data-sort]').forEach(h => h.classList.remove('sort-asc','sort-desc'));
    commentsPane.querySelectorAll('th[data-sort]').forEach(h => h.classList.remove('sort-asc','sort-desc'));
    state.checkedUrls.clear();
    state.notesCount = 0;
    state.commentsCount = 0;
    state.phase = '—';
    state.overall = { value: 0, max: 0 };
    state.current = { value: 0, max: 0, indeterminate: false };
    renderNotes([]);
    renderComments([]);
    setOverall(0, 0);
    setCurrent(0, 0, false);
    setMetrics();
    setDockState('空闲', false);
    setRunPill('', false);
    stopElapsed();
    $('#m-elapsed').textContent = '0.0s';
    $('#stop-btn').disabled = true;
  };

  $('#ctx-clear').addEventListener('click', () => {
    if (state.es) {
      log('任务运行中，请先「停止」再新建任务', 'is-warn');
      return;
    }
    setContext(null);
    resetUI();
    log('已重置 · 下次操作将创建新任务', 'is-phase');
  });

  const loadHistory = async () => {
    try {
      const r = await fetch('/api/tasks').then(r => r.json());
      state.history = (r && r.items) || [];
      $('#history-count').textContent = String(state.history.length);
      renderHistory();
    } catch (e) {
      console.error('loadHistory failed', e);
      log('加载历史失败：' + (e.message || e), 'is-error');
    }
  };

  const renderHistory = () => {
    const tbody = $('#history-tbody');
    const tbl = document.querySelector('.history-table');
    const empty = $('#history-empty');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (state.history.length === 0) {
      tbl.hidden = true;
      empty.style.display = '';
      return;
    }
    tbl.hidden = false;
    empty.style.display = 'none';
    state.history.forEach((t) => {
      const tr = document.createElement('tr');
      tr.dataset.tid = t.id;
      if (t.id === state.contextTaskId) tr.classList.add('is-loaded');
      tr.innerHTML = `
        <td>
          <span class="h-name">${escHtml(t.name)}</span>
          <span class="h-id">${escHtml(t.id)}</span>
        </td>
        <td><span class="kind-tag k-${escHtml(t.kind)}">${escHtml(kindCn(t.kind))}</span></td>
        <td class="num">${t.notes}</td>
        <td class="num">${t.comments}</td>
        <td class="w-runs">${(t.runs || []).length}</td>
        <td class="h-time" title="${new Date(t.updated * 1000).toLocaleString()}">${fmtTimeAgo(t.updated)}</td>
        <td class="w-action">
          <button class="btn-ghost xs" data-act="load">载入</button>
          <button class="btn-ghost xs" data-act="rename">改名</button>
          <button class="btn-ghost xs danger" data-act="del">删除</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  };

  $('#refresh-history').addEventListener('click', () => loadHistory());

  $('#history-tbody').addEventListener('click', async (e) => {
    const tr = e.target.closest('tr');
    if (!tr) return;
    const tid = tr.dataset.tid;
    const t = state.history.find(x => x.id === tid);
    if (!t) return;
    const act = e.target.dataset && e.target.dataset.act;

    if (act === 'rename') {
      const newName = prompt('新的任务名称：', t.name);
      if (!newName || newName.trim() === '' || newName === t.name) return;
      await fetch(`/api/task/${tid}/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName.trim() }),
      });
      await loadHistory();
      if (tid === state.contextTaskId) setContext(tid, newName.trim());
      return;
    }
    if (act === 'del') {
      if (!confirm(`确定删除任务「${t.name}」？\n（数据将从磁盘移除）`)) return;
      const r = await fetch(`/api/task/${tid}`, { method: 'DELETE' });
      if (r.ok) {
        if (tid === state.contextTaskId) setContext(null);
        await loadHistory();
      } else {
        const j = await r.json().catch(() => ({}));
        log(`删除失败：${j.error || r.status}`, 'is-error');
      }
      return;
    }

    // 默认动作：载入
    await loadTaskAsContext(tid, t.name);
  });

  const loadTaskAsContext = async (tid, name) => {
    setContext(tid, name);
    state.taskId = tid;            // ← 同步设为当前任务，否则批量按钮的启用判断会失效
    state.cachedNotes = [];
    state.checkedUrls.clear();
    feedEl.innerHTML = '';
    log(`已载入任务 ${name}`, 'is-phase');
    await refreshResults(tid);
    setMetrics();
    // 切回评论 tab，方便用户立刻追加评论
    const targetTab = $$('.tab').find(b => b.dataset.mode === 'comments');
    if (targetTab) targetTab.click();
  };

  // initial render
  setOverall(0, 0);
  setCurrent(0, 0, false);
  setMetrics();
  setDockState('空闲', false);
  log('就绪', 'is-phase');
  updateSelection();
  updateRunButtonLabels();
  updateBatchButtonHint();
  loadHistory();
})();
