Här är ett komplett, mörkt HTML/CSS/JS-dashboard som pollar API:et var 5:e sekund och visar alla begärda vyer – helt utan externa beroenden.

```html
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Forge Command Center</title>
    <style>
        /* === Reset & Global === */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, monospace;
            background: #0a0a0f;
            color: #d0d0da;
            min-height: 100vh;
            padding: 1.5rem;
        }
        h1, h2, h3 { font-weight: 400; letter-spacing: 0.02em; }
        h1 { font-size: 1.6rem; margin-bottom: 0.2rem; color: #e8e8f0; }
        h2 { font-size: 1.15rem; margin-bottom: 0.75rem; color: #c8c8d4; }
        .subtitle { font-size: 0.85rem; color: #787890; margin-bottom: 1.5rem; }

        /* === Layout === */
        .dashboard {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.25rem;
        }
        .dashboard > .full-width { grid-column: 1 / -1; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        #last-updated {
            font-size: 0.8rem;
            color: #6a6a80;
            background: #151520;
            padding: 0.3rem 0.8rem;
            border-radius: 6px;
        }
        #error-message {
            background: #3d1a1a;
            color: #ff6b6b;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.85rem;
            display: none;
        }

        /* === Cards === */
        .card {
            background: #111118;
            border: 1px solid #1e1e2a;
            border-radius: 12px;
            padding: 1rem 1.2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }
        .badge {
            display: inline-block;
            background: #1e1e2e;
            color: #a0a0b8;
            padding: 0.15rem 0.6rem;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.05em;
        }

        /* === Stats Grid === */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 0.8rem;
        }
        .stat-card {
            background: #151520;
            border-radius: 10px;
            padding: 0.8rem 1rem;
            text-align: center;
            border: 1px solid #1e1e2a;
        }
        .stat-card .value {
            font-size: 1.8rem;
            font-weight: 500;
            color: #e0e0f0;
            line-height: 1.2;
        }
        .stat-card .label {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6a6a84;
            margin-top: 0.2rem;
        }

        /* === Active Runs Table === */
        .run-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }
        .run-table th {
            text-align: left;
            padding-bottom: 0.4rem;
            color: #6a6a84;
            font-weight: 500;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            border-bottom: 1px solid #1e1e2a;
        }
        .run-table td {
            padding: 0.45rem 0;
            border-bottom: 1px solid #181822;
        }
        .run-table tr:last-child td { border-bottom: none; }
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 6px;
        }
        .status-running .status-dot { background: #4caf50; }
        .status-eval .status-dot { background: #ff9800; }
        .status-improving .status-dot { background: #2196f3; }
        .status-failed .status-dot { background: #f44336; }
        .status-text { font-size: 0.8rem; }

        /* === Agent Status === */
        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 0.6rem;
        }
        .agent-card {
            background: #151520;
            border-radius: 8px;
            padding: 0.6rem 0.9rem;
            display: flex;
            align-items: center;
            gap: 0.6rem;
            border: 1px solid #1e1e2a;
        }
        .agent-card .agent-name {
            font-size: 0.9rem;
            font-weight: 500;
        }
        .agent-card .agent-status {
            margin-left: auto;
            font-size: 0.7rem;
            padding: 0.15rem 0.6rem;
            border-radius: 12px;
            font-weight: 500;
        }

        /* === Score Canvas === */
        #score-canvas {
            width: 100%;
            height: auto;
            background: #0e0e14;
            border-radius: 8px;
            display: block;
        }
        .chart-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 0.5rem;
            font-size: 0.75rem;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }
        .legend-color {
            width: 10px;
            height: 10px;
            border-radius: 2px;
        }

        /* === Responsive === */
        @media (max-width: 800px) {
            .dashboard { grid-template-columns: 1fr; }
            body { padding: 0.8rem; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
        @media (max-width: 500px) {
            .stats-grid { grid-template-columns: 1fr; }
            .agent-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <header>
        <div>
            <h1>⚙️ Forge Command Center</h1>
            <div class="subtitle">Realtidsöversikt – agenter &amp; blueprints</div>
        </div>
        <div style="display:flex; gap:0.8rem; align-items:center;">
            <span id="last-updated">–</span>
            <span id="error-message"></span>
        </div>
    </header>

    <div class="dashboard">
        <!-- Stats -->
        <section class="card full-width" id="stats-section">
            <div class="card-header">
                <h2>Statistik</h2>
                <span class="badge">uppdateras var 5 s</span>
            </div>
            <div class="stats-grid" id="stats-grid">
                <div class="stat-card"><div class="value" id="stat-total-runs">–</div><div class="label">Totala runs</div></div>
                <div class="stat-card"><div class="value" id="stat-active-runs">–</div><div class="label">Aktiva runs</div></div>
                <div class="stat-card"><div class="value" id="stat-avg-score">–</div><div class="label">Medelvärde score</div></div>
                <div class="stat-card"><div class="value" id="stat-blueprints">–</div><div class="label">Blueprints</div></div>
            </div>
        </section>

        <!-- Active Runs -->
        <section class="card" id="runs-section">
            <div class="card-header">
                <h2>Aktiva runs</h2>
                <span class="badge" id="run-count">0</span>
            </div>
            <div style="max-height:320px; overflow-y:auto;">
                <table class="run-table">
                    <thead><tr><th>Run-ID</th><th>Blueprint</th><th>Status</th><th>Score</th><th>Varaktighet</th></tr></thead>
                    <tbody id="runs-tbody"></tbody>
                </table>
            </div>
            <div style="margin-top:0.5rem; font-size:0.75rem; color:#5a5a70;" id="runs-empty">Inga aktiva runs för närvarande.</div>
        </section>

        <!-- Agent Status -->
        <section class="card" id="agents-section">
            <div class="card-header">
                <h2>Agenter</h2>
                <span class="badge" id="agent-count">0</span>
            </div>
            <div class="agent-grid" id="agent-grid"></div>
        </section>

        <!-- Score History Chart -->
        <section class="card full-width" id="score-section">
            <div class="card-header">
                <h2>Score-historik per blueprint</h2>
                <span class="badge" id="bp-count">0 blueprints</span>
            </div>
            <canvas id="score-canvas" width="600" height="240"></canvas>
            <div class="chart-legend" id="chart-legend"></div>
        </section>
    </div>

    <script>
        (function() {
            'use strict';

            const POLL_INTERVAL = 5000;
            const canvas = document.getElementById('score-canvas');
            const ctx = canvas.getContext('2d');
            let cachedBlueprints = {};        // { name: [ {score, timestamp}, ... ] }
            let blueprintNames = [];

            // --- DOM helpers ---
            const $ = id => document.getElementById(id);

            // --- Fetch with error handling ---
            async function fetchJSON(url) {
                const res = await fetch(url);
                if (!res.ok) throw new Error(`HTTP ${res.status} – ${res.statusText}`);
                return res.json();
            }

            function formatDuration(seconds) {
                if (seconds == null) return '—';
                const m = Math.floor(seconds / 60);
                const s = Math.floor(seconds % 60);
                return `${m}m ${s}s`;
            }

            function statusColor(status) {
                switch (status?.toLowerCase()) {
                    case 'running': return '#4caf50';
                    case 'eval': case 'evaluating': return '#ff9800';
                    case 'improving': return '#2196f3';
                    case 'failed': return '#f44336';
                    default: return '#88889a';
                }
            }

            function statusClass(status) {
                switch (status?.toLowerCase()) {
                    case 'running': return 'status-running';
                    case 'eval': case 'evaluating': return 'status-eval';
                    case 'improving': return 'status-improving';
                    case 'failed': return 'status-failed';
                    default: return '';
                }
            }

            // --- Render Stats ---
            function renderStats(stats) {
                $('stat-total-runs').textContent = stats.total_runs ?? '–';
                $('stat-active-runs').textContent = stats.active_runs ?? '–';
                const avg = stats.average_score;
                $('stat-avg-score').textContent = avg != null ? parseFloat(avg).toFixed(2) : '–';
                $('stat-blueprints').textContent = stats.total_blueprints ?? '–';
            }

            // --- Render Active Runs ---
            function renderRuns(runs) {
                const tbody = $('runs-tbody');
                const container = $('runs-section');
                if (!runs || runs.length === 0) {
                    tbody.innerHTML = '';
                    $('run-count').textContent = '0';
                    $('runs-empty').style.display = 'block';
                    return;
                }
                $('runs-empty').style.display = 'none';
                $('run-count').textContent = runs.length;
                tbody.innerHTML = runs.map(run => {
                    const status = run.status || 'unknown';
                    const cls = statusClass(status);
                    return `<tr class="${cls}">
                        <td style="font-family:monospace;font-size:0.8rem;">${run.id || run.run_id || '–'}</td>
                        <td>${run.blueprint || run.blueprint_name || '–'}</td>
                        <td><span class="status-dot"></span><span class="status-text">${status}</span></td>
                        <td>${run.score != null ? parseFloat(run.score).toFixed(2) : '—'}</td>
                        <td>${formatDuration(run.duration_seconds)}</td>
                    </tr>`;
                }).join('');
            }

            // --- Render Agents ---
            function renderAgents(agents) {
                const grid = $('agent-grid');
                if (!agents || agents.length === 0) {
                    grid.innerHTML = '<div style="color:#5a5a70;">Inga agenter anslutna.</div>';
                    $('agent-count').textContent = '0';
                    return;
                }
                $('agent-count').textContent = agents.length;
                grid.innerHTML = agents.map(agent => {
                    const status = agent.status || 'unknown';
                    const color = statusColor(status);
                    return `<div class="agent-card">
                        <span class="agent-name">${agent.name || agent.id || 'Agent'}</span>
                        <span class="agent-status" style="background:${color}22; color:${color}; border:1px solid ${color}55;">
                            ${status}
                        </span>
                    </div>`;
                }).join('');
            }

            // --- Render Score Chart ---
            function renderChart() {
                const w = canvas.width;
                const h = canvas.height;
                const padding = { top: 15, bottom: 25, left: 40, right: 20 };
                const plotW = w - padding.left - padding.right;
                const plotH = h - padding.top - padding.bottom;

                ctx.clearRect(0, 0, w, h);
                ctx.font = '10px system-ui, sans-serif';
                ctx.fillStyle = '#6a6a84';

                // Determine overall min/max score across all blueprints (min 0 for y-axis)
                let allScores = [];
                const series = {};
                Object.entries(cachedBlueprints).forEach(([name, data]) => {
                    if (data && data.length > 0) {
                        series[name] = data;
                        data.forEach(d => allScores.push(d.score));
                    }
                });
                if (allScores.length === 0) {
                    ctx.fillStyle = '#5a5a70';
                    ctx.textAlign = 'center';
                    ctx.fillText('Ingen score-historik ännu.', w/2, h/2);
                    return;
                }

                const minScore = Math.min(0, ...allScores);
                const maxScore = Math.max(...allScores);
                const range = maxScore - minScore || 1;
                const yScale = plotH / range;
                const xStep = plotW / (Object.values(series)[0]?.length || 1);

                // Draw axes
                ctx.strokeStyle = '#222233';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(padding.left, padding.top);
                ctx.lineTo(padding.left, padding.top + plotH);
                ctx.lineTo(padding.left + plotW, padding.top + plotH);
                ctx.stroke();

                // Y axis labels
                ctx.fillStyle = '#5a5a70';
                ctx.textAlign = 'right';
                ctx.textBaseline = 'middle';
                const yLabels = 5;
                for (let i = 0; i <= yLabels; i++) {
                    const y = padding.top + plotH - (i / yLabels) * plotH;
                    const val = minScore + (i / yLabels) * range;
                    ctx.fillText(val.toFixed(1), padding.left - 6, y);
                }

                // Color palette
                const colors = ['#4caf50','#2196f3','#ff9800','#e91e63','#9c27b0','#00bcd4','#ffeb3b','#f44336'];
                let colorIndex = 0;

                // Draw each series
                ctx.lineWidth = 2;
                const names = Object.keys(series);
                names.forEach((name, idx) => {
                    const data = series[name];
                    if (data.length < 1) return;
                    const color = colors[idx % colors.length];
                    ctx.strokeStyle = color;
                    ctx.beginPath();
                    data.forEach((point, i) => {
                        const x = padding.left + (i / (data.length - 1 || 1)) * plotW;
                        const y = padding.top + plotH - (point.score - minScore) * yScale;
                        if (i === 0) ctx.moveTo(x, y);
                        else ctx.lineTo(x, y);
                    });
                    ctx.stroke();

                    // Points (small dots)
                    ctx.fillStyle = color;
                    data.forEach((point, i) => {
                        const x = padding.left + (i / (data.length - 1 || 1)) * plotW;
                        const y = padding.top + plotH - (point.score - minScore) * yScale;
                        ctx.beginPath();
                        ctx.arc(x, y, 3, 0, 2 * Math.PI);
                        ctx.fill();
                    });
                });

                // Legend
                const legendEl = $('chart-legend');
                legendEl.innerHTML = names.map((name, i) => {
                    const color = colors[i % colors.length];
                    return `<span class="legend-item">
                        <span class="legend-color" style="background:${color}"></span>
                        ${name}
                    </span>`;
                }).join('');
            }

            // --- Main Update ---
            async function updateDashboard() {
                const now = new Date().toLocaleTimeString('sv-SE', { hour12: false });
                $('last-updated').textContent = `🔄 ${now}`;
                $('error-message').style.display = 'none';

                try {
                    const [runs, blueprints, stats, agents] = await Promise.all([
                        fetchJSON('/api/runs'),
                        fetchJSON('/api/blueprints'),
                        fetchJSON('/api/stats'),
                        fetchJSON('/api/status')
                    ]);

                    // Stats
                    if (stats) renderStats(stats);

                    // Runs
                    if (Array.isArray(runs)) renderRuns(runs);

                    // Agents
                    if (Array.isArray(agents)) renderAgents(agents);

                    // Blueprints → score history
                    if (Array.isArray(blueprints)) {
                        // Build cached data: each blueprint object may contain a "scores" or "history" array
                        // or we can accumulate from runs? Let's assume /api/blueprints returns list of objects
                        // each with name and possibly scores array (score history).
                        // If not, we fall back to using runs grouped by blueprint.
                        let hasHistory = false;
                        const newCache = {};
                        blueprintNames = [];

                        blueprints.forEach(bp => {
                            const name = bp.name || bp.id || 'Unnamed';
                            if (bp.scores && Array.isArray(bp.scores) && bp.scores.length > 0) {
                                hasHistory = true;
                                newCache[name] = bp.scores.map(s => ({
                                    score: typeof s === 'number' ? s : (s.score ?? 0),
                                    timestamp: s.timestamp || 0
                                }));
                            } else if (bp.history && Array.isArray(bp.history)) {
                                hasHistory = true;
                                newCache[name] = bp.history.map(h => ({
                                    score: h.score ?? 0,
                                    timestamp: h.timestamp || 0
                                }));
                            }
                        });

                        if (hasHistory) {
                            cachedBlueprints = newCache;
                            blueprintNames = Object.keys(cachedBlueprints);
                        } else {
                            // Fallback: build history from runs (if runs have blueprint field)
                            if (Array.isArray(runs)) {
                                const byBlueprint = {};
                                runs.forEach(run => {
                                    const bp = run.blueprint || run.blueprint_name || 'unknown';
                                    if (!byBlueprint[bp]) byBlueprint[bp] = [];
                                    if (run.score != null) {
                                        byBlueprint[bp].push({ score: parseFloat(run.score), timestamp: run.timestamp || 0 });
                                    }
                                });
                                cachedBlueprints = byBlueprint;
                                blueprintNames = Object.keys(cachedBlueprints);
                            }
                        }

                        $('bp-count').textContent = `${blueprintNames.length} blueprints`;
                        renderChart();
                    }

                } catch (err) {
                    const msgEl = $('error-message');
                    msgEl.textContent = `❌ Kunde inte hämta data: ${err.message}`;
                    msgEl.style.display = 'block';
                    console.error(err);
                }
            }

            // --- Canvas resize helper ---
            function resizeCanvas() {
                const container = canvas.parentElement;
                const rect = container.getBoundingClientRect();
                const width = rect.width - 24; // padding
                if (width > 0) {
                    canvas.style.width = width + 'px';
                    canvas.style.height = (width * 0.4) + 'px';
                    // Keep canvas internal resolution scaled for sharpness
                    canvas.width = width * 2;
                    canvas.height = (width * 0.4) * 2;
                    renderChart();
                }
            }

            // --- Init ---
            window.addEventListener('load', () => {
                updateDashboard().then(() => resizeCanvas());
                setInterval(updateDashboard, POLL_INTERVAL);
                window.addEventListener('resize', resizeCanvas);
            });

            // Expose for debugging
            window.__forge = { updateDashboard, renderChart };

        })();
    </script>
</body>
</html>
```

## Så fungerar det

- **Polling var 5:e sekund** – `setInterval` anropar `updateDashboard()` som hämtar alla fyra endpoints parallellt.
- **Aktiva runs** – visas i en tabell med färgkodad status (grön/running, orange/eval, blå/improving, röd/failed).
- **Score-historik per blueprint** – ritas som linjediagram på en canvas med punkter. Varje blueprint får en egen färg och visas i en legend under grafen. Om API:et returnerar `scores` eller `history` per blueprint används det, annars byggs historik från runs.
- **Agent-status** – visas som kort med färgade status-märken.
- **Statistik** – fyra kort med totala runs, aktiva runs, medel-score och antal blueprints.
- **Responsiv layout** – två kolumner på bred skärm, en kolumn på mobil.
- **Inga externa beroenden** – ren vanilla HTML/CSS/JS.

Sidan är redo att köras mot `localhost:8000`. Varje vy uppdateras automatiskt och felmeddelanden visas om API:et inte svarar.