const state = {
  userId: `U${Math.floor(Math.random() * 90000 + 10000)}`,
  stage: 0,
  events: [],
  stageStartedAt: performance.now(),
  visitedTiles: new Set(),
  hiddenTiles: new Set(["0-3", "1-1", "2-4", "3-2", "4-0"]),
  energy: 12,
  intel: 0,
  puzzleAttempts: 0,
  lastScan: null,
  scores: null,
};

const stages = [
  renderRouteStage,
  renderMapStage,
  renderSignalStage,
  renderBudgetStage,
  renderPuzzleStage,
];

const stageEl = document.querySelector("#stage");
const stageLabel = document.querySelector("#stageLabel");
const progressFill = document.querySelector("#progressFill");
const scoreList = document.querySelector("#scoreList");
const insightList = document.querySelector("#insightList");
const evidenceList = document.querySelector("#evidenceList");
const recommendationList = document.querySelector("#recommendationList");
const profileBox = document.querySelector("#profileBox");
const serverStatus = document.querySelector("#serverStatus");
const radar = document.querySelector("#radar");

function decisionTime() {
  return Number(((performance.now() - state.stageStartedAt) / 1000).toFixed(3));
}

function logEvent(type, details = {}) {
  state.events.push({
    type,
    timestamp: Date.now(),
    stage: state.stage + 1,
    energy: state.energy,
    intel: state.intel,
    ...details,
  });
}

function setStage(index) {
  state.stage = index;
  state.stageStartedAt = performance.now();
  stageLabel.textContent = `Stage ${Math.min(index + 1, stages.length)} / ${stages.length}`;
  progressFill.style.width = `${Math.max(20, ((index + 1) / stages.length) * 100)}%`;
  stages[index]();
}

function sceneShell(title, body, controls, extra = "") {
  stageEl.innerHTML = `
    <div class="resource-rail">
      <span>Energy <strong>${state.energy}</strong></span>
      <span>Intel <strong>${state.intel}</strong></span>
      <span>Events <strong>${state.events.length}</strong></span>
    </div>
    <div class="scene">
      <div class="scene-art" aria-hidden="true">
        <div class="scan-line"></div>
        <div class="moon"></div>
        <div class="ridge"></div>
        <div class="path"></div>
      </div>
      <div class="copy">
        <h2>${title}</h2>
        <p>${body}</p>
        ${extra}
        <div class="actions">${controls}</div>
      </div>
    </div>
  `;
}

function renderRouteStage() {
  const cards = [
    {
      id: "safe",
      title: "Stabilize first",
      text: "Spend 2 energy for a protected route and one clue.",
      risk: 0.15,
      energy: 2,
      intel: 1,
      pattern: "safe",
    },
    {
      id: "balanced",
      title: "Probe the edge",
      text: "Spend 3 energy, gain two clues, and accept moderate uncertainty.",
      risk: 0.45,
      energy: 3,
      intel: 2,
      pattern: "balanced",
    },
    {
      id: "risk",
      title: "Cross the unstable bridge",
      text: "Spend 1 energy and move fast, but the signal may be noisy.",
      risk: 0.82,
      energy: 1,
      intel: 0,
      pattern: "risk",
    },
  ];

  sceneShell(
    "The expedition begins with a real tradeoff.",
    "Your first move affects the evidence available later. The model reads the tradeoff pattern, not a self-rating.",
    "",
    `<div class="choice-grid">${cards
      .map(
        (card) => `
          <button class="choice-card" data-route="${card.id}">
            <strong>${card.title}</strong>
            <span>${card.text}</span>
          </button>`
      )
      .join("")}</div>`
  );

  stageEl.querySelectorAll("[data-route]").forEach((button) => {
    button.addEventListener("click", () => {
      const card = cards.find((item) => item.id === button.dataset.route);
      state.energy = Math.max(0, state.energy - card.energy);
      state.intel += card.intel;
      logEvent("risk_choice", {
        choice: card.id === "risk" ? "risk" : "safe",
        risk_level: card.risk,
        pattern: card.pattern,
        decision_time: decisionTime(),
      });
      logEvent("resource_allocation", {
        energy_spent: card.energy,
        clue_value: card.intel,
        risk_level: card.risk,
        decision_time: decisionTime(),
      });
      setStage(1);
    });
  });
}

