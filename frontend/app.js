const state = {
  userId: `U${Math.floor(Math.random() * 90000 + 10000)}`,
  questions: [],
  index: 0,
  events: [],
  questionStartedAt: performance.now(),
  timerId: null,
  activeTimerToken: 0,
  remaining: 0,
  lastResult: null,
};

const stageEl = document.querySelector("#stage");
const stageLabel = document.querySelector("#stageLabel");
const progressFill = document.querySelector("#progressFill");
const scoreList = document.querySelector("#scoreList");
const insightList = document.querySelector("#insightList");
const evidenceList = document.querySelector("#evidenceList");
const reasonList = document.querySelector("#reasonList");
const recommendationList = document.querySelector("#recommendationList");
const profileBox = document.querySelector("#profileBox");
const serverStatus = document.querySelector("#serverStatus");
const radar = document.querySelector("#radar");

async function boot() {
  await checkServer();
  await loadQuestions();
  drawRadar(null);
  renderIntro();
}

async function checkServer() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    serverStatus.textContent = data.model_mode === "xgboost" ? "XGBoost active" : "Fallback model active";
    if (data.gemini_available) serverStatus.textContent += " + Gemini";
  } catch {
    serverStatus.textContent = "Server offline";
  }
}

async function loadQuestions() {
  const response = await fetch(`/api/questions?ts=${Date.now()}`, { cache: "no-store" });
  const payload = await response.json();
  state.questions = payload.questions || [];
  stageLabel.textContent = `${state.questions.length} scenarios`;
}

function renderIntro() {
  clearInterval(state.timerId);
  progressFill.style.width = "0%";
  stageEl.innerHTML = `
    <div class="intro-grid">
      <div class="intro-copy">
        <p class="eyebrow">Timed Scenario Engine</p>
        <h2>Every option has hidden behavioral weights.</h2>
        <p>You will answer ${state.questions.length} timed scenarios. Each scenario has a fixed countdown between 5 and 13 seconds. After every choice, the next scenario appears immediately.</p>
        <div class="actions">
          <button class="btn" id="startAssessment">Start assessment</button>
        </div>
      </div>
      <div class="system-map">
        <span>User</span>
        <span>Timed Scenario</span>
        <span>Weighted Decision</span>
        <span>Feature Engine</span>
        <span>XGBoost</span>
        <span>Dashboard</span>
      </div>
    </div>
  `;
  document.querySelector("#startAssessment").addEventListener("click", () => {
    state.index = 0;
    state.events = [];
    renderQuestion();
  });
}

function renderQuestion() {
  clearInterval(state.timerId);
  state.activeTimerToken += 1;
  const timerToken = state.activeTimerToken;
  const question = state.questions[state.index];
  if (!question) {
    submitScore();
    return;
  }

  state.questionStartedAt = performance.now();
  state.remaining = question.time_limit;
  stageLabel.textContent = `Scenario ${state.index + 1} / ${state.questions.length} - ${question.time_limit}s`;
  progressFill.style.width = `${((state.index + 1) / state.questions.length) * 100}%`;

  stageEl.innerHTML = `
    <div class="question-layout">
      <div class="question-card">
        <div class="question-number">Question ${state.index + 1}</div>
        <div class="question-meta">
          <span>${question.title || "Scenario"}</span>
          <span>${label(question.category)}</span>
          <span>Difficulty ${question.difficulty}/5</span>
          <span>Fixed limit: ${question.time_limit}s</span>
        </div>
        <div class="timer">
          <strong id="timeRemaining">${question.time_limit}</strong>
          <span>seconds left</span>
          <div class="timer-track"><i id="timerFill"></i></div>
        </div>
        <h2>${question.scenario}</h2>
        <p>Choose one strategy. Your option, timing, timeout status, and hidden option weights are logged.</p>
        <div class="mini-log">
          <span>Answered: ${state.events.length}</span>
          <span>Remaining: ${state.questions.length - state.index}</span>
        </div>
      </div>
      <div class="option-grid">
        ${question.options.map(optionTemplate).join("")}
      </div>
    </div>
  `;

  stageEl.querySelectorAll("[data-option]").forEach((button) => {
    button.addEventListener("click", () => selectOption(button.dataset.option));
  });

  tickTimer(timerToken);
  state.timerId = setInterval(() => tickTimer(timerToken), 250);
}

function optionTemplate(option) {
  return `
    <button class="option-card" data-option="${option.key}">
      <span class="option-key">${option.key}</span>
      <strong>${option.label} choice</strong>
      <em>${option.text}</em>
    </button>
  `;
}

