const state = {
  userId: `U${Math.floor(Math.random() * 90000 + 10000)}`,
  stage: 0,
  events: [],
  stageStartedAt: performance.now(),
  visitedTiles: new Set(),
  hiddenTiles: new Set(["1-2", "2-1", "3-3"]),
  puzzleAttempts: 0,
  scores: null,
};

const stages = [renderRiskStage, renderExploreStage, renderHintStage, renderPuzzleStage];

const stageEl = document.querySelector("#stage");
const stageLabel = document.querySelector("#stageLabel");
const progressFill = document.querySelector("#progressFill");
const scoreList = document.querySelector("#scoreList");
const insightList = document.querySelector("#insightList");
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
    ...details,
  });
}

function setStage(index) {
  state.stage = index;
  state.stageStartedAt = performance.now();
  stageLabel.textContent = `Stage ${Math.min(index + 1, 4)} / 4`;
  progressFill.style.width = `${Math.max(25, ((index + 1) / 4) * 100)}%`;
  stages[index]();
}

function sceneShell(title, body, controls, extra = "") {
  stageEl.innerHTML = `
    <div class="scene">
      <div class="scene-art" aria-hidden="true">
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

function renderRiskStage() {
  sceneShell(
    "A glowing bridge cuts across the valley.",
    "One route is stable and slow. The other is unknown, shorter, and visibly unstable. Choose how your expedition begins.",
    `
      <button class="btn warning" data-choice="risk">Take unknown bridge</button>
      <button class="btn secondary" data-choice="safe">Follow safe ridge</button>
    `
  );

  stageEl.querySelectorAll("[data-choice]").forEach((button) => {
    button.addEventListener("click", () => {
      logEvent("risk_choice", {
        choice: button.dataset.choice,
        decision_time: decisionTime(),
      });
      setStage(1);
    });
  });
}

function renderExploreStage() {
  const tiles = Array.from({ length: 16 }, (_, index) => {
    const row = Math.floor(index / 4);
    const col = index % 4;
    const id = `${row}-${col}`;
    const classes = ["tile"];
    if (state.visitedTiles.has(id)) classes.push("visited");
    if (state.hiddenTiles.has(id) && state.visitedTiles.has(id)) classes.push("hidden");
    return `<button class="${classes.join(" ")}" data-tile="${id}">${state.visitedTiles.has(id) ? "✓" : "?"}</button>`;
  }).join("");

  sceneShell(
    "The hidden zone opens.",
    "Explore the grid before moving forward. Some tiles contain hidden signals that improve the expedition map.",
    `
      <button class="btn" id="continueExplore">Continue</button>
      <button class="btn secondary" id="hintExplore">Ask for scan hint</button>
    `,
    `<div class="grid-zone">${tiles}</div>`
  );

  stageEl.querySelectorAll("[data-tile]").forEach((button) => {
    button.addEventListener("click", () => {
      const tile = button.dataset.tile;
      if (!state.visitedTiles.has(tile)) {
        state.visitedTiles.add(tile);
        logEvent("explore_tile", {
          tile,
          hidden: state.hiddenTiles.has(tile),
          decision_time: decisionTime(),
        });
      }
      renderExploreStage();
    });
  });

  document.querySelector("#continueExplore").addEventListener("click", () => {
    logEvent("path_choice", {
      choice: "continue",
      decision_time: decisionTime(),
      explored_count: state.visitedTiles.size,
    });
    setStage(2);
  });

  document.querySelector("#hintExplore").addEventListener("click", () => {
    logEvent("hint_request", {
      context: "exploration",
      decision_time: decisionTime(),
    });
    const unvisitedHidden = [...state.hiddenTiles].find((tile) => !state.visitedTiles.has(tile));
    if (unvisitedHidden) {
      const tile = document.querySelector(`[data-tile="${unvisitedHidden}"]`);
      tile.textContent = "!";
    }
  });
}

function renderHintStage() {
  sceneShell(
    "An AI signal offers a clue.",
    "A sealed gate asks you to infer the correct direction. You can ask the AI for more context or make the call now.",
    `
      <button class="btn secondary" id="askHint">Request AI hint</button>
      <button class="btn" data-path="left">Choose left gate</button>
      <button class="btn warning" data-path="right">Choose right gate</button>
    `
  );

  document.querySelector("#askHint").addEventListener("click", () => {
    logEvent("hint_request", {
      context: "gate",
      decision_time: decisionTime(),
    });
    document.querySelector(".copy p").textContent =
      "The AI signal says: the louder gate is not always the safer one. You can still choose either path.";
  });

  stageEl.querySelectorAll("[data-path]").forEach((button) => {
    button.addEventListener("click", () => {
      logEvent("risk_choice", {
        choice: button.dataset.path === "right" ? "risk" : "safe",
        decision_time: decisionTime(),
      });
      setStage(3);
    });
  });
}

function renderPuzzleStage() {
  sceneShell(
    "Final uncertainty puzzle.",
    "Decode the gate number. Pattern: 2, 4, 8, 16, ?",
    `
      <button class="btn" id="submitPuzzle">Submit</button>
      <button class="btn secondary" id="puzzleHint">Ask for hint</button>
    `,
    `
      <div class="puzzle-box">
        <input id="puzzleAnswer" inputmode="numeric" autocomplete="off" placeholder="Enter answer" />
        <div class="feedback" id="feedback"></div>
      </div>
    `
  );

  document.querySelector("#puzzleHint").addEventListener("click", () => {
    logEvent("hint_request", {
      context: "puzzle",
      decision_time: decisionTime(),
    });
    document.querySelector("#feedback").textContent = "Hint: each number doubles.";
  });

  document.querySelector("#submitPuzzle").addEventListener("click", async () => {
    const answer = document.querySelector("#puzzleAnswer").value.trim();
    const correct = answer === "32";
    state.puzzleAttempts += 1;

    logEvent("puzzle_attempt", {
      answer,
      correct,
      attempt: state.puzzleAttempts,
      decision_time: decisionTime(),
    });

    if (!correct && state.puzzleAttempts < 3) {
      logEvent("retry", { attempt: state.puzzleAttempts });
      document.querySelector("#feedback").textContent = "Not quite. Try again.";
      state.stageStartedAt = performance.now();
      return;
    }

    await submitScore();
  });
}

async function submitScore() {
  stageEl.innerHTML = `<div class="copy"><h2>Scoring expedition...</h2><p>Your behavioral features are being calculated.</p></div>`;

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
  const featurePairs = Object.entries(result.features)
    .map(([key, value]) => `<li><strong>${label(key)}</strong>: ${value}</li>`)
    .join("");

  stageEl.innerHTML = `
    <div class="scene">
      <div class="scene-art" aria-hidden="true">
        <div class="moon"></div>
        <div class="ridge"></div>
        <div class="path"></div>
      </div>
      <div class="copy">
        <h2>Assessment complete.</h2>
        <p>Model mode: ${result.model_mode}. The score combines behavioral prediction with transparent rule-based logic.</p>
        <ul>${featurePairs}</ul>
        <div class="actions">
          <button class="btn" id="restart">Start new session</button>
        </div>
      </div>
    </div>
  `;

  document.querySelector("#restart").addEventListener("click", () => {
    state.events = [];
    state.visitedTiles = new Set();
    state.puzzleAttempts = 0;
    state.userId = `U${Math.floor(Math.random() * 90000 + 10000)}`;
    setStage(0);
    drawRadar(null);
  });
}

function renderDashboard(result) {
  const labels = {
    confidence: "Confidence",
    curiosity: "Curiosity",
    emotional_safety: "Emotional Safety",
    exploratory_power: "Exploratory Power",
  };

  scoreList.innerHTML = Object.entries(result.scores)
    .map(([key, value]) => `
      <div class="score-row">
        <header><span>${labels[key]}</span><span>${value}/10</span></header>
        <div class="bar"><span style="width: ${value * 10}%"></span></div>
      </div>
    `)
    .join("");

  insightList.innerHTML = result.insights.map((text) => `<li>${text}</li>`).join("");
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
  ctx.strokeStyle = "#d9d5ca";
  ctx.fillStyle = "#66706b";
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
  ctx.fillStyle = "rgba(19, 111, 99, 0.28)";
  ctx.strokeStyle = "#136f63";
  ctx.lineWidth = 3;
  ctx.fill();
  ctx.stroke();
  ctx.lineWidth = 1;
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