function renderMapStage() {
  const tiles = Array.from({ length: 25 }, (_, index) => {
    const row = Math.floor(index / 5);
    const col = index % 5;
    const id = `${row}-${col}`;
    const classes = ["tile"];
    if (state.visitedTiles.has(id)) classes.push("visited");
    if (state.hiddenTiles.has(id) && state.visitedTiles.has(id)) classes.push("hidden");
    const label = state.visitedTiles.has(id) ? (state.hiddenTiles.has(id) ? "SIG" : "OK") : "?";
    return `<button class="${classes.join(" ")}" data-tile="${id}">${label}</button>`;
  }).join("");

  const hint = state.lastScan ? `<p class="signal-note">${state.lastScan}</p>` : "";
  sceneShell(
    "Map the hidden zone before the path collapses.",
    "Every tile costs one energy. Hidden signals increase information gain; stopping early preserves energy.",
    `
      <button class="btn" id="continueExplore">Lock route</button>
      <button class="btn secondary" id="scanMap">Spend 1 energy scan</button>
    `,
    `${hint}<div class="grid-zone">${tiles}</div>`
  );

  stageEl.querySelectorAll("[data-tile]").forEach((button) => {
    button.addEventListener("click", () => {
      const tile = button.dataset.tile;
      if (state.energy <= 0) {
        state.lastScan = "Energy is depleted; lock the route to continue.";
        renderMapStage();
        return;
      }
      if (!state.visitedTiles.has(tile)) {
        state.energy -= 1;
        const hidden = state.hiddenTiles.has(tile);
        if (hidden) state.intel += 2;
        state.visitedTiles.add(tile);
        logEvent("explore_tile", {
          tile,
          hidden,
          pattern: hidden ? "discover" : "explore",
          decision_time: decisionTime(),
        });
      }
      renderMapStage();
    });
  });

  document.querySelector("#scanMap").addEventListener("click", () => {
    if (state.energy <= 0) {
      state.lastScan = "No energy remains for a scan.";
      renderMapStage();
      return;
    }
    state.energy -= 1;
    const target = [...state.hiddenTiles].find((tile) => !state.visitedTiles.has(tile));
    state.lastScan = target ? `Scan pulse narrows toward sector ${target}.` : "No hidden signals remain nearby.";
    logEvent("hint_request", {
      context: "map_scan",
      decision_time: decisionTime(),
    });
    logEvent("resource_allocation", {
      energy_spent: 1,
      clue_value: target ? 1 : 0,
      risk_level: 0.2,
      decision_time: decisionTime(),
    });
    renderMapStage();
  });

  document.querySelector("#continueExplore").addEventListener("click", () => {
    logEvent("path_choice", {
      choice: "lock_route",
      pattern: "commit",
      explored_count: state.visitedTiles.size,
      decision_time: decisionTime(),
    });
    setStage(2);
  });
}

