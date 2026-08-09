export default function(component) {
  const { parentElement, data, setTriggerValue } = component;
  const payload = data || {};

  let root = parentElement.querySelector(".coco-root");
  if (!root) {
    // Abort previous listeners if Streamlit remounts without calling cleanup.
    if (parentElement._cocoAbort) {
      parentElement._cocoAbort.abort();
    }
    const abort = new AbortController();
    parentElement._cocoAbort = abort;

    parentElement.innerHTML = `
      <div class="coco-root">
        <div class="coco-header">
          <div>
            <div class="coco-title"></div>
            <div class="coco-meta"></div>
          </div>
          <div class="coco-status"></div>
        </div>
        <div class="coco-banner" hidden></div>
        <div class="coco-transcript" id="coco-transcript"></div>
        <div class="coco-error" hidden></div>
        <div class="coco-input-row">
          <textarea class="coco-textarea" id="coco-prompt"></textarea>
          <div class="coco-actions">
            <button class="coco-btn" id="coco-stop" type="button">Stop</button>
            <button class="coco-btn primary" id="coco-send" type="button">Send</button>
          </div>
        </div>
      </div>
    `;
    root = parentElement.querySelector(".coco-root");
    bindActions(parentElement, setTriggerValue, abort.signal);
  }

  root.style.height = `${payload.height || 500}px`;

  const titleEl = root.querySelector(".coco-title");
  const metaEl = root.querySelector(".coco-meta");
  const statusEl = root.querySelector(".coco-status");
  const bannerEl = root.querySelector(".coco-banner");
  const errorEl = root.querySelector(".coco-error");
  const promptEl = root.querySelector("#coco-prompt");

  if (titleEl) titleEl.textContent = payload.header?.title || "CoCo";
  if (metaEl) metaEl.textContent = formatMeta(payload.header);
  if (statusEl) {
    statusEl.textContent = payload.status || "idle";
    statusEl.className = `coco-status ${payload.status || "idle"}`;
  }
  if (bannerEl) {
    const showPlan = payload.header?.permission_mode === "plan";
    bannerEl.hidden = !showPlan;
    if (showPlan) {
      bannerEl.innerHTML = "";
      const text = document.createElement("span");
      text.textContent = "Plan mode — no edits until you execute.";
      bannerEl.appendChild(text);
      const pending = payload.pending_approval;
      const pendingExit =
        pending &&
        String(pending.tool_name || "")
          .toLowerCase()
          .replace(/[^a-z0-9]/g, "") === "exitplanmode";
      if (!pendingExit) {
        const btn = document.createElement("button");
        btn.className = "coco-btn primary coco-banner-execute";
        btn.type = "button";
        btn.textContent = "Execute plan";
        btn.addEventListener(
          "click",
          () => setTriggerValue("execute_plan", { prompt: "Execute the approved plan." }),
          parentElement._cocoAbort ? { signal: parentElement._cocoAbort.signal } : undefined,
        );
        bannerEl.appendChild(btn);
      }
    }
  }
  if (errorEl) {
    errorEl.hidden = !payload.last_error;
    errorEl.textContent = payload.last_error || "";
  }
  if (promptEl instanceof HTMLTextAreaElement && !promptEl.placeholder) {
    promptEl.placeholder = payload.placeholder || "Ask CoCo about your data…";
  }

  renderTranscript(root.querySelector("#coco-transcript"), payload, setTriggerValue);
  updateActions(root, payload);

  // CCv2 skill: return cleanup to remove listeners / tear down DOM on unmount.
  return () => {
    if (parentElement._cocoAbort) {
      parentElement._cocoAbort.abort();
      delete parentElement._cocoAbort;
    }
    const mounted = parentElement.querySelector(".coco-root");
    if (mounted) mounted.remove();
  };
}