function tickTimer(timerToken) {
  if (timerToken !== state.activeTimerToken) return;
  const question = state.questions[state.index];
  if (!question) return;
  const timeEl = document.querySelector("#timeRemaining");
  const fillEl = document.querySelector("#timerFill");
  if (!timeEl || !fillEl) return;
  const elapsed = (performance.now() - state.questionStartedAt) / 1000;
  const remaining = Math.max(0, question.time_limit - elapsed);
  state.remaining = remaining;
  timeEl.textContent = Math.ceil(remaining);
  fillEl.style.width = `${Math.max(0, (remaining / question.time_limit) * 100)}%`;
  if (remaining <= 0) {
    clearInterval(state.timerId);
    logDecision("TIMEOUT", true);
    advanceQuestion();
  }
}

function selectOption(optionKey) {
  clearInterval(state.timerId);
  stageEl.querySelectorAll("[data-option]").forEach((button) => {
    button.disabled = true;
    if (button.dataset.option === optionKey) button.classList.add("selected");
  });
  logDecision(optionKey, false);
  setTimeout(advanceQuestion, 140);
}

function logDecision(optionKey, timeout) {
  const question = state.questions[state.index];
  const option = question.options.find((item) => item.key === optionKey);
  const timeTaken = Number(((performance.now() - state.questionStartedAt) / 1000).toFixed(3));
  state.events.push({
    type: timeout ? "timeout" : "decision",
    user_id: state.userId,
    question_id: question.id,
    category: question.category,
    selected_option: optionKey,
    time_taken: timeout ? question.time_limit : Math.min(timeTaken, question.time_limit),
    time_limit: question.time_limit,
    decision_under_pressure: timeTaken / question.time_limit >= 0.65,
    hint_used: option ? option.hint_used : false,
    path_unlocked: option ? option.path_unlock : false,
    option_intent: option ? option.intent : "timeout",
    option_weights: option ? option.weights : { risk: 0, information: 0, explore: 0, curiosity: 0, pressure: 1 },
    timeout,
  });
}

function advanceQuestion() {
  state.index += 1;
  progressFill.style.width = `${(state.index / state.questions.length) * 100}%`;
  if (state.index >= state.questions.length) {
    submitScore();
    return;
  }
  renderQuestion();
}

async function submitScore() {
  clearInterval(state.timerId);
  progressFill.style.width = "100%";
  stageLabel.textContent = "Scoring";
  stageEl.innerHTML = `
    <div class="transition-card">
      <strong>Generating TCBIS report</strong>
      <span>Feature engineering and XGBoost scoring are running.</span>
    </div>
  `;

  const response = await fetch("/api/score", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: state.userId, events: state.events }),
  });
  const result = await response.json();
  if (!response.ok) {
    stageEl.innerHTML = `<div class="transition-card"><strong>Scoring failed</strong><span>${result.error || "Unknown error"}</span></div>`;
    return;
  }
  state.lastResult = result;
  renderDashboard(result);
  renderReport(result);
}

function renderReport(result) {
  const explanations = Object.entries(result.report.trait_explanations)
    .map(([key, value]) => `<li><strong>${label(key)}</strong>: ${value}</li>`)
    .join("");
  const reasons = renderReasonCards(result.report.score_reasons || {});
  stageEl.innerHTML = `
    <div class="report-stage">
      <div>
        <p class="eyebrow">Assessment Complete</p>
        <h2>${result.report.profile}</h2>
        <p>${result.report.headline}</p>
      </div>
      <div class="report-grid">
        <div class="report-panel"><strong>Reliability</strong><span>${result.report.reliability.level} (${result.report.reliability.score}%)</span></div>
        <div class="report-panel"><strong>Model Mode</strong><span>${result.model_mode}</span></div>
        <div class="report-panel"><strong>Events</strong><span>${result.features.event_count}</span></div>
      </div>
      <ul class="explanation-list">${explanations}</ul>
      <div class="reason-grid">${reasons}</div>
      <div class="actions">
        <button class="btn" id="restart">Run again</button>
        <button class="btn secondary" id="downloadJson">Download JSON report</button>
      </div>
    </div>
  `;
  document.querySelector("#restart").addEventListener("click", resetSession);
  document.querySelector("#downloadJson").addEventListener("click", () => downloadReport(result));
}

