// Start the backend from 06_Code with: python echo_api.py
// Open index.html in a browser. A future phase will add voice.

const API_BASE_URL = "http://127.0.0.1:8000";

const apiStatus = document.querySelector("#apiStatus");
const apiStatusText = document.querySelector("#apiStatusText");
const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const messages = document.querySelector("#messages");

function setApiStatus(connected, text) {
  apiStatus.classList.toggle("connected", connected);
  apiStatus.classList.toggle("disconnected", !connected);
  apiStatusText.textContent = text;
}

function formatTools(tools) {
  if (!Array.isArray(tools) || tools.length === 0) {
    return "None";
  }

  return tools.join(", ");
}

function appendMessage(role, text, details = null) {
  const row = document.createElement("article");
  row.className = `message ${role}`;

  const label = document.createElement("div");
  label.className = "message-label";
  label.textContent = role === "user" ? "You" : "Echo";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const content = document.createElement("p");
  content.textContent = text;
  bubble.appendChild(content);

  if (details) {
    const disclosure = document.createElement("details");
    disclosure.className = "response-details";

    const summary = document.createElement("summary");
    summary.textContent = "Details";
    disclosure.appendChild(summary);

    const detailList = document.createElement("dl");
    Object.entries(details).forEach(([key, value]) => {
      const term = document.createElement("dt");
      term.textContent = key;
      const definition = document.createElement("dd");
      definition.textContent = value;
      detailList.appendChild(term);
      detailList.appendChild(definition);
    });

    disclosure.appendChild(detailList);
    bubble.appendChild(disclosure);
  }

  row.appendChild(label);
  row.appendChild(bubble);
  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;

  return row;
}

function appendError(text) {
  appendMessage("echo", text, { status: "ERROR" });
}

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    const data = await response.json();
    setApiStatus(data.status === "ok", "Connected");
  } catch (error) {
    setApiStatus(false, "Disconnected");
  }
}

function setWaiting(waiting) {
  sendButton.disabled = waiting;
  messageInput.disabled = waiting;
  sendButton.textContent = waiting ? "Sending" : "Send";
}

async function sendMessage(message) {
  appendMessage("user", message);
  const thinking = appendMessage("echo", "Thinking...");
  setWaiting(true);

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ message })
    });

    let data = {};

    try {
      data = await response.json();
    } catch (error) {
      data = {};
    }

    if (!response.ok || data.status === "ERROR") {
      throw new Error(data.message || `Request failed: ${response.status}`);
    }

    thinking.remove();
    appendMessage("echo", data.answer || "No answer returned.", {
      status: data.status || "UNKNOWN",
      confidence: data.confidence || "UNKNOWN",
      mode: data.mode || "UNKNOWN",
      "selected tools": formatTools(data.selected_tools)
    });
    setApiStatus(true, "Connected");
  } catch (error) {
    thinking.remove();
    appendError(error.message || "Echo API request failed.");
    setApiStatus(false, "Disconnected");
  } finally {
    setWaiting(false);
    messageInput.focus();
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();

  if (!message) {
    return;
  }

  messageInput.value = "";
  sendMessage(message);
});

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

checkHealth();