function renderTranscript(container, payload, setTriggerValue) {
  if (!container) return;

  const transcript = payload.transcript || [];
  const isStreaming = payload.status === "running" || payload.needs_polling;

  container.innerHTML = "";
  if (!transcript.length) {
    container.innerHTML = `<div class="coco-empty">Start a conversation with CoCo.</div>`;
    return;
  }

  let lastTextIndex = -1;
  for (let i = 0; i < transcript.length; i += 1) {
    if (transcript[i].kind === "text" || transcript[i].role === "user") {
      lastTextIndex = i;
    }
  }

  transcript.forEach((item, index) => {
    if (item.role === "user") {
      container.appendChild(createMessage("user", item.content || ""));
      return;
    }
    if (item.kind === "text") {
      const streaming = isStreaming && index === lastTextIndex;
      container.appendChild(createMessage("assistant", item.content || "", streaming));
      return;
    }
    if (item.kind === "tool") {
      container.appendChild(
        createToolCard(item, payload.show_tool_details !== false),
      );
      return;
    }
    if (item.kind === "structured_output" && payload.show_structured_inline !== false) {
      container.appendChild(createStructuredCard(item.content));
      return;
    }
    if (item.kind === "approval") {
      container.appendChild(
        createApprovalCard(
          item,
          payload.pending_approval,
          setTriggerValue,
          Boolean(payload.debug_mode),
        ),
      );
    }
  });

  container.scrollTop = container.scrollHeight;
}

function createMessage(role, content, streaming = false) {
  const el = document.createElement("div");
  el.className = `coco-message ${role}${streaming ? " coco-streaming" : ""}`;
  el.textContent = content;
  if (streaming) {
    const cursor = document.createElement("span");
    cursor.className = "coco-cursor";
    cursor.textContent = " ▍";
    el.appendChild(cursor);
  }
  return el;
}

function normalizeToolName(name) {
  return String(name || "")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}

function toolFamily(name) {
  const n = normalizeToolName(name);
  const map = {
    askuserquestion: "ask_user",
    sql: "sql",
    sqlexecute: "sql",
    sqlquery: "sql",
    snowflakesql: "sql",
    runsql: "sql",
    read: "read",
    write: "write",
    edit: "edit",
    bash: "bash",
    shell: "bash",
    glob: "glob",
    grep: "grep",
    exitplanmode: "exit_plan",
  };
  return map[n] || "generic";
}

function statusLabel(status) {
  if (status === "running") return "Running";
  if (status === "completed") return "Completed";
  if (status === "error") return "Failed";
  return status || "Running";
}

