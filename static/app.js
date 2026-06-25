const chat = document.getElementById("chat");
const composer = document.getElementById("composer");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const gmailStatus = document.getElementById("gmail-status");
const calendarStatus = document.getElementById("calendar-status");
const gmailConnect = document.getElementById("gmail-connect");
const calendarConnect = document.getElementById("calendar-connect");

let isSending = false;
let authState = { gmail: false, calendar: false };

function scrollToBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function appendMessage(text, type) {
  const el = document.createElement("div");
  el.className = `message message--${type}`;
  el.textContent = text;
  chat.appendChild(el);
  scrollToBottom();
  return el;
}

function formatToolArgs(args) {
  if (!args || Object.keys(args).length === 0) {
    return "{}";
  }
  return JSON.stringify(args, null, 2);
}

function appendToolCalls(toolCalls) {
  if (!toolCalls || toolCalls.length === 0) {
    return;
  }

  const container = document.createElement("div");
  container.className = "tool-calls";

  const heading = document.createElement("div");
  heading.className = "tool-calls__heading";
  heading.textContent =
    toolCalls.length === 1 ? "Tool used" : `${toolCalls.length} tools used`;
  container.appendChild(heading);

  for (const toolCall of toolCalls) {
    const item = document.createElement("details");
    item.className = "tool-call";
    item.open = true;

    const summary = document.createElement("summary");
    summary.className = "tool-call__name";
    summary.textContent = toolCall.name;
    item.appendChild(summary);

    const args = document.createElement("pre");
    args.className = "tool-call__args";
    args.textContent = formatToolArgs(toolCall.args);
    item.appendChild(args);

    if (toolCall.result) {
      const result = document.createElement("pre");
      result.className = "tool-call__result";
      result.textContent = toolCall.result;
      item.appendChild(result);
    }

    container.appendChild(item);
  }

  chat.appendChild(container);
  scrollToBottom();
}

function setServiceStatus(element, connectButton, connected) {
  element.textContent = connected ? "Connected" : "Not connected";
  element.className = `auth-status auth-status--${connected ? "connected" : "disconnected"}`;
  connectButton.hidden = connected;
}

function updateComposerState() {
  const ready = authState.gmail && authState.calendar;
  messageInput.disabled = isSending || !ready;
  sendButton.disabled = isSending || !ready;

  if (!ready) {
    messageInput.placeholder = "Connect Gmail and Calendar to start chatting…";
  } else {
    messageInput.placeholder = "Ask about your email or calendar…";
  }
}

function setLoading(loading) {
  isSending = loading;
  updateComposerState();
  sendButton.textContent = loading ? "Sending…" : "Send";
}

async function loadAuthStatus() {
  try {
    const response = await fetch("/auth/status");
    if (!response.ok) {
      throw new Error("status request failed");
    }

    const data = await response.json();
    authState = {
      gmail: data.gmail.connected,
      calendar: data.calendar.connected,
    };

    setServiceStatus(gmailStatus, gmailConnect, authState.gmail);
    setServiceStatus(calendarStatus, calendarConnect, authState.calendar);
    updateComposerState();

    if (!authState.gmail || !authState.calendar) {
      appendMessage(
        "Connect Gmail and Calendar above before sending messages.",
        "notice",
      );
    }
  } catch {
    gmailStatus.textContent = "Unavailable";
    calendarStatus.textContent = "Unavailable";
    appendMessage("Could not load connection status.", "error");
  }
}

function handleAuthRedirect() {
  const params = new URLSearchParams(window.location.search);
  const service = params.get("auth");
  const status = params.get("status");
  const message = params.get("message");

  if (!service || !status) {
    return;
  }

  const label = service === "gmail" ? "Gmail" : "Calendar";

  if (status === "success") {
    appendMessage(`${label} connected successfully.`, "notice");
  } else {
    appendMessage(
      `${label} connection failed${message ? `: ${message}` : "."}`,
      "error",
    );
  }

  window.history.replaceState({}, "", "/");
}

async function parseErrorDetail(response) {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") {
      return { message: data.detail };
    }
    if (data.detail && typeof data.detail === "object") {
      return data.detail;
    }
    if (Array.isArray(data.detail)) {
      return {
        message: data.detail.map((item) => item.msg || String(item)).join(", "),
      };
    }
  } catch {
    // Fall through to status text.
  }
  return { message: `Request failed (${response.status})` };
}

async function sendMessage(message) {
  const loadingEl = appendMessage("Thinking…", "loading");

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    loadingEl.remove();

    if (!response.ok) {
      const detail = await parseErrorDetail(response);

      if (response.status === 401 && detail.service && detail.auth_url) {
        appendMessage(detail.message || "Authorization required.", "error");
        authState[detail.service] = false;
        if (detail.service === "gmail") {
          setServiceStatus(gmailStatus, gmailConnect, false);
        } else if (detail.service === "calendar") {
          setServiceStatus(calendarStatus, calendarConnect, false);
        }
        updateComposerState();
        return;
      }

      appendMessage(detail.message || "Request failed.", "error");
      return;
    }

    const data = await response.json();
    appendToolCalls(data.tool_calls);
    appendMessage(data.reply, "assistant");
  } catch {
    loadingEl.remove();
    appendMessage("Could not reach the server. Is the API running?", "error");
  }
}

composer.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (isSending || !authState.gmail || !authState.calendar) {
    return;
  }

  const message = messageInput.value.trim();
  if (!message) {
    return;
  }

  appendMessage(message, "user");
  messageInput.value = "";
  messageInput.style.height = "auto";

  setLoading(true);
  try {
    await sendMessage(message);
  } finally {
    setLoading(false);
    if (authState.gmail && authState.calendar) {
      messageInput.focus();
    }
  }
});

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    composer.requestSubmit();
  }
});

messageInput.addEventListener("input", () => {
  messageInput.style.height = "auto";
  messageInput.style.height = `${messageInput.scrollHeight}px`;
});

handleAuthRedirect();
loadAuthStatus();
