"use strict";

(() => {
  const RUNS_PATH = "/api/public-acquisition/runs";
  const POLL_MS = 320;
  const DISCOVER_MS = 500;
  const SENSITIVE_QUERY_TERMS = new Set(["token", "key", "secret", "signature", "sig", "auth", "password", "credential"]);
  const followButton = document.getElementById("follow-button");
  const runStatus = document.getElementById("run-status");
  const connectionStatus = document.getElementById("connection-status");
  const runTitle = document.getElementById("run-title");
  const runDetail = document.getElementById("run-detail");
  const fetchContent = document.getElementById("fetch-content");
  const jevContent = document.getElementById("jev-content");
  const fetchJump = document.getElementById("fetch-jump");
  const jevJump = document.getElementById("jev-jump");
  const resultsPanel = document.getElementById("results-panel");
  const results = document.getElementById("results");

  const state = {
    selectedRunId: null,
    pinned: false,
    latestSeenId: null,
    events: new Map(),
    lastEventId: 0,
    snapshot: null,
    polling: false,
    discovering: false,
    discoverQueued: false,
    discoveryBaselineSet: false,
    directHydrate: false,
    generation: 0,
    pollTimer: 0,
    discoverTimer: 0,
    streamTimer: 0,
    streamQueue: [],
    streamDeadline: 0,
    resultKey: null,
  };

  const feeds = {
    fetch: createFeed(fetchContent, fetchJump),
    jev: createFeed(jevContent, jevJump),
  };

  function element(name, className, text) {
    const node = document.createElement(name);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function clear(node) {
    node.replaceChildren();
  }

  function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  function validRunId(value) {
    return typeof value === "string" && /^[0-9a-f]{32}$/.test(value);
  }

  function terminal(status) {
    return status === "completed" || status === "partial" || status === "failed";
  }

  function active(status) {
    return status === "queued" || status === "running";
  }

  function statusLabel(status) {
    return {
      queued: "采集中",
      running: "采集中",
      completed: "已完成",
      partial: "部分完成",
      failed: "失败",
    }[status] || "等待任务";
  }

  function safeUrl(value) {
    if (typeof value !== "string" || value.length > 2048) return null;
    try {
      const url = new URL(value);
      if (url.protocol !== "https:" || url.username || url.password || (url.port && url.port !== "443")) return null;
      for (const key of url.searchParams.keys()) {
        if (SENSITIVE_QUERY_TERMS.has(key.toLowerCase())) return null;
      }
      return url.href;
    } catch {
      return null;
    }
  }

  function compactUrl(value) {
    const href = safeUrl(value);
    if (!href) return "已验证公开来源";
    const url = new URL(href);
    return `${url.hostname}${url.pathname}`.slice(0, 120);
  }

  function link(value, label) {
    const href = safeUrl(value);
    if (!href) return null;
    const node = element("a", "safe-link", label || compactUrl(href));
    node.href = href;
    node.target = "_blank";
    node.rel = "noopener noreferrer";
    return node;
  }

  function setConnection(message, tone = "idle") {
    connectionStatus.textContent = message;
    connectionStatus.className = `status ${tone}`;
  }

  async function request(path, options = {}) {
    const response = await fetch(path, {
      credentials: "same-origin",
      cache: "no-store",
      ...options,
      headers: { Accept: "application/json", ...(options.headers || {}) },
    });
    let payload = null;
    try { payload = await response.json(); } catch { /* use generic failure below */ }
    if (!response.ok || !isRecord(payload)) {
      const error = new Error(isRecord(payload) && typeof payload.error_code === "string" ? payload.error_code : "connection_failed");
      error.code = error.message;
      throw error;
    }
    return payload;
  }

  function setHash(runId, pinned) {
    const destination = pinned && validRunId(runId) ? `#run_id=${runId}` : window.location.pathname + window.location.search;
    window.history.replaceState({}, "", destination);
  }

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function createFeed(container, jump) {
    const feed = {
      container,
      jump,
      records: new Map(),
      following: true,
      programmatic: false,
      frame: 0,
      lastScrollTop: 0,
      hasContent: false,
      touchY: null,
    };
    const stopProgrammaticScroll = () => {
      if (!feed.programmatic) return;
      cancelAnimationFrame(feed.frame);
      feed.programmatic = false;
    };
    const pauseFollowing = () => {
      stopProgrammaticScroll();
      feed.following = false;
      jump.hidden = false;
    };
    container.addEventListener("pointerdown", stopProgrammaticScroll);
    container.addEventListener("wheel", (event) => {
      if (event.deltaY < 0) pauseFollowing();
      else stopProgrammaticScroll();
    }, { passive: true });
    container.addEventListener("touchstart", (event) => {
      feed.touchY = event.touches[0]?.clientY ?? null;
      stopProgrammaticScroll();
    }, { passive: true });
    container.addEventListener("touchmove", (event) => {
      const nextY = event.touches[0]?.clientY;
      if (typeof nextY === "number" && typeof feed.touchY === "number" && nextY > feed.touchY) pauseFollowing();
      feed.touchY = typeof nextY === "number" ? nextY : feed.touchY;
    }, { passive: true });
    container.addEventListener("scroll", () => {
      const current = container.scrollTop;
      if (!feed.programmatic && current < feed.lastScrollTop - 2) {
        feed.following = false;
        jump.hidden = false;
      } else if (feedAtBottom(feed)) {
        feed.following = true;
        jump.hidden = true;
      }
      feed.lastScrollTop = current;
    });
    jump.addEventListener("click", () => {
      feed.following = true;
      jump.hidden = true;
      scrollFeedToLive(feed);
    });
    return feed;
  }

  function feedAtBottom(feed) {
    return feed.container.scrollHeight - feed.container.scrollTop - feed.container.clientHeight <= 8;
  }

  function scrollFeedToLive(feed, instant = false) {
    if (!feed.following) return;
    const target = Math.max(0, feed.container.scrollHeight - feed.container.clientHeight);
    if (Math.abs(target - feed.container.scrollTop) < 1) return;
    cancelAnimationFrame(feed.frame);
    if (instant || prefersReducedMotion()) {
      feed.programmatic = true;
      feed.container.scrollTop = target;
      feed.lastScrollTop = target;
      feed.programmatic = false;
      return;
    }
    const start = feed.container.scrollTop;
    const startedAt = performance.now();
    feed.programmatic = true;
    const step = (now) => {
      const progress = Math.min(1, (now - startedAt) / 200);
      const eased = 1 - (1 - progress) * (1 - progress);
      const current = start + (target - start) * eased;
      feed.container.scrollTop = current;
      feed.lastScrollTop = current;
      if (progress < 1) feed.frame = requestAnimationFrame(step);
      else feed.programmatic = false;
    };
    feed.frame = requestAnimationFrame(step);
  }

  function resetFeed(feed, message) {
    cancelAnimationFrame(feed.frame);
    feed.records.clear();
    feed.following = true;
    feed.programmatic = false;
    feed.lastScrollTop = 0;
    feed.hasContent = false;
    feed.jump.hidden = true;
    feed.container.replaceChildren(element("p", "empty", message));
  }

  function prepareFeedForContent(feed) {
    if (feed.hasContent) return;
    feed.hasContent = true;
    feed.container.replaceChildren();
  }

  function resetRun(runId, { directHydrate = false } = {}) {
    state.generation += 1;
    state.selectedRunId = runId;
    state.events.clear();
    state.lastEventId = 0;
    state.snapshot = null;
    state.directHydrate = directHydrate;
    state.streamQueue = [];
    window.clearTimeout(state.streamTimer);
    state.streamTimer = 0;
    state.streamDeadline = 0;
    state.resultKey = null;
    resetFeed(feeds.fetch, "等待");
    resetFeed(feeds.jev, "等待");
    renderControls();
    renderResults();
  }

  function selectRun(runId, pinned, { directHydrate = Boolean(pinned) } = {}) {
    if (!validRunId(runId)) return;
    state.pinned = Boolean(pinned);
    if (state.selectedRunId !== runId) resetRun(runId, { directHydrate });
    setHash(runId, state.pinned);
    renderControls();
    pollSoon(0);
  }

  function orderedEvents() {
    return [...state.events.values()].sort((left, right) => left.event_id - right.event_id);
  }

  function appendEvents(events) {
    if (!Array.isArray(events)) return [];
    const added = [];
    for (const event of [...events].sort((left, right) => (left?.event_id || 0) - (right?.event_id || 0))) {
      if (!isRecord(event) || !Number.isInteger(event.event_id) || event.event_id < 1) continue;
      if (state.events.has(event.event_id)) continue;
      state.events.set(event.event_id, event);
      added.push(event);
    }
    return added;
  }

  function visibleStreamEvent(event) {
    return ["fetch_started", "fetch_finished", "jev_choice_started", "jev_choice_finished", "selected_link"].includes(event.type);
  }

  function displayEvents(events, { direct = false } = {}) {
    const visible = events.filter(visibleStreamEvent);
    if (direct) {
      visible.forEach((event) => applyStreamEvent(event, false));
      scrollFeedToLive(feeds.fetch, true);
      scrollFeedToLive(feeds.jev, true);
      return;
    }
    if (!state.streamQueue.length && !state.streamTimer) state.streamDeadline = performance.now() + 600;
    state.streamQueue.push(...visible);
    drainStreamQueue();
  }

  function drainStreamQueue() {
    if (state.streamTimer || !state.streamQueue.length) return;
    const showNext = () => {
      state.streamTimer = 0;
      const event = state.streamQueue.shift();
      if (event) applyStreamEvent(event, true);
      if (state.streamQueue.length) {
        const remainingMs = Math.max(0, state.streamDeadline - performance.now());
        const delay = Math.min(75, Math.max(0, Math.floor(remainingMs / state.streamQueue.length)));
        state.streamTimer = window.setTimeout(showNext, delay);
      } else {
        state.streamDeadline = 0;
      }
    };
    state.streamTimer = window.setTimeout(showNext, 0);
  }

  function markArrival(node) {
    if (prefersReducedMotion()) return;
    node.classList.remove("is-new");
    void node.offsetWidth;
    node.classList.add("is-new");
    window.setTimeout(() => node.classList.remove("is-new"), 150);
  }

  function renderControls() {
    const snapshot = state.snapshot;
    followButton.textContent = "跟随采集";
    followButton.disabled = false;
    if (!validRunId(state.selectedRunId)) {
      runStatus.textContent = "等待新采集";
      runStatus.className = "badge idle";
      runTitle.textContent = "等待新采集";
      runDetail.textContent = "";
      return;
    }
    if (!snapshot) {
      runStatus.textContent = "读取中";
      runStatus.className = "badge idle";
      runTitle.textContent = "正在读取已保存任务";
      runDetail.textContent = "";
      return;
    }
    const status = snapshot.status;
    const historical = state.pinned && terminal(status);
    if (historical) {
      runStatus.textContent = `上次采集 · ${statusLabel(status)}`;
      runStatus.className = `badge ${status || "idle"}`;
    } else if (active(status)) {
      runStatus.textContent = "采集中";
      runStatus.className = "badge running";
    } else {
      runStatus.textContent = statusLabel(status);
      runStatus.className = `badge ${status || "idle"}`;
    }
    if (historical) {
      runTitle.textContent = `上次采集 · ${statusLabel(status)}`;
      runDetail.textContent = "";
    } else if (active(status)) {
      runTitle.textContent = "采集中";
      runDetail.textContent = "";
    } else if (terminal(status)) {
      runTitle.textContent = statusLabel(status);
      runDetail.textContent = "";
    } else {
      runTitle.textContent = statusLabel(status);
      runDetail.textContent = "";
    }
  }

  function fetchStatus(event) {
    if (!event) return "读取中";
    return event.status === "fetched" ? "已读取" : "未完成";
  }

  function replaceLink(container, value, label) {
    container.replaceChildren();
    const source = link(value, label);
    if (source) {
      source.classList.add("source-link");
      container.append(source);
    }
  }

  function appendFeedNode(feed, node, animate) {
    const previous = !animate || prefersReducedMotion()
      ? []
      : [...feed.container.children].map((child) => ({ child, top: child.getBoundingClientRect().top }));
    feed.container.append(node);
    for (const item of previous) {
      const distance = item.top - item.child.getBoundingClientRect().top;
      if (Math.abs(distance) > 1 && typeof item.child.animate === "function") {
        item.child.animate(
          [{ transform: `translateY(${distance}px)` }, { transform: "translateY(0)" }],
          { duration: 200, easing: "cubic-bezier(.2,.8,.2,1)" },
        );
      }
    }
  }

  function createFetchRecord(id, animate) {
    const card = element("article", "content-card");
    const top = element("div", "card-top");
    const heading = element("div");
    const title = element("h3", "", "公开岗位网页");
    const source = element("div");
    const pill = element("span", "status-pill active", "读取中");
    const snippet = element("p", "snippet");
    snippet.hidden = true;
    heading.append(title, source);
    top.append(heading, pill);
    card.append(top, snippet);
    const record = { id, started: null, finished: null, card, title, source, pill, snippet };
    feeds.fetch.records.set(id, record);
    prepareFeedForContent(feeds.fetch);
    appendFeedNode(feeds.fetch, card, animate);
    return record;
  }

  function updateFetchRecord(record, animate) {
    const event = record.finished || record.started;
    const isBoard = typeof event?.route === "string" && event.route.endsWith("_board_api");
    record.title.textContent = isBoard ? "岗位列表" : typeof record.finished?.page_title === "string" ? record.finished.page_title : "公开岗位网页";
    replaceLink(record.source, record.finished?.final_url || event?.url, compactUrl(record.finished?.final_url || event?.url));
    record.pill.textContent = fetchStatus(record.finished);
    record.pill.className = "status-pill";
    if (!record.finished) record.pill.classList.add("active");
    if (record.finished && record.finished.status !== "fetched") record.pill.classList.add("failed");
    const snippet = record.finished?.snippet;
    record.snippet.hidden = typeof snippet !== "string" || !snippet;
    record.snippet.textContent = typeof snippet === "string" ? snippet : "";
    if (animate) markArrival(record.card);
    scrollFeedToLive(feeds.fetch, !animate);
  }

  function createJevRecord(id, animate) {
    const card = element("article", "jev-card");
    const top = element("div", "card-top");
    const title = element("h3", "", "Jev 判断");
    const pill = element("span", "status-pill active", "判断中");
    const summary = element("p", "input-summary");
    const choice = element("p", "choice-output");
    const source = element("div");
    const details = element("details", "jev-details");
    top.append(title, pill);
    card.append(top, summary, choice, source, details);
    const record = { id, started: null, finished: null, selected: null, card, pill, summary, choice, source, details };
    feeds.jev.records.set(id, record);
    prepareFeedForContent(feeds.jev);
    appendFeedNode(feeds.jev, card, animate);
    return record;
  }

  function selectedRoleFor(record) {
    const selectedUrl = safeUrl(record.selected?.observed_url);
    const roles = Array.isArray(state.snapshot?.result?.roles) ? state.snapshot.result.roles : [];
    const role = selectedUrl
      ? roles.find((item) => isRecord(item) && [item.job_url, item.application_url].some((url) => safeUrl(url) === selectedUrl))
      : null;
    return { selectedUrl, role };
  }

  function updateJevRecord(record, animate) {
    const summary = isRecord(record.started?.input_summary) ? record.started.input_summary : null;
    const { selectedUrl, role } = selectedRoleFor(record);
    const observed = summary && Number.isInteger(summary.observed_link_count)
      ? summary.observed_link_count
      : record.started?.candidate_count;
    record.summary.hidden = !Number.isInteger(observed);
    record.summary.textContent = Number.isInteger(observed) ? `输入：${observed} 个岗位链接` : "";
    record.pill.className = "status-pill";
    record.pill.textContent = record.finished?.status === "ok" ? "已输出" : record.finished ? "未提供选择" : "判断中";
    if (!record.finished) record.pill.classList.add("active");
    if (record.finished && record.finished.status !== "ok") record.pill.classList.add("failed");
    record.choice.hidden = !record.finished;
    if (record.finished) {
      record.choice.textContent = typeof role?.title === "string"
        ? `已选择：${role.title}`
        : selectedUrl
          ? "已选择公开来源"
          : record.finished.choice === "done"
            ? "停止继续采集"
            : record.finished.choice === "needs_followup"
              ? "需要继续核实"
              : "未得到有效选择";
    }
    replaceLink(record.source, selectedUrl, typeof role?.title === "string" ? `已选择：${role.title}` : "已选择的公开来源");
    const wasOpen = record.details.open;
    const detailNodes = [];
    if (typeof record.started?.question === "string") detailNodes.push(element("p", "question", record.started.question));
    if (summary && Array.isArray(summary.observed_links)) {
      const list = element("ul", "observed-links");
      for (const observedLink of summary.observed_links) {
        if (!isRecord(observedLink)) continue;
        const item = element("li");
        const observedLinkNode = link(observedLink.url, typeof observedLink.label === "string" ? observedLink.label : "已观察公开链接");
        if (observedLinkNode) item.append(observedLinkNode);
        list.append(item);
      }
      if (list.childElementCount) detailNodes.push(list);
    }
    if (record.finished) {
      const choice = typeof record.finished.choice === "string" ? record.finished.choice : "未提供选择";
      detailNodes.push(element("p", "output-note", `Choice：${choice}`));
      if (typeof record.finished.model === "string") detailNodes.push(element("p", "output-note", `模型：${record.finished.model}`));
    }
    record.details.hidden = !detailNodes.length;
    record.details.replaceChildren(element("summary", "", "查看输入输出"), ...detailNodes);
    record.details.open = wasOpen;
    if (animate) markArrival(record.card);
    scrollFeedToLive(feeds.jev, !animate);
  }

  function applyStreamEvent(event, animate) {
    if (event.type === "fetch_started" || event.type === "fetch_finished") {
      if (typeof event.request_id !== "string") return;
      const record = feeds.fetch.records.get(event.request_id) || createFetchRecord(event.request_id, animate);
      if (event.type === "fetch_started") record.started = event;
      else record.finished = event;
      updateFetchRecord(record, animate);
      return;
    }
    if (typeof event.call_id !== "string") return;
    const record = feeds.jev.records.get(event.call_id) || createJevRecord(event.call_id, animate);
    if (event.type === "jev_choice_started") record.started = event;
    else if (event.type === "jev_choice_finished") record.finished = event;
    else if (event.type === "selected_link") record.selected = event;
    else return;
    updateJevRecord(record, animate);
  }

  function refreshJevRecords() {
    feeds.jev.records.forEach((record) => updateJevRecord(record, false));
  }

  function appendRole(role) {
    const card = element("article", "role");
    card.append(element("h3", "", typeof role.title === "string" ? role.title : "公开结构化岗位"));
    const facts = [role.location, role.employment_type, role.listing_scope].filter((value) => typeof value === "string" && value);
    if (facts.length) card.append(element("p", "", facts.join(" · ")));
    const links = element("div");
    for (const [key, label] of [["job_url", "岗位页"], ["application_url", "官方申请链接"], ["source_url", "来源"]]) {
      const source = link(role[key], label);
      if (source) links.append(source);
    }
    if (links.childElementCount) card.append(links);
    return card;
  }

  function renderResults() {
    if (!terminal(state.snapshot?.status)) {
      resultsPanel.hidden = true;
      state.resultKey = null;
      clear(results);
      return;
    }
    const key = `${state.selectedRunId || ""}:${state.snapshot?.status || ""}:${state.snapshot?.finished_at || ""}`;
    if (state.resultKey === key) return;
    state.resultKey = key;
    resultsPanel.hidden = false;
    clear(results);
    const result = isRecord(state.snapshot?.result) ? state.snapshot.result : null;
    if (!result) {
      results.append(element("p", "empty", state.snapshot?.status === "failed" ? "采集失败" : "没有结果"));
      return;
    }
    const roles = Array.isArray(result.roles) ? result.roles.filter(isRecord) : [];
    if (roles.length) roles.forEach((role) => results.append(appendRole(role)));
    else results.append(element("p", "empty", "未观察到可结构化的公开岗位。"));
    if (result.status === "partial") results.append(element("p", "results-note", "公开范围未完整；不代表职位开放状态。"));
  }

  function pollSoon(delay) {
    window.clearTimeout(state.pollTimer);
    state.pollTimer = window.setTimeout(poll, delay);
  }

  function discoverSoon(delay) {
    if (state.discovering) {
      state.discoverQueued = true;
      return;
    }
    window.clearTimeout(state.discoverTimer);
    state.discoverTimer = window.setTimeout(discover, delay);
  }

  async function poll() {
    if (state.polling || !validRunId(state.selectedRunId)) return;
    const requestedRunId = state.selectedRunId;
    const generation = state.generation;
    state.polling = true;
    try {
      const snapshot = await request(`${RUNS_PATH}/${requestedRunId}?after=${state.lastEventId}`);
      if (snapshot.run_id !== requestedRunId || requestedRunId !== state.selectedRunId || generation !== state.generation) return;
      const addedEvents = appendEvents(snapshot.events);
      if (Number.isInteger(snapshot.next_event_id) && snapshot.next_event_id >= state.lastEventId) state.lastEventId = snapshot.next_event_id;
      const direct = state.directHydrate;
      state.directHydrate = false;
      state.snapshot = snapshot;
      setConnection("已连接。", snapshot.status || "idle");
      renderControls();
      renderResults();
      refreshJevRecords();
      displayEvents(addedEvents, { direct });
      if (!terminal(snapshot.status)) pollSoon(POLL_MS);
    } catch (error) {
      if (generation !== state.generation || requestedRunId !== state.selectedRunId) return;
      if (error?.code === "invalid_cursor") {
        resetRun(state.selectedRunId, { directHydrate: false });
        setConnection("正在重新读取保留事件。", "disconnected");
        pollSoon(0);
      } else if (error?.code === "not_found") {
        state.pinned = false;
        state.latestSeenId = null;
        state.discoveryBaselineSet = false;
        resetRun(null);
        setHash(null, false);
        setConnection("该历史运行已不在内存中。", "disconnected");
        discoverSoon(0);
      } else {
        setConnection("本机连接暂时中断。", "disconnected");
        pollSoon(1400);
      }
    } finally {
      state.polling = false;
      if (generation !== state.generation && validRunId(state.selectedRunId)) pollSoon(0);
    }
  }

  async function discover() {
    if (state.discovering) {
      state.discoverQueued = true;
      return;
    }
    const generation = state.generation;
    state.discovering = true;
    try {
      const response = await request(RUNS_PATH);
      if (generation !== state.generation) return;
      const latestRunId = validRunId(response.latest_run_id) ? response.latest_run_id : null;
      const latestSummary = Array.isArray(response.runs)
        ? response.runs.find((run) => isRecord(run) && run.run_id === latestRunId)
        : null;
      if (!state.pinned && !state.discoveryBaselineSet) {
        state.discoveryBaselineSet = true;
        state.latestSeenId = latestRunId;
        if (latestRunId && active(latestSummary?.status)) {
          selectRun(latestRunId, false);
        }
      } else if (!state.pinned && latestRunId !== state.latestSeenId) {
        state.latestSeenId = latestRunId;
        if (latestRunId) selectRun(latestRunId, false);
      }
      if (!state.pinned && !state.selectedRunId) {
        setConnection("等待新采集。", "idle");
        renderControls();
      }
    } catch {
      if (generation === state.generation) setConnection("无法连接本机监控服务。", "disconnected");
    } finally {
      state.discovering = false;
      const queued = state.discoverQueued;
      state.discoverQueued = false;
      discoverSoon(queued ? 0 : DISCOVER_MS);
    }
  }

  function followAcquisition() {
    state.pinned = false;
    state.latestSeenId = null;
    state.discoveryBaselineSet = false;
    resetRun(null);
    setHash(null, false);
    setConnection("等待新采集。", "idle");
    discoverSoon(0);
  }

  followButton.addEventListener("click", followAcquisition);

  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const initialRunId = hash.get("run_id");
  if (validRunId(initialRunId)) {
    state.pinned = true;
    resetRun(initialRunId, { directHydrate: true });
    setConnection("正在读取历史运行。", "idle");
    pollSoon(0);
  } else {
    renderControls();
    renderResults();
  }
  discoverSoon(0);
})();
