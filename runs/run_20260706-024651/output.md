Jag bygger ett komplett mörkt dashboard i en HTML-fil som pollar API:et var 5:e sekund. Layouten har en header med statistik, en trekolumnsgrid för aktiva runs, score-historik per blueprint och agentstatus. All data hämtas från din lokala API-server (localhost:8000) och presenteras med tydliga färgkoder och enkel typografi – inga externa beroenden.

```html
<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Forge Command Center</title>
  <style>
    /* === Reset & Base === */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      background: #0d1117;
      color: #c9d1d9;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
      line-height: 1.5;
      padding: 0 1.5rem;
    }

    /* === Header === */
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.2rem 0;
      border-bottom: 1px solid #21262d;
      margin-bottom: 1rem;
    }
    .header h1 {
      font-size: 1.5rem;
      font-weight: 600;
      letter-spacing: -0.02em;
    }
    .header .last-updated {
      font-size: 0.8rem;
      color: #8b949e;
    }
    .header .last-updated .dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #3fb950;
      margin-right: 6px;
      vertical-align: middle;
      animation: pulse-dot 1.5s ease-in-out infinite;
    }
    @keyframes pulse-dot {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }

    /* === Stats Row === */
    .stats-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    .stat-card {
      background: #161b22;
      border: 1px solid #21262d;
      border-radius: 8px;
      padding: 1rem 1.2rem;
    }
    .stat-card .label {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #8b949e;
      margin-bottom: 0.3rem;
    }
    .stat-card .value {
      font-size: 1.8rem;
      font-weight: 700;
    }
    .stat-card .value.green { color: #3fb950; }
    .stat-card .value.blue  { color: #58a6ff; }
    .stat-card .value.amber { color: #d29922; }

    /* === Dashboard Grid === */
    .dashboard {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 1rem;
      padding-bottom: 2rem;
    }
    @media (max-width: 1024px) {
      .dashboard { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 640px) {
      .dashboard { grid-template-columns: 1fr; }
      .stats-row { grid-template-columns: 1fr; }
    }

    /* === Panels === */
    .panel {
      background: #161b22;
      border: 1px solid #21262d;
      border-radius: 8px;
      padding: 1rem 1.2rem;
    }
    .panel h2 {
      font-size: 0.9rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #8b949e;
      margin-bottom: 0.8rem;
      padding-bottom: 0.4rem;
      border-bottom: 1px solid #21262d;
    }

    /* === Run list === */
    .run-list { list-style: none; }
    .run-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.4rem 0;
      border-bottom: 1px solid #1e242c;
      font-size: 0.9rem;
    }
    .run-item:last-child { border-bottom: none; }
    .run-item .run-id {
      font-family: 'SFMono-Regular', Consolas, monospace;
      font-size: 0.85rem;
      color: #58a6ff;
    }
    .run-item .run-blueprint {
      color: #c9d1d9;
      margin: 0 0.5rem;
    }
    .badge {
      display: inline-block;
      padding: 0.15rem 0.5rem;
      border-radius: 12px;
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
    }
    .badge-running    { background: #2ea043; color: #fff; }
    .badge-eval       { background: #1f6feb; color: #fff; }
    .badge-improving  { background: #bb8009; color: #fff; }
    .badge-error      { background: #da3633; color: #fff; }
    .badge-unknown    { background: #484f58; color: #fff; }

    /* === Blueprint score bars === */
    .bp-list { list-style: none; }
    .bp-item {
      margin-bottom: 0.6rem;
    }
    .bp-item:last-child { margin-bottom: 0; }
    .bp-name {
      font-size: 0.85rem;
      margin-bottom: 0.2rem;
      display: flex;
      justify-content: space-between;
    }
    .bp-score {
      font-weight: 600;
    }
    .bp-bar-bg {
      width: 100%;
      height: 8px;
      background: #30363d;
      border-radius: 4px;
      overflow: hidden;
    }
    .bp-bar-fill {
      height: 100%;
      border-radius: 4px;
      transition: width 0.3s ease;
    }
    .bp-bar-green  { background: linear-gradient(90deg, #2ea043, #3fb950); }
    .bp-bar-yellow { background: linear-gradient(90deg, #bb8009, #d29922); }
    .bp-bar-red    { background: linear-gradient(90deg, #da3633, #f85149); }

    /* === Agent status === */
    .agent-status {
      font-size: 0.9rem;
    }
    .agent-list {
      list-style: none;
    }
    .agent-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.4rem 0;
      border-bottom: 1px solid #1e242c;
    }
    .agent-item:last-child { border-bottom: none; }
    .agent-name {
      font-family: 'SFMono-Regular', Consolas, monospace;
      font-size: 0.85rem;
    }

    /* === Loader === */
    .empty-state {
      color: #484f58;
      font-style: italic;
      font-size: 0.85rem;
    }
  </style>
</head>
<body>

  <!-- Header -->
  <header class="header">
    <h1>Forge Command Center</h1>
    <span class="last-updated">
      <span class="dot"></span>
      <span id="updateTime">–</span>
    </span>
  </header>

  <!-- Stats Row -->
  <div class="stats-row" id="statsRow">
    <div class="stat-card">
      <div class="label">Totala Runs</div>
      <div class="value green" id="totalRuns">–</div>
    </div>
    <div class="stat-card">
      <div class="label">Aktiva Runs</div>
      <div class="value blue" id="activeRuns">–</div>
    </div>
    <div class="stat-card">
      <div class="label">Medelpoäng</div>
      <div class="value amber" id="avgScore">–</div>
    </div>
  </div>

  <!-- Dashboard Grid -->
  <div class="dashboard">

    <!-- Active Runs -->
    <section class="panel">
      <h2>Aktiva runs</h2>
      <ul class="run-list" id="runList">
        <li class="empty-state">Laddar…</li>
      </ul>
    </section>

    <!-- Blueprint Scores -->
    <section class="panel">
      <h2>Blueprint-poäng</h2>
      <ul class="bp-list" id="bpList">
        <li class="empty-state">Laddar…</li>
      </ul>
    </section>

    <!-- Agent Status -->
    <section class="panel">
      <h2>Agentstatus</h2>
      <div class="agent-status" id="agentStatus">
        <span class="empty-state">Laddar…</span>
      </div>
    </section>

  </div>

  <script>
    (function() {
      'use strict';

      const API_BASE = 'http://localhost:8000';
      // Poll-intervall: 5 sekunder
      const POLL_INTERVAL = 5000;

      // DOM-referenser
      const updateTimeEl   = document.getElementById('updateTime');
      const totalRunsEl    = document.getElementById('totalRuns');
      const activeRunsEl   = document.getElementById('activeRuns');
      const avgScoreEl     = document.getElementById('avgScore');
      const runListEl      = document.getElementById('runList');
      const bpListEl       = document.getElementById('bpList');
      const agentStatusEl  = document.getElementById('agentStatus');

      // Hjälpfunktion: skapa element
      function createEl(tag, className, text) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (text !== undefined) el.textContent = text;
        return el;
      }

      // Formatera tidsstämpel
      function nowString() {
        const d = new Date();
        return d.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      }

      // Färgkod för run-status
      function badgeClassForStatus(status) {
        const s = (status || '').toLowerCase();
        if (s === 'running')  return 'badge-running';
        if (s === 'eval')     return 'badge-eval';
        if (s === 'improving') return 'badge-improving';
        if (s === 'error')    return 'badge-error';
        return 'badge-unknown';
      }

      // Färg för score-bar (score 0-1)
      function barClassForScore(score) {
        if (score >= 0.7) return 'bp-bar-green';
        if (score >= 0.4) return 'bp-bar-yellow';
        return 'bp-bar-red';
      }

      // --- Uppdatera sektioner ---

      function updateStats(stats) {
        // stats förväntas innehålla: total_runs, active_runs, average_score
        const total   = stats.total_runs   ?? '–';
        const active  = stats.active_runs  ?? '–';
        const avg     = stats.average_score ?? '–';
        totalRunsEl.textContent  = total;
        activeRunsEl.textContent = active;
        // Visa poäng som procent eller decimal
        avgScoreEl.textContent   = (typeof avg === 'number') 
          ? avg.toFixed(2) + (avg <= 1 ? '' : '') 
          : avg;
      }

      function updateRuns(runs) {
        // runs förväntas vara en array av objekt: { id, name?, blueprint, status, start_time? }
        if (!Array.isArray(runs) || runs.length === 0) {
          runListEl.innerHTML = '<li class="empty-state">Inga aktiva runs</li>';
          return;
        }
        const fragment = document.createDocumentFragment();
        runs.forEach(run => {
          const li = createEl('li', 'run-item');
          const idSpan = createEl('span', 'run-id', run.id || run.name || '?');
          const bpSpan = createEl('span', 'run-blueprint', run.blueprint || '–');
          const badge  = createEl('span', `badge ${badgeClassForStatus(run.status)}`, run.status || 'unknown');
          li.appendChild(idSpan);
          li.appendChild(bpSpan);
          li.appendChild(badge);
          fragment.appendChild(li);
        });
        runListEl.innerHTML = '';
        runListEl.appendChild(fragment);
      }

      function updateBlueprints(blueprints) {
        // blueprints förväntas vara en array av objekt: { name, scores?, average_score? }
        if (!Array.isArray(blueprints) || blueprints.length === 0) {
          bpListEl.innerHTML = '<li class="empty-state">Inga blueprints</li>';
          return;
        }
        const fragment = document.createDocumentFragment();
        blueprints.forEach(bp => {
          const score = (bp.average_score !== undefined) 
            ? bp.average_score 
            : (Array.isArray(bp.scores) && bp.scores.length > 0 
                ? bp.scores.reduce((a,b)=>a+b,0) / bp.scores.length 
                : 0);
          const scorePct = Math.min(Math.max(score, 0), 1); // clamp 0-1

          const li = createEl('li', 'bp-item');

          // Namn och poäng
          const nameRow = createEl('div', 'bp-name');
          const nameSpan = createEl('span', '', bp.name || 'Unknown');
          const scoreSpan = createEl('span', 'bp-score', (scorePct * 100).toFixed(1) + '%');
          nameRow.appendChild(nameSpan);
          nameRow.appendChild(scoreSpan);

          // Bar-bakgrund
          const barBg = createEl('div', 'bp-bar-bg');
          const barFill = createEl('div', `bp-bar-fill ${barClassForScore(scorePct)}`);
          barFill.style.width = (scorePct * 100) + '%';
          barBg.appendChild(barFill);

          li.appendChild(nameRow);
          li.appendChild(barBg);
          fragment.appendChild(li);
        });
        bpListEl.innerHTML = '';
        bpListEl.appendChild(fragment);
      }

      function updateAgentStatus(status) {
        // status kan vara en sträng (t.ex. "running") eller ett objekt/array.
        if (typeof status === 'string') {
          // Enkel agent
          const badge = createEl('span', `badge ${badgeClassForStatus(status)}`, status);
          agentStatusEl.innerHTML = '';
          agentStatusEl.appendChild(badge);
        } else if (Array.isArray(status)) {
          // Flera agenter – förväntas array av { name, status }
          if (status.length === 0) {
            agentStatusEl.innerHTML = '<span class="empty-state">Inga agenter</span>';
            return;
          }
          const list = createEl('ul', 'agent-list');
          status.forEach(agent => {
            const li = createEl('li', 'agent-item');
            const nameSpan = createEl('span', 'agent-name', agent.name || 'agent');
            const badge = createEl('span', `badge ${badgeClassForStatus(agent.status)}`, agent.status || 'unknown');
            li.appendChild(nameSpan);
            li.appendChild(badge);
            list.appendChild(li);
          });
          agentStatusEl.innerHTML = '';
          agentStatusEl.appendChild(list);
        } else if (status && typeof status === 'object') {
          // Enskild agent som objekt (t.ex. { agent: "running" })
          const agentName = Object.keys(status)[0] || 'agent';
          const agentVal  = status[agentName] || 'unknown';
          const badge = createEl('span', `badge ${badgeClassForStatus(agentVal)}`, agentVal);
          const container = createEl('div', 'agent-item');
          container.appendChild(createEl('span', 'agent-name', agentName));
          container.appendChild(badge);
          agentStatusEl.innerHTML = '';
          agentStatusEl.appendChild(container);
        } else {
          agentStatusEl.innerHTML = '<span class="empty-state">Ingen status</span>';
        }
      }

      // --- Huvudfunktion: hämta och uppdatera ---
      async function poll() {
        try {
          const endpoints = [
            fetch(`${API_BASE}/api/runs`),
            fetch(`${API_BASE}/api/blueprints`),
            fetch(`${API_BASE}/api/stats`),
            fetch(`${API_BASE}/api/status`)
          ];
          const results = await Promise.allSettled(endpoints);

          const data = { runs: null, blueprints: null, stats: null, status: null };

          // Parsa JSON där det gick bra
          for (let i = 0; i < results.length; i++) {
            const res = results[i];
            if (res.status === 'fulfilled') {
              try {
                const json = await res.value.json();
                if (i === 0) data.runs = json;
                else if (i === 1) data.blueprints = json;
                else if (i === 2) data.stats = json;
                else if (i === 3) data.status = json;
              } catch (e) {
                console.warn(`Endpoint ${i} returnerade ogiltig JSON`);
              }
            } else {
              console.warn(`Endpoint ${i} misslyckades:`, res.reason);
            }
          }

          // Uppdatera UI (med null-säkerhet)
          if (data.stats)       updateStats(data.stats);
          if (data.runs)        updateRuns(data.runs);
          if (data.blueprints)  updateBlueprints(data.blueprints);
          if (data.status !== null) updateAgentStatus(data.status);

          // Tidstämpel
          updateTimeEl.textContent = nowString();

        } catch (err) {
          console.error('Poll-fel:', err);
        }
      }

      // Starta polling
      poll();
      setInterval(poll, POLL_INTERVAL);
    })();
  </script>

</body>
</html>
```

