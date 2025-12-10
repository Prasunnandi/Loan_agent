// chat.js

// ---- Session & DOM Elements ----
let sessionId = Math.random().toString(36).substring(2);

const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const uploadBtn = document.getElementById("upload-btn");
const salaryInput = document.getElementById("salary-slip");
const downloadBtn = document.getElementById("download-btn");
const themeToggle = document.getElementById("theme-toggle");

// Snapshot elements (right panel)
const snapName = document.getElementById("snap-name");
const snapPhone = document.getElementById("snap-phone");
const snapAmount = document.getElementById("snap-amount");
const snapTenure = document.getElementById("snap-tenure");
const snapEmi = document.getElementById("snap-emi");
const statusBadge = document.getElementById("status-badge");

// Stage indicator elements (top-right header)
const stageProfile = document.getElementById("stage-profile");
const stageOffer = document.getElementById("stage-offer");
const stageKyc = document.getElementById("stage-kyc");
const stageDecision = document.getElementById("stage-decision");

// ---- Theme handling ----
function applyTheme(theme) {
  document.body.dataset.theme = theme;
  try {
    localStorage.setItem("theme", theme);
  } catch (e) {}
  if (themeToggle) themeToggle.textContent = theme === "light" ? "Dark" : "Light";
}

const savedTheme = (function () {
  try {
    return localStorage.getItem("theme") || "dark";
  } catch (e) {
    return "dark";
  }
})();
applyTheme(savedTheme);

// ---- Stage Progress Logic ----
function setStage(stageKey) {
  const map = {
    profile: stageProfile,
    offer: stageOffer,
    kyc: stageKyc,
    decision: stageDecision,
  };

  // Clear all active states
  Object.values(map).forEach((el) => {
    if (!el) return;
    el.classList.remove("stage-active-step");
    const dot = el.querySelector(".stage-dot");
    if (dot) dot.classList.remove("stage-active");
  });

  const active = map[stageKey];
  if (!active) return;

  active.classList.add("stage-active-step");
  const dot = active.querySelector(".stage-dot");
  if (dot) dot.classList.add("stage-active");

  // Small pulse animation
  active.classList.add("stage-pulse");
  setTimeout(() => active.classList.remove("stage-pulse"), 450);
}

/**
 * Map backend conversation state → stage name.
 * INIT / ASK_NAME / ASK_PHONE → profile
 * ASK_LOAN_AMOUNT / SALES    → offer
 * ASK_SALARY / ASK_PAN / WAIT_UPLOAD → kyc
 * UNDERWRITE / APPROVED / REJECTED  → decision
 */
function setStageFromState(state) {
  switch (state) {
    case "INIT":
    case "ASK_NAME":
    case "ASK_PHONE":
      setStage("profile");
      break;

    case "ASK_LOAN_AMOUNT":
    case "SALES":
      setStage("offer");
      break;

    case "ASK_SALARY":
    case "ASK_PAN":
    case "WAIT_UPLOAD":
      setStage("kyc");
      break;

    case "UNDERWRITE":
    case "APPROVED":
    case "REJECTED":
      setStage("decision");
      break;

    default:
      // keep whatever was active
      break;
  }
}

// ---- Utility: Append Message to Chat (with optional chips) ----
function appendMessage(text, sender, chips = null) {
  const msg = document.createElement("div");
  msg.classList.add("message", sender);

  // Bubble
  const bubble = document.createElement("div");
  bubble.classList.add("bubble");
  bubble.innerHTML = (text || "").replace(/\n/g, "<br>");
  msg.appendChild(bubble);

  // Chips (buttons inside chat) – e.g. tenure / quick replies
  if (chips && Array.isArray(chips) && chips.length > 0) {
    const chipWrap = document.createElement("div");
    chipWrap.classList.add("chat-chips");

    chips.forEach((chip) => {
      const btn = document.createElement("button");
      btn.className = "chip-btn";
      btn.innerText = chip.label;
      btn.onclick = () => sendMessage(chip.value);
      chipWrap.appendChild(btn);
    });

    msg.appendChild(chipWrap);
  }

  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;

  if (sender === "bot") {
    updateSnapshotFromBot(text);
  }
}

// ---- Snapshot Logic (Parse Bot Replies) ----
function updateSnapshotFromBot(text) {
  if (!text) return;
  const lower = text.toLowerCase();

  // Try to parse loan details from bot reply
  if (
    text.includes("Loan Amount") ||
    text.includes("Loan details") ||
    text.includes("offer")
  ) {
    const amt = text.match(/Loan Amount[^₹]*₹?([\d,]+)/i);
    const ten = text.match(/Tenure[^0-9]*(\d+)\s*months/i);
    const emi = text.match(/EMI[^₹]*₹?([\d,]+)/i);

    if (amt && snapAmount) snapAmount.textContent = "₹" + amt[1];
    if (ten && snapTenure) snapTenure.textContent = ten[1] + " months";
    if (emi && snapEmi) snapEmi.textContent = "₹" + emi[1];
  }

  if (!statusBadge) return;

  const looksRejected =
    lower.includes("unfortunately") ||
    lower.includes("doesn’t meet") ||
    lower.includes("doesnt meet") ||
    lower.includes("not approved") ||
    lower.includes("rejected");

  const looksApproved =
    (lower.includes("eligible") || lower.includes("approved")) && !looksRejected;

  if (looksApproved) {
    statusBadge.textContent = "Approved";
    statusBadge.className = "status-pill status-approved";
  } else if (looksRejected) {
    statusBadge.textContent = "Rejected";
    statusBadge.className = "status-pill status-rejected";
  }
}