function renderSignalStage() {
  sceneShell(
    "The AI signal disagrees with the terrain.",
    "A bright gate promises speed. A quiet gate matches the map. You can request a second signal or commit from the evidence you already have.",
    `
      <button class="btn secondary" id="askHint">Request second signal</button>
      <button class="btn" data-path="quiet">Take quiet gate</button>
      <button class="btn warning" data-path="bright">Take bright gate</button>
    `,
    `<div class="signal-board"><span>Map Intel: ${state.intel}</span><span>Signal Noise: ${state.intel >= 4 ? "Low" : "High"}</span></div>`
  );

  document.querySelector("#askHint").addEventListener("click", () => {
    state.intel += 1;
    logEvent("hint_request", {
      context: "gate_signal",
      decision_time: decisionTime(),
    });
    logEvent("signal_choice", {
      choice: "ask_more",
      pattern: "investigate",
      decision_time: decisionTime(),
    });
    document.querySelector(".copy p").textContent =
      "The second signal says the bright gate is faster but less stable. The quiet gate is slower with fewer unknowns.";
    document.querySelector(".signal-board").innerHTML = `<span>Map Intel: ${state.intel}</span><span>Signal Noise: Medium</span>`;
  });

  stageEl.querySelectorAll("[data-path]").forEach((button) => {
    button.addEventListener("click", () => {
      const bright = button.dataset.path === "bright";
      logEvent("risk_choice", {
        choice: bright ? "risk" : "safe",
        risk_level: bright ? 0.75 : 0.28,
        pattern: bright ? "risk" : "safe",
        decision_time: decisionTime(),
      });
      setStage(3);
    });
  });
}

function renderBudgetStage() {
  const plans = [
    { id: "stabilize", title: "Stabilize", text: "Spend 4 energy for high reliability.", energy: 4, clue: 4, risk: 0.2, pattern: "safe" },
    { id: "scout", title: "Scout", text: "Spend 3 energy for balanced signal coverage.", energy: 3, clue: 5, risk: 0.45, pattern: "balanced" },
    { id: "rush", title: "Rush", text: "Spend 1 energy and preserve speed.", energy: 1, clue: 1, risk: 0.78, pattern: "risk" },
  ];

  sceneShell(
    "Allocate your remaining expedition budget.",
    "This choice tests whether you conserve, investigate, or rush when the final outcome is close.",
    "",
    `<div class="choice-grid">${plans
      .map(
        (plan) => `
          <button class="choice-card" data-plan="${plan.id}">
            <strong>${plan.title}</strong>
            <span>${plan.text}</span>
          </button>`
      )
      .join("")}</div>`
  );

  stageEl.querySelectorAll("[data-plan]").forEach((button) => {
    button.addEventListener("click", () => {
      const plan = plans.find((item) => item.id === button.dataset.plan);
      const spent = Math.min(state.energy, plan.energy);
      state.energy -= spent;
      state.intel += plan.clue;
      logEvent("resource_allocation", {
        energy_spent: spent,
        clue_value: plan.clue,
        risk_level: plan.risk,
        decision_time: decisionTime(),
      });
      logEvent("signal_choice", {
        choice: plan.id,
        pattern: plan.pattern,
        decision_time: decisionTime(),
      });
      setStage(4);
    });
  });
}

function renderPuzzleStage() {
  sceneShell(
    "Final gate: commit under uncertainty.",
    "Decode the sequence and place a confidence wager. Wagering high after weak evidence is different from wagering high after strong evidence.",
    `
      <button class="btn" id="submitPuzzle">Submit answer</button>
      <button class="btn secondary" id="puzzleHint">Request final hint</button>
    `,
    `
      <div class="puzzle-box">
        <label>Sequence: 3, 5, 9, 17, ?</label>
        <input id="puzzleAnswer" inputmode="numeric" autocomplete="off" placeholder="Enter answer" />
        <label for="wager">Confidence wager: <strong id="wagerValue">5</strong>/10</label>
        <input id="wager" type="range" min="0" max="10" value="5" />
        <div class="feedback" id="feedback"></div>
      </div>
    `
  );

  const wager = document.querySelector("#wager");
  wager.addEventListener("input", () => {
    document.querySelector("#wagerValue").textContent = wager.value;
  });

  document.querySelector("#puzzleHint").addEventListener("click", () => {
    state.intel += 1;
    logEvent("hint_request", {
      context: "final_gate",
      decision_time: decisionTime(),
    });
    document.querySelector("#feedback").textContent = "Hint: the added amount doubles each step.";
  });

  document.querySelector("#submitPuzzle").addEventListener("click", async () => {
    const answer = document.querySelector("#puzzleAnswer").value.trim();
    const wagerValue = Number(document.querySelector("#wager").value);
    const correct = answer === "33";
    state.puzzleAttempts += 1;

    logEvent("confidence_wager", {
      wager: wagerValue,
      decision_time: decisionTime(),
    });
    logEvent("puzzle_attempt", {
      answer,
      correct,
      attempt: state.puzzleAttempts,
      decision_time: decisionTime(),
    });

    if (!correct && state.puzzleAttempts < 3) {
      logEvent("retry", { attempt: state.puzzleAttempts });
      document.querySelector("#feedback").textContent = "The gate rejects that answer. Recalibrate and try again.";
      state.stageStartedAt = performance.now();
      return;
    }

    await submitScore();
  });
}

