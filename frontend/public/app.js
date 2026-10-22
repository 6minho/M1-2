// 엔화 AI 비서 - 바닐라 JS 프론트엔드
const API = (window.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const $ = (sel) => document.querySelector(sel);
const fmt = (n) => Number(n).toLocaleString("ko-KR", { maximumFractionDigits: 2 });

let currentConvId = null;
let editingId = null;
let dataCache = [];

// ---------- 공통 fetch (콜드스타트 안내 포함) ----------
async function api(path, options = {}) {
  const slowTimer = setTimeout(() => ($("#server-banner").hidden = false), 3000);
  try {
    const res = await fetch(API + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = Array.isArray(body.detail)
        ? body.detail.map((d) => d.msg).join(", ")
        : body.detail || res.statusText;
      throw new Error(detail);
    }
    return body;
  } finally {
    clearTimeout(slowTimer);
    $("#server-banner").hidden = true;
  }
}

// ---------- 탭 ----------
document.querySelectorAll(".tab").forEach((btn) =>
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b === btn));
    $("#tab-chat").hidden = btn.dataset.tab !== "chat";
    $("#tab-data").hidden = btn.dataset.tab !== "data";
    if (btn.dataset.tab === "data") loadData();
  })
);

// ---------- 요약 ----------
function renderSummary(s) {
  $("#s-period").textContent = s.period;
  $("#s-count").textContent = `${s.count}개`;
  const trend = $("#s-trend");
  trend.textContent = s.trend;
  trend.className = "val " + (s.trend.startsWith("하락") ? "down" : s.trend.startsWith("상승") ? "up" : "");
  if (!s.metrics) return;
  const m = s.metrics;
  $("#s-latest").textContent = `${fmt(m.latest)}원`;
  $("#s-avg").textContent = `${fmt(m.average)}원`;
  $("#s-range").textContent = `${fmt(m.max)} / ${fmt(m.min)}`;
}

async function loadSummary() {
  try {
    renderSummary(await api("/api/data/summary"));
  } catch (e) {
    $("#s-trend").textContent = "요약을 불러오지 못했어요: " + e.message;
  }
}

// ---------- 채팅 ----------
function addMessage(role, text) {
  $("#chat-empty")?.remove();
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  el.textContent = text;
  $("#messages").appendChild(el);
  $("#messages").scrollTop = $("#messages").scrollHeight;
  return el;
}

function showTyping() {
  const el = addMessage("assistant", "");
  el.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';
  return el;
}

async function sendMessage(text) {
  text = text.trim();
  if (!text) return;
  $("#chat-input").value = "";
  $("#chat-send").disabled = true;
  addMessage("user", text);
  const loading = showTyping();

  try {
    const res = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: text, conversation_id: currentConvId }),
    });
    loading.remove();
    addMessage("assistant", res.reply);
    currentConvId = res.conversation_id;
    renderSummary(res.summary);
    loadConversations();
  } catch (e) {
    loading.remove();
    addMessage("error", "오류: " + e.message);
  } finally {
    $("#chat-send").disabled = false;
    $("#chat-input").focus();
  }
}

$("#chat-form").addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage($("#chat-input").value);
});
document.querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => sendMessage(c.textContent)));

function resetChat() {
  currentConvId = null;
  $("#messages").innerHTML =
    '<div class="empty" id="chat-empty"><p>새 대화를 시작하세요. 저장된 환율 데이터를 바탕으로 답해 드려요.</p></div>';
  highlightConv();
}
$("#new-chat").addEventListener("click", resetChat);

// ---------- 대화 기록 ----------
function highlightConv() {
  document.querySelectorAll("#conv-list li").forEach((li) =>
    li.classList.toggle("active", li.dataset.id === currentConvId)
  );
}