function renderDashboard(result) {
  const labels = {
    confidence: "Confidence",
    curiosity: "Curiosity",
    emotional_safety: "Emotional Safety",
    exploratory_power: "Exploratory Power",
  };
  profileBox.innerHTML = `
    <strong>${result.report.profile}</strong>
    <span>${result.report.headline}</span>
    <em>${result.report.reliability.level} reliability - ${result.report.reliability.score}%</em>
  `;
  scoreList.innerHTML = Object.entries(result.scores)
    .map(([key, value]) => `
      <div class="score-row">
        <header><span>${labels[key]}</span><span>${value}/10</span></header>
        <div class="bar"><span style="width: ${value * 10}%"></span></div>
      </div>
    `)
    .join("");
  evidenceList.innerHTML = result.report.evidence
    .map((item) => `
      <div class="metric">
        <span>${item.label}</span>
        <strong>${item.value}</strong>
        <small>${item.unit}</small>
      </div>
    `)
    .join("");
  reasonList.innerHTML = renderReasonCards(result.report.score_reasons || {}, true);
  insightList.innerHTML = result.insights.map((text) => `<li>${text}</li>`).join("");
  recommendationList.innerHTML = result.report.recommendations.map((text) => `<li>${text}</li>`).join("");
  drawRadar(result.scores);
}

function drawRadar(scores) {
  const ctx = radar.getContext("2d");
  const width = radar.width;
  const height = radar.height;
  const cx = width / 2;
  const cy = height / 2 + 8;
  const radius = 92;
  const keys = ["confidence", "curiosity", "emotional_safety", "exploratory_power"];
  const names = ["Confidence", "Curiosity", "Safety", "Explore"];

  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#c8d0c9";
  ctx.fillStyle = "#4e5b55";
  ctx.font = "13px sans-serif";

  for (let ring = 1; ring <= 4; ring += 1) {
    ctx.beginPath();
    keys.forEach((_, index) => {
      const angle = -Math.PI / 2 + (index * Math.PI * 2) / keys.length;
      const r = (radius * ring) / 4;
      const x = cx + Math.cos(angle) * r;
      const y = cy + Math.sin(angle) * r;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.stroke();
  }

  keys.forEach((key, index) => {
    const angle = -Math.PI / 2 + (index * Math.PI * 2) / keys.length;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
    ctx.stroke();
    ctx.fillText(names[index], cx + Math.cos(angle) * (radius + 22) - 28, cy + Math.sin(angle) * (radius + 22) + 4);
  });

  if (!scores) return;
  ctx.beginPath();
  keys.forEach((key, index) => {
    const angle = -Math.PI / 2 + (index * Math.PI * 2) / keys.length;
    const r = radius * (scores[key] / 10);
    const x = cx + Math.cos(angle) * r;
    const y = cy + Math.sin(angle) * r;
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = "rgba(18, 107, 90, 0.28)";
  ctx.strokeStyle = "#126b5a";
  ctx.lineWidth = 3;
  ctx.fill();
  ctx.stroke();
  ctx.lineWidth = 1;
}

async function resetSession() {
  state.userId = `U${Math.floor(Math.random() * 90000 + 10000)}`;
  state.index = 0;
  state.events = [];
  state.lastResult = null;
  await loadQuestions();
  profileBox.innerHTML = `<strong>Awaiting timed decisions</strong><span>Complete the scenario set to generate an evidence-backed behavioral profile.</span>`;
  scoreList.innerHTML = `<p class="empty">Trait scores appear after scoring.</p>`;
  evidenceList.innerHTML = "";
  reasonList.innerHTML = `<p class="empty">Score reasons appear after the assessment.</p>`;
  insightList.innerHTML = `<li>The model is waiting for timed weighted decisions.</li>`;
  recommendationList.innerHTML = `<li>Complete the assessment to generate next-step guidance.</li>`;
  drawRadar(null);
  renderIntro();
}

function downloadReport(result) {
  const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${result.user_id}-tcbis-report.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function renderReasonCards(reasons, compact = false) {
  const labels = {
    confidence: "Confidence",
    curiosity: "Curiosity",
    emotional_safety: "Emotional Safety",
    exploratory_power: "Exploratory Power",
  };
  return Object.entries(reasons)
    .map(([key, items]) => `
      <div class="reason-card ${compact ? "compact" : ""}">
        <strong>${labels[key] || label(key)}</strong>
        <ul>${items.map((item) => `<li>${item}</li>`).join("")}</ul>
      </div>
    `)
    .join("");
}

function label(key) {
  return String(key).replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

boot();
