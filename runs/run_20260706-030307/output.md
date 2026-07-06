```html
<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Forge Command Center</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      background: #0d1117;
      color: #e6edf3;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      padding: 2rem;
      min-height: 100vh;
    }

    .container {
      max-width: 1400px;
      margin: 0 auto;
    }

    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #21262d;
    }

    header h1 {
      font-size: 1.8rem;
      font-weight: 600;
      letter-spacing: -0.02em;
      color: #f0f6fc;
    }

    .last-update {
      font-size: 0.85rem;
      color: #8b949e;
      font-variant-numeric: tabular-nums;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }

    .card {
      background: #161b22;
      border: 1px solid #21262d;
      border-radius: 12px;
      padding: 1.25rem;
      transition: border-color 0.2s;
    }

    .card:hover {
      border-color: #30363d;
    }

    .card h2 {
      font-size: 0.9rem;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #8b949e;
      margin-bottom: 0.75rem;
    }

    .stat-value {
      font-size: 2rem;
      font-weight: 600;
      color: #f0f6fc;
      line-height: 1.2;
    }

    .stat-label {
      font-size: 0.8rem;
      color: #8b949e;
      margin-top: 0.25rem;
    }

    /* Status badges */
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 500;
    }

    .status-badge::before {
      content: '';
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    .status-badge.running::before {
      background: #3fb950;
      box-shadow: 0 0 6px #3fb95088;
    }
    .status-badge.eval::before {
      background: #d29922;
      box-shadow: 0 0 6px #d2992288;
    }
    .status-badge.improving::before {
      background: #58a6ff;
      box-shadow: 0 0 6px #58a6ff88;
    }
    .status-badge.idle::before {
      background: #484f58;
    }
    .status-badge.failed::before {
      background: #f85149;
      box-shadow: 0 0 6px #f8514988;
    }
    .status-badge.completed::before {
      background: #3fb950;
    }

    /* Agent status */
    .agent-status-card {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .agent-status-card .status-text {
      font-size: 1.2rem;
      font-weight: 500;
    }

    /* Runs list */
    .runs-list {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }

    .run-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.6rem 0.8rem;
      background: #0d1117;
      border-radius: 8px;
      border-left: 4px solid #30363d;
      font-size: 0.9rem;
    }

    .run-item .run-id {
      font-family: 'SF Mono', 'Fira Code', monospace;
      font-size: 0.8rem;
      color: #8b949e;
    }

    .run-item .run-score {
      font-weight: 500;
    }

    /* Blueprint score history */
    .blueprint-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .blueprint-item {
      background: #0d1117;
      border-radius: 8px;
      padding: 0.8rem;
    }

    .blueprint-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }

    .blueprint-name {
      font-weight: 500;
    }

    .blueprint-latest-score {
      font-size: 0.85rem;
      color: #8b949e;
    }

    .sparkline {
      display: block;
      width: 100%;
      height: 32px;
    }

    .empty-state {
      color: #484f58;
      text-align: center;
      padding: 1.5rem 0;
      font-size: 0.9rem;
    }

    .error-state {
      color: #f85149;
      text-align: center;
      padding: 0.5rem;
      font-size: 0.85rem;
    }

    @media (max-width: 600px) {
      body {
        padding: 1rem;
      }
      header h1 {
        font-size: 1.3rem;
      }
      .stat-value {
        font-size: 1.5rem;
      }
    }
  </style>
</head>
<body>
<div class="container">
  <header>
    <h1>Forge Command Center</h1>
    <span class="last-update" id="lastUpdate">⏳ uppdateras...</span>
  </header>

  <!-- Stats cards -->
  <section class="grid" id="statsGrid">
    <div class="card">
      <h2>Genomsnittlig score</h2>
      <div class="stat-value" id="avgScore">—</div>
      <div class="stat-label">över alla körningar</div>
    </div>
    <div class="card">
      <h2>Totalt antal runs</h2>
      <div class="stat-value" id="totalRuns">—</div>
      <div class="stat-label">inklusive aktiva</div>
    </div>
    <div class="card">
      <h2>Aktiva runs</h2>
      <div class="stat-value" id="activeRunsCount">—</div>
      <div class="stat-label">just nu</div>
    </div>
    <div class="card agent-status-card">
      <h2>Agentstatus</h2>
      <div id="agentStatusContainer">
        <span class="status-text">—</span>
      </div>
    </div>
  </section>

  <!-- Active runs -->
  <section class="card" style="margin-bottom: 2rem;">
    <h2>Aktiva runs</h2>
    <div id="activeRunsList" class="runs-list">
      <div class="empty-state">Inga aktiva runs</div>
    </div>
  </section>

  <!-- Blueprints with score history -->
  <section class="card" style="margin-bottom: 2rem;">
    <h2>Score-historik per blueprint</h2>
    <div id="blueprintList" class="blueprint-list">
      <div class="empty-state">Inga blueprints laddade</div>
    </div>
  </section>
</div>

<script>
  (function() {
    const API_BASE = 'http://localhost:8000';
    const POLL_INTERVAL = 5000;

    const lastUpdateEl = document.getElementById('lastUpdate');
    const avgScoreEl = document.getElementById('avgScore');
    const totalRunsEl = document.getElementById('totalRuns');
    const activeRunsCountEl = document.getElementById('activeRunsCount');
    const agentStatusContainer = document.getElementById('agentStatusContainer');
    const activeRunsListEl = document.getElementById('activeRunsList');
    const blueprintListEl = document.getElementById('blueprintList');

    // Hjälpfunktion: status-badge HTML
    function statusBadge(status) {
      const statusClass = (status || 'unknown').toLowerCase();
      const label = status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Okänd';
      return `<span class="status-badge ${statusClass}">${label}</span>`;
    }

    // Rita sparkline (enkel SVG-linje)
    function renderSparkline(scores, container) {
      if (!scores || scores.length === 0) {
        container.innerHTML = '<span style="color:#484f58;font-size:0.8rem;">ingen data</span>';
        return;
      }

      const width = container.clientWidth || 240;
      const height = 32;
      const padding = 2;
      const plotWidth = width - padding * 2;
      const plotHeight = height - padding * 2;

      const min = Math.min(...scores);
      const max = Math.max(...scores);
      const range = max - min || 1;

      const points = scores.map((s, i) => {
        const x = padding + (i / (scores.length - 1 || 1)) * plotWidth;
        const y = padding + plotHeight - ((s - min) / range) * plotHeight;
        return `${x},${y}`;
      });

      const polyline = points.join(' ');
      const svg = `
        <svg class="sparkline" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
          <polyline fill="none" stroke="#58a6ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" points="${polyline}" />
          <circle cx="${points[points.length-1].split(',')[0]}" cy="${points[points.length-1].split(',')[1]}" r="3" fill="#58a6ff" />
        </svg>
      `;
      container.innerHTML = svg;
    }

    // Uppdatera alla vyer
    async function fetchAll() {
      try {
        const [runsRes, blueprintsRes, statsRes, statusRes] = await Promise.all([
          fetch(`${API_BASE}/api/runs`),
          fetch(`${API_BASE}/api/blueprints`),
          fetch(`${API_BASE}/api/stats`),
          fetch(`${API_BASE}/api/status`)
        ]);

        if (!runsRes.ok || !blueprintsRes.ok || !statsRes.ok || !statusRes.ok) {
          throw new Error('API-svar felaktiga');
        }

        const runs = await runsRes.json();
        const blueprints = await blueprintsRes.json();
        const stats = await statsRes.json();
        const agentStatus = await statusRes.json();

        // --- Stats ---
        const avgScore = stats?.average_score ?? stats?.avg_score ?? stats?.mean_score ?? null;
        avgScoreEl.textContent = avgScore !== null ? avgScore.toFixed(2) : '—';
        const total = stats?.total_runs ?? stats?.total ?? stats?.count ?? null;
        totalRunsEl.textContent = total !== null ? total : '—';

        // --- Aktiva runs ---
        const activeRuns = Array.isArray(runs) ? runs.filter(r => r.status === 'running') : [];
        activeRunsCountEl.textContent = activeRuns.length;

        if (activeRuns.length === 0) {
          activeRunsListEl.innerHTML = '<div class="empty-state">Inga aktiva runs</div>';
        } else {
          activeRunsListEl.innerHTML = activeRuns.map(r => {
            const score = r.score !== undefined && r.score !== null ? r.score.toFixed(2) : '—';
            const id = r.id || r.run_id || '?';
            return `
              <div class="run-item">
                <span class="run-id">#${id}</span>
                <span>${statusBadge(r.status)}</span>
                <span class="run-score">score: ${score}</span>
              </div>
            `;
          }).join('');
        }

        // --- Blueprints & score history ---
        const bpList = Array.isArray(blueprints) ? blueprints : [];
        if (bpList.length === 0) {
          blueprintListEl.innerHTML = '<div class="empty-state">Inga blueprints tillgängliga</div>';
        } else {
          blueprintListEl.innerHTML = bpList.map(bp => {
            const name = bp.name || bp.id || 'Okänd';
            const history = bp.score_history || bp.scores || [];
            const latestScore = history.length > 0 ? history[history.length - 1] : null;

            return `
              <div class="blueprint-item">
                <div class="blueprint-header">
                  <span class="blueprint-name">${name}</span>
                  <span class="blueprint-latest-score">senaste: ${latestScore !== null ? latestScore.toFixed(2) : '—'}</span>
                </div>
                <div class="sparkline-container" style="width:100%;height:32px;"></div>
              </div>
            `;
          }).join('');

          // Rita sparklines efter att DOM uppdaterats
          const bpItems = blueprintListEl.querySelectorAll('.blueprint-item');
          bpList.forEach((bp, idx) => {
            const container = bpItems[idx]?.querySelector('.sparkline-container');
            if (container) {
              const history = bp.score_history || bp.scores || [];
              renderSparkline(history, container);
            }
          });
        }

        // --- Agent status ---
        const statusValue = agentStatus?.status || agentStatus?.agent_status || 'idle';
        agentStatusContainer.innerHTML = statusBadge(statusValue);

        // --- Tidsstämpel ---
        const now = new Date();
        lastUpdateEl.textContent = `senast uppdaterad ${now.toLocaleTimeString('sv-SE')}`;

      } catch (err) {
        console.warn('Pollning misslyckades:', err);
        lastUpdateEl.textContent = '⚠️ uppdatering misslyckades';
        // Visa felen på respektive ställe (men fortsätt försöka)
        if (avgScoreEl.textContent === '—') avgScoreEl.textContent = '⚠️';
        if (totalRunsEl.textContent === '—') totalRunsEl.textContent = '⚠️';
        activeRunsListEl.innerHTML = '<div class="error-state">Kunde inte ladda runs</div>';
        blueprintListEl.innerHTML = '<div class="error-state">Kunde inte ladda blueprints</div>';
        agentStatusContainer.innerHTML = '<span class="error-state">Okänd</span>';
      }
    }

    // Starta polling
    fetchAll();
    setInterval(fetchAll, POLL_INTERVAL);
  })();
</script>
</body>
</html>
```