const boolKeys = [
  "regenIfNeeded",
  "sneakyRegen",
  "stockpile",
  "greedLong",
  "timeConstraint",
  "cyberbullying",
  "mistakes",
  "burstType",
  "spamType",
  "dynamicRate",
  "dynamicPauses",
  "dynamicMistakes",
];

const numericKeys = [
  "minWait",
  "maxWait",
  "mistakePause",
  "miniPause",
  "minWpm",
  "maxWpm",
  "spamWpm",
  "burstChance",
  "minMistakeChance",
  "maxMistakeChance",
  "spamChance",
  "jitterPercent",
];

const defaultSettings = {
  selectMode: "common",
  regenIfNeeded: true,
  sneakyRegen: true,
  stockpile: true,
  greedLong: false,
  timeConstraint: true,
  cyberbullying: false,
  mistakes: true,
  burstType: true,
  spamType: true,
  dynamicRate: false,
  dynamicPauses: true,
  dynamicMistakes: true,
  minWait: 1,
  maxWait: 3.2,
  mistakePause: 0.1,
  miniPause: 0.33,
  minWpm: 70,
  maxWpm: 120,
  spamWpm: 1000,
  burstChance: 0.5,
  minMistakeChance: 0.01,
  maxMistakeChance: 0.15,
  spamChance: 0.1,
  jitterPercent: 0.5,
};

let csrfToken = "";
let heartbeatTimer = null;

function setStatus(message, isError = false) {
  const status = document.getElementById("status");
  status.textContent = message;
  status.style.color = isError ? "#ff9b9b" : "";
}

function parseLines(raw) {
  return raw
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

function applySettings(settings) {
  document.getElementById("selectMode").value = settings.selectMode ?? defaultSettings.selectMode;
  for (const key of boolKeys) {
    document.getElementById(key).checked = Boolean(settings[key]);
  }
  for (const key of numericKeys) {
    document.getElementById(key).value = settings[key] ?? defaultSettings[key];
  }
}

function getPayload() {
  const roomcode = document.getElementById("roomcode").value.trim().toUpperCase();
  if (!/^[A-Z]{4}$/.test(roomcode)) {
    throw new Error("Room code must be exactly 4 letters.");
  }

  const payload = {
    username: document.getElementById("username").value.trim(),
    roomcode,
    dictionaries: parseLines(document.getElementById("dictionaries").value),
    invalid: parseLines(document.getElementById("invalid").value),
    proxies: parseLines(document.getElementById("proxies").value),
    selectMode: document.getElementById("selectMode").value,
  };

  for (const key of boolKeys) {
    payload[key] = document.getElementById(key).checked;
  }
  for (const key of numericKeys) {
    const num = Number(document.getElementById(key).value);
    if (!Number.isFinite(num)) {
      throw new Error(`Invalid number for ${key}`);
    }
    payload[key] = num;
  }
  return payload;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || data.message || "Request failed");
  }
  return data;
}

async function loadInitialData() {
  const csrfData = await fetchJson("/api/csrf");
  csrfToken = csrfData.csrfToken;
  const settings = await fetchJson("/api/settings");
  applySettings({ ...defaultSettings, ...settings });
  setStatus("Ready.");
}

function startHeartbeat() {
  stopHeartbeat();
  heartbeatTimer = window.setInterval(async () => {
    try {
      await fetchJson("/api/heartbeat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: "{}",
      });
    } catch (error) {
      setStatus(`Heartbeat failed: ${error.message}`, true);
      stopHeartbeat();
    }
  }, 2000);
}

function stopHeartbeat() {
  if (heartbeatTimer !== null) {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }
}

async function launchBot() {
  try {
    const payload = getPayload();
    setStatus("Launching bot...");
    const result = await fetchJson("/api/launch", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(payload),
    });
    setStatus(result.message || "Bot launched.");
    startHeartbeat();
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function stopBot() {
  try {
    const result = await fetchJson("/api/stop", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: "{}",
    });
    stopHeartbeat();
    setStatus(result.message || "Bot stopped.");
  } catch (error) {
    setStatus(error.message, true);
  }
}

document.getElementById("launchBtn").addEventListener("click", launchBot);
document.getElementById("stopBtn").addEventListener("click", stopBot);

loadInitialData().catch((error) => {
  setStatus(`Startup error: ${error.message}`, true);
});