// ---- Update Snapshot from User Messages ----
function updateSnapshotFromUser(message) {
  const trimmed = (message || "").trim();
  if (!trimmed) return;

  const digitsOnly = trimmed.replace(/\D/g, "");
  const lower = trimmed.toLowerCase();

  // Commands / greetings we should NOT treat as a name
  const controlWords = ["menu", "main menu", "restart", "start over"];
  const greetingWords = ["hi", "hello", "hey"];

  const isControl = controlWords.includes(lower);
  const isGreeting = greetingWords.includes(lower);

  // --- Name logic ---
  if (snapName && !digitsOnly) {
    const currentRaw = (snapName.textContent || "—").trim().toLowerCase();
    const currentIsPlaceholder =
      currentRaw === "—" ||
      controlWords.includes(currentRaw) ||
      greetingWords.includes(currentRaw);

    if (!isControl && !isGreeting && currentIsPlaceholder) {
      snapName.textContent = trimmed;
    }
  }

  // --- Phone logic ---
  if (snapPhone && digitsOnly.length >= 10) {
    snapPhone.textContent = digitsOnly;
  }
}

// ---- Core: Send Message to Backend ----
async function sendMessage(forcedText) {
  const raw = forcedText !== undefined ? forcedText : userInput.value;
  const message = (raw || "").trim();
  if (!message) return;

  // UI: disable input while sending
  if (sendBtn) {
    sendBtn.disabled = true;
    sendBtn.textContent = "Sending…";
  }
  if (userInput) userInput.disabled = true;

  appendMessage(message, "user");
  userInput.value = "";

  // Update snapshot from user side (name & phone)
  updateSnapshotFromUser(message);

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    if (!res.ok) {
      appendMessage("⚠️ Sorry, something went wrong on the server.", "bot");
      return;
    }

    const data = await res.json();

    // Animate stage based on backend state
    if (data.state) {
      setStageFromState(data.state);
    }

    // Decide if we should show chips in this bot reply
    let chips = null;

    if (data.state === "SALES") {
      chips = [
        { label: "12m", value: "make it 12 months" },
        { label: "24m", value: "make it 24 months" },
        { label: "36m", value: "make it 36 months" },
        { label: "48m", value: "make it 48 months" },
        { label: "60m", value: "make it 60 months" },
        { label: "OK", value: "ok" },
        { label: "EMI too high", value: "emi too high" },
        { label: "Menu", value: "menu" },
      ];
    }

    appendMessage(data.reply, "bot", chips);

    if (data.state === "APPROVED") {
      downloadBtn.disabled = false;
    } else if (data.state === "INIT" || data.state === "ASK_NAME") {
      downloadBtn.disabled = true;
    }
  } catch (err) {
    console.error(err);
    appendMessage("⚠️ Network error. Please try again.", "bot");
  } finally {
    if (sendBtn) {
      sendBtn.disabled = false;
      sendBtn.textContent = "Send";
    }
    if (userInput) {
      userInput.disabled = false;
      userInput.focus();
    }
  }
}

// ---- Upload Salary Slip ----
async function uploadSlip() {
  const file = salaryInput.files[0];
  if (!file) {
    appendMessage("Please select a salary slip file first.", "bot");
    return;
  }

  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("file", file);

  if (uploadBtn) {
    uploadBtn.disabled = true;
    uploadBtn.textContent = "Uploading…";
  }

  try {
    const res = await fetch("/upload", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      appendMessage("⚠️ Upload failed. Please try again.", "bot");
      return;
    }

    const data = await res.json();

    if (data.state) {
      setStageFromState(data.state);
    }

    appendMessage(data.reply, "bot");

    if (data.state === "APPROVED") {
      downloadBtn.disabled = false;
    }
  } catch (err) {
    console.error(err);
    appendMessage("⚠️ Network error during upload. Please try again.", "bot");
  } finally {
    if (uploadBtn) {
      uploadBtn.disabled = false;
      uploadBtn.textContent = "Upload & Run Eligibility";
    }
  }
}

// ---- Event Listeners ----
sendBtn.addEventListener("click", () => sendMessage());
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});
uploadBtn.addEventListener("click", uploadSlip);

downloadBtn.addEventListener("click", () => {
  window.open(`/sanction_letter/${sessionId}`, "_blank");
});

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const next = document.body.dataset.theme === "light" ? "dark" : "light";
    applyTheme(next);
  });
}

// ---- Initial Greeting ----
fetch("/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: "", session_id: sessionId }),
})
  .then((res) => res.json())
  .then((data) => {
    appendMessage(data.reply, "bot");
    if (data.state) setStageFromState(data.state);
  })
  .catch((err) => {
    console.error(err);
    appendMessage("⚠️ Unable to start conversation. Please refresh.", "bot");
  });

// ---- Quick Tenure Buttons: (still usable from outside if needed) ----
function quickTenure(months) {
  const text = `make it ${months} months`;
  sendMessage(text);
}

// ---- Quick Reply Chips (OK / EMI too high / Menu) ----
function quickReply(text) {
  sendMessage(text);
}

// ---- Return to Menu Button ----
function returnToMenu() {
  chatBox.innerHTML = "";

  if (snapName) snapName.textContent = "—";
  if (snapPhone) snapPhone.textContent = "—";
  if (snapAmount) snapAmount.textContent = "—";
  if (snapTenure) snapTenure.textContent = "—";
  if (snapEmi) snapEmi.textContent = "—";

  if (statusBadge) {
    statusBadge.textContent = "Draft";
    statusBadge.className = "status-pill status-idle";
  }

  downloadBtn.disabled = true;

  sendMessage("menu");
}

// Expose functions globally (for onclick in HTML)
window.quickTenure = quickTenure;
window.quickReply = quickReply;
window.returnToMenu = returnToMenu;
window.appendMessage = appendMessage;