function firstStr(obj, keys) {
  if (!obj || typeof obj !== "object") return "";
  for (const key of keys) {
    const value = obj[key];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return "";
}

function extractSqlText(input) {
  const direct = firstStr(input, ["query", "command", "sql", "statement", "text"]);
  if (direct) return direct;
  for (const key of ["input", "arguments", "params"]) {
    const nested = input?.[key];
    if (nested && typeof nested === "object") {
      const found = extractSqlText(nested);
      if (found) return found;
    }
  }
  return "";
}

function extractPath(input) {
  return firstStr(input, ["path", "file_path", "filePath", "filename", "file", "target"]);
}

function truncate(text, limit = 4000) {
  const value = String(text || "");
  return value.length > limit ? `${value.slice(0, limit)}\n…` : value;
}

function createCardShell(titleText, { open = false } = {}) {
  const card = document.createElement("details");
  card.className = "coco-tool-card";
  if (open) card.open = true;
  const summary = document.createElement("summary");
  summary.className = "coco-tool-summary";
  summary.textContent = titleText;
  card.appendChild(summary);
  const body = document.createElement("div");
  body.className = "coco-tool-card-body";
  card.appendChild(body);
  card._body = body;
  return card;
}

function cardBody(card) {
  return card._body || card;
}

function appendPre(card, text, className = "coco-sql-query") {
  if (!text) return;
  const pre = document.createElement("pre");
  pre.className = className;
  pre.textContent = text;
  cardBody(card).appendChild(pre);
}

function appendMeta(card, text) {
  const meta = document.createElement("div");
  meta.className = "coco-meta";
  meta.textContent = text;
  cardBody(card).appendChild(meta);
}

function createAskUserCard(item) {
  const questions = Array.isArray(item.input?.questions) ? item.input.questions : [];
  const headers = questions.map(
    (q, idx) => q.header || q.question || `Question ${idx + 1}`,
  );
  const summary = headers.length ? headers.join(", ") : "clarifying question";
  const status = item.status || "running";
  const card = createCardShell(
    `Question · ${statusLabel(status)}${summary ? ` · ${summary}` : ""}`,
    { open: status === "error" },
  );
  if (status === "running") appendMeta(card, `Waiting for your answer — ${summary}`);
  else if (status === "completed") appendMeta(card, `Answered — ${summary}`);
  else if (status === "error") appendMeta(card, `Question cancelled or failed — ${summary}`);
  else appendMeta(card, summary);
  return card;
}

function createSqlCard(item) {
  const status = item.status || "running";
  const card = createCardShell(`SQL · ${statusLabel(status)}`, {
    open: status === "error",
  });
  appendPre(card, extractSqlText(item.input || {}));
  if (status === "running") appendMeta(card, "Executing query…");
  else if (item.result != null) {
    appendPre(
      card,
      typeof item.result === "string" ? item.result : JSON.stringify(item.result, null, 2),
      "coco-tool-body",
    );
  }
  return card;
}

function createPathCard(item, familyLabel, runningText) {
  const status = item.status || "running";
  const path = extractPath(item.input || {});
  const card = createCardShell(
    path ? `${familyLabel} · ${statusLabel(status)} · ${path}` : `${familyLabel} · ${statusLabel(status)}`,
    { open: status === "error" },
  );
  if (familyLabel === "Write") {
    appendPre(card, truncate(firstStr(item.input || {}, ["content", "new_str", "newString", "text"]), 2500));
  }
  if (familyLabel === "Edit") {
    const oldText = firstStr(item.input || {}, ["old_string", "oldString", "old_str"]);
    const newText = firstStr(item.input || {}, ["new_string", "newString", "new_str"]);
    if (oldText) {
      appendMeta(card, "Before");
      appendPre(card, truncate(oldText, 1500));
    }
    if (newText) {
      appendMeta(card, "After");
      appendPre(card, truncate(newText, 1500));
    }
  }
  if (status === "running") appendMeta(card, runningText);
  else if (typeof item.result === "string" && item.result) appendPre(card, truncate(item.result), "coco-tool-body");
  return card;
}

function createBashCard(item) {
  const status = item.status || "running";
  const command = firstStr(item.input || {}, ["command", "cmd"]);
  const shortCmd =
    command && command.length > 48 ? `${command.slice(0, 48)}…` : command;
  const card = createCardShell(
    shortCmd
      ? `Bash · ${statusLabel(status)} · ${shortCmd}`
      : `Bash · ${statusLabel(status)}`,
    { open: status === "error" },
  );
  appendPre(card, command);
  if (status === "running") appendMeta(card, "Running command…");
  else if (typeof item.result === "string" && item.result) appendPre(card, truncate(item.result), "coco-tool-body");
  return card;
}

function createPatternCard(item, familyLabel, runningText) {
  const status = item.status || "running";
  const pattern = firstStr(item.input || {}, ["pattern", "glob_pattern", "glob", "regex"]);
  const path = extractPath(item.input || {});
  const meta = [pattern && `\`${pattern}\``, path && `in \`${path}\``].filter(Boolean).join(" · ");
  const resultText = typeof item.result === "string" ? item.result : "";
  const lines = resultText
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => {
      const lower = line.toLowerCase();
      return !(
        lower.startsWith("grepped:") ||
        lower.startsWith("found ") ||
        lower.startsWith("matches for")
      );
    });
  const count = lines.length;
  let countLabel = "";
  if (status === "completed" && resultText.trim()) {
    countLabel =
      familyLabel === "Grep"
        ? count === 1
          ? "1 match"
          : `${count} matches`
        : count === 1
          ? "1 file"
          : `${count} files`;
  }
  const titleBits = [
    `${familyLabel} · ${statusLabel(status)}`,
    meta ? meta.replace(/`/g, "") : "",
    countLabel,
  ].filter(Boolean);
  const card = createCardShell(titleBits.join(" · "), { open: status === "error" });
  if (status === "running") {
    appendMeta(card, runningText);
    return card;
  }
  if (status === "error") {
    appendMeta(card, typeof item.result === "string" ? truncate(item.result, 200) : "Failed");
    return card;
  }
  if (!resultText.trim()) {
    appendMeta(card, familyLabel === "Grep" ? "No matches." : "No files found.");
    return card;
  }
  if (countLabel) appendMeta(card, countLabel);
  return card;
}

function createGenericCard(item) {
  const status = item.status || "running";
  const name = item.name || "Tool";
  const card = createCardShell(`${name} · ${statusLabel(status)}`, {
    open: status === "error",
  });
  const input = item.input || {};
  Object.keys(input)
    .slice(0, 6)
    .forEach((key) => {
      const value = input[key];
      const rendered =
        value && typeof value === "object"
          ? `(${Array.isArray(value) ? "array" : "object"})`
          : truncate(String(value ?? ""), 120);
      appendMeta(card, `${key}: ${rendered}`);
    });
  if (status === "running") appendMeta(card, "Running…");
  else if (typeof item.result === "string" && item.result) appendPre(card, truncate(item.result), "coco-tool-body");
  return card;
}

function createToolCard(item) {
  const family = toolFamily(item.name);
  if (family === "ask_user") return createAskUserCard(item);
  if (family === "sql") return createSqlCard(item);
  if (family === "read") return createPathCard(item, "Read", "Reading file…");
  if (family === "write") return createPathCard(item, "Write", "Writing file…");
  if (family === "edit") return createPathCard(item, "Edit", "Applying edit…");
  if (family === "bash") return createBashCard(item);
  if (family === "glob") return createPatternCard(item, "Glob", "Searching files…");
  if (family === "grep") return createPatternCard(item, "Grep", "Searching content…");
  if (family === "exit_plan") {
    const status = item.status || "running";
    const card = createCardShell(`Plan · ${statusLabel(status)}`, {
      open: status === "error",
    });
    appendPre(card, firstStr(item.input || {}, ["plan", "message", "text"]));
    return card;
  }
  return createGenericCard(item);
}

function createStructuredCard(content) {
  const details = document.createElement("details");
  details.className = "coco-structured";
  details.open = true;
  details.innerHTML = `<summary>Structured output</summary>`;
  const pre = document.createElement("pre");
  pre.textContent = JSON.stringify(content, null, 2);
  details.appendChild(pre);
  return details;
}

function createApprovalCard(item, pending, setTriggerValue, debugMode = false) {
  const card = document.createElement("div");
  card.className = "coco-approval";
  const isPending = pending && pending.request_id === item.id && item.status === "pending";
  const inputBlock = debugMode
    ? `<pre class="coco-tool-body">${escapeHtml(JSON.stringify(item.tool_input || {}, null, 2))}</pre>`
    : "";
  card.innerHTML = `
    <div class="coco-approval-title">Approval required</div>
    <div>Tool: <strong>${escapeHtml(item.tool_name || "")}</strong></div>
    ${inputBlock}
  `;
  if (isPending) {
    const actions = document.createElement("div");
    actions.className = "coco-approval-actions";
    actions.innerHTML = `
      <button class="coco-btn primary" data-action="approve" type="button">Approve once</button>
      <button class="coco-btn" data-action="always" type="button">Always allow ${escapeHtml(item.tool_name || "tool")}</button>
      <button class="coco-btn" data-action="deny" type="button">Deny</button>
    `;
    actions.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      const action = target.getAttribute("data-action");
      if (!action) return;
      if (action === "deny") {
        setTriggerValue("deny_tool", { request_id: item.id, reason: "Denied by user" });
      } else {
        setTriggerValue("approve_tool", { request_id: item.id, always: action === "always" });
      }
    });
    card.appendChild(actions);
  } else {
    const status = document.createElement("div");
    status.className = "coco-meta";
    status.textContent = `Status: ${item.status || "resolved"}`;
    card.appendChild(status);
  }
  return card;
}

function bindActions(root, setTriggerValue, signal) {
  const promptEl = root.querySelector("#coco-prompt");
  const sendEl = root.querySelector("#coco-send");
  const stopEl = root.querySelector("#coco-stop");
  const opts = signal ? { signal } : undefined;

  if (sendEl instanceof HTMLButtonElement) {
    sendEl.addEventListener(
      "click",
      () => {
        if (!(promptEl instanceof HTMLTextAreaElement)) return;
        const text = promptEl.value.trim();
        if (!text) return;
        setTriggerValue("submit_prompt", { text });
        promptEl.value = "";
      },
      opts,
    );
  }

  if (promptEl instanceof HTMLTextAreaElement) {
    promptEl.addEventListener(
      "keydown",
      (event) => {
        if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
          event.preventDefault();
          sendEl?.click();
        }
      },
      opts,
    );
  }

  if (stopEl instanceof HTMLButtonElement) {
    stopEl.addEventListener(
      "click",
      () => setTriggerValue("cancel_run", true),
      opts,
    );
  }
}

function updateActions(root, payload) {
  const sendEl = root.querySelector("#coco-send");
  const stopEl = root.querySelector("#coco-stop");
  const isBusy = ["running", "awaiting_user"].includes(payload.status) || payload.needs_polling;

  if (sendEl instanceof HTMLButtonElement) {
    sendEl.disabled = isBusy;
  }
  if (stopEl instanceof HTMLButtonElement) {
    stopEl.disabled = !isBusy;
  }
}

function formatMeta(header) {
  if (!header) return "";
  const parts = [];
  if (header.model) parts.push(header.model);
  if (header.connection) parts.push(`connection: ${header.connection}`);
  return parts.join(" · ");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