async function loadConversations() {
  const list = $("#conv-list");
  try {
    const convs = await api("/api/conversations");
    list.innerHTML = "";
    if (!convs.length) {
      list.innerHTML = '<li class="conv-empty">아직 대화가 없어요</li>';
      return;
    }
    convs.forEach((c) => {
      const li = document.createElement("li");
      li.dataset.id = c.id;
      li.innerHTML = `<div class="t"></div><span class="meta">${c.message_count}</span><button class="del" title="삭제">×</button>`;
      li.querySelector(".t").textContent = c.title;
      li.addEventListener("click", () => openConversation(c.id));
      li.querySelector(".del").addEventListener("click", async (e) => {
        e.stopPropagation();
        if (!confirm("이 대화를 삭제할까요?")) return;
        await api(`/api/conversations/${c.id}`, { method: "DELETE" });
        if (currentConvId === c.id) resetChat();
        loadConversations();
      });
      list.appendChild(li);
    });
    highlightConv();
  } catch (e) {
    list.innerHTML = `<li class="conv-empty">불러오기 실패: ${e.message}</li>`;
  }
}

async function openConversation(id) {
  try {
    const conv = await api(`/api/conversations/${id}`);
    currentConvId = conv.id;
    $("#messages").innerHTML = "";
    conv.messages.forEach((m) => addMessage(m.role, m.content));
    highlightConv();
  } catch (e) {
    addMessage("error", "대화를 불러오지 못했어요: " + e.message);
  }
}

// ---------- 데이터 관리 (CRUD) ----------
function formMsg(text, ok = true) {
  const el = $("#form-msg");
  el.textContent = text;
  el.className = "form-msg " + (ok ? "ok" : "err");
}

function renderRows(flashId) {
  const tbody = $("#data-rows");
  tbody.innerHTML = "";
  // 최신 날짜가 위로
  [...dataCache].reverse().forEach((d) => {
    const tr = document.createElement("tr");
    if (d.id === flashId) tr.className = "flash";
    tr.innerHTML = `<td>${d.date}</td><td class="num">${fmt(d.value)}</td><td class="memo"></td>
      <td class="actions"><button class="btn small edit">수정</button> <button class="btn small del">삭제</button></td>`;
    tr.querySelector(".memo").textContent = d.memo;
    tr.querySelector(".edit").addEventListener("click", () => startEdit(d));
    tr.querySelector(".del").addEventListener("click", () => removeRow(d));
    tbody.appendChild(tr);
  });
}

async function loadData(flashId) {
  try {
    dataCache = await api("/api/data");
    renderRows(flashId);
  } catch (e) {
    formMsg("목록을 불러오지 못했어요: " + e.message, false);
  }
}

function startEdit(d) {
  editingId = d.id;
  $("#form-title").textContent = `데이터 수정 (${d.date})`;
  $("#f-date").value = d.date;
  $("#f-value").value = d.value;
  $("#f-memo").value = d.memo;
  $("#f-submit").textContent = "저장";
  $("#f-cancel").hidden = false;
  formMsg("");
  $("#f-value").focus();
}

function endEdit() {
  editingId = null;
  $("#data-form").reset();
  $("#form-title").textContent = "새 데이터 추가";
  $("#f-submit").textContent = "추가";
  $("#f-cancel").hidden = true;
}
$("#f-cancel").addEventListener("click", endEdit);

$("#data-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    date: $("#f-date").value,
    value: parseFloat($("#f-value").value),
    memo: $("#f-memo").value.trim(),
  };
  try {
    const saved = editingId
      ? await api(`/api/data/${editingId}`, { method: "PUT", body: JSON.stringify(body) })
      : await api("/api/data", { method: "POST", body: JSON.stringify(body) });
    formMsg(editingId ? `${saved.date} 데이터를 수정했어요.` : `${saved.date} 데이터를 추가했어요.`);
    endEdit();
    await loadData(saved.id);
    loadSummary();
  } catch (err) {
    formMsg("저장 실패: " + err.message, false);
  }
});

async function removeRow(d) {
  if (!confirm(`${d.date} (${fmt(d.value)}원) 데이터를 삭제할까요?`)) return;
  try {
    await api(`/api/data/${d.id}`, { method: "DELETE" });
    formMsg(`${d.date} 데이터를 삭제했어요.`);
    await loadData();
    loadSummary();
  } catch (e) {
    formMsg("삭제 실패: " + e.message, false);
  }
}

// ---------- 시작 ----------
(async function init() {
  // 무료 서버 콜드스타트 대비: 먼저 /health 로 깨운다
  try { await api("/health"); } catch (_) {}
  loadSummary();
  loadConversations();
})();