### Översikt över dashboardet

**1. Header och statistikrad**  
- Visar titel och en pulserande indikator med senaste uppdateringstid.  
- Tre statistik-kort för totala runs, aktiva runs och medelpoäng – hämtas från `/api/stats`.

**2. Aktiva runs (vänster panel)**  
- Listar varje run med dess ID, blueprint och en färgad badge (running/eval/improving/error).  
- Data från `/api/runs`.

**3. Blueprint-poäng (mittenpanel)**  
- Varje blueprint visas med namn och genomsnittspoäng som en procentuell stapel (0–100%).  
- Stapelfärgen ändras (grön/gul/röd) baserat på poängen.  
- Data från `/api/blueprints` – använder `average_score` eller räknar medelvärdet av `scores`.

**4. Agentstatus (höger panel)**  
- Hanterar flera format: en sträng, en array av agenter eller ett objekt med agentnyckel.  
- Visar varje agent med namn och statusbadge (samma färgkodning som runs).  
- Data från `/api/status`.

**Tekniskt**  
- All data hämtas parallellt med `Promise.allSettled` för att tolerera enskilda endpoint-fel.  
- Uppdateras automatiskt var 5:e sekund.  
- Responsiv layout med CSS Grid som anpassar sig till tre, två eller en kolumn.  
- Inga externa beroenden – all kod är inline.  

Du kan anpassa API-adressen i `API_BASE` om servern körs på annan port eller host.