async function submitScore() {
  stageEl.innerHTML = `<div class="copy"><h2>Generating behavioral report...</h2><p>XGBoost is scoring the engineered session features.</p></div>`;

  const response = await fetch("/api/score", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: state.userId,
      events: state.events,
    }),
  });

  const result = await response.json();
  if (!response.ok) {
    stageEl.innerHTML = `<div class="copy"><h2>Scoring failed</h2><p>${result.error || "Unknown error"}</p></div>`;
    return;
  }

  state.scores = result.scores;
  renderDashboard(result);
  renderComplete(result);
}

function renderComplete(result) {
  const explanations = Object.entries(result.report.trait_explanations)
    .map(([key, value]) => `<li><strong>${label(key)}</strong>: ${value}</li>`)
    .join("");

  stageEl.innerHTML = `
    <div class="report-stage">
      <div>
        <p class="eyebrow">Assessment Complete</p>
        <h2>${result.report.profile}</h2>
        <p>${result.report.headline}</p>
      </div>
      <div class="report-grid">
        <div class="report-panel">
          <strong>Reliability</strong>
          <span>${result.report.reliability.level} (${result.report.reliability.score}%)</span>
        </div>
        <div class="report-panel">
          <strong>Model Mode</strong>
          <span>${result.model_mode}</span>
        </div>
        <div class="report-panel">
          <strong>Model vs Rule Gap</strong>
          <span>${result.report.confidence_gap}</span>
        </div>
      </div>
      <ul class="explanation-list">${explanations}</ul>
      <div class="actions">
        <button class="btn" id="restart">Start new run</button>
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
    .map(
      ([key, value]) => `
        <div class="score-row">
          <header><span>${labels[key]}</span><span>${value}/10</span></header>
          <div class="bar"><span style="width: ${value * 10}%"></span></div>
        </div>
      `
    )
    .join("");

  evidenceList.innerHTML = result.report.evidence
    .map(
      (item) => `
        <div class="metric">
          <span>${item.label}</span>
          <strong>${item.value}</strong>
          <small>${item.unit}</small>
        </div>`
    )
    .join("");

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

function resetSession() {
  state.userId = `U${Math.floor(Math.random() * 90000 + 10000)}`;
  state.stage = 0;
  state.events = [];
  state.stageStartedAt = performance.now();
  state.visitedTiles = new Set();
  state.energy = 12;
  state.intel = 0;
  state.puzzleAttempts = 0;
  state.lastScan = null;
  state.scores = null;
  profileBox.innerHTML = `<strong>Awaiting session</strong><span>Play through the expedition to generate an evidence-backed report.</span>`;
  scoreList.innerHTML = `<p class="empty">Scores appear after the final gate.</p>`;
  evidenceList.innerHTML = "";
  insightList.innerHTML = `<li>The model is waiting for behavioral data.</li>`;
  recommendationList.innerHTML = `<li>Complete a run to generate next-step guidance.</li>`;
  drawRadar(null);
  setStage(0);
}

function downloadReport(result) {
  const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${result.user_id}-behavioral-report.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function label(key) {
  return key.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

async function checkServer() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    serverStatus.textContent = data.model_mode === "xgboost" ? "XGBoost active" : "Fallback model active";
  } catch {
    serverStatus.textContent = "Server offline";
  }
}

checkServer();
drawRadar(null);
setStage(0);
