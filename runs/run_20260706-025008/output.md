Det här är ett komplett, mörkt dashboard i en enda HTML-fil som pollar ditt API var 5:e sekund och visar runs, blueprint-statistik och agentstatus.
```html
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Forge Command Center</title>
    <style>
        /* ---------- Reset & bas ---------- */
        *,
        *::before,
        *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background: #0b0e14;
            color: #e1e6ef;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            font-size: 14px;
            line-height: 1.5;
            padding: 24px 32px;
            min-height: 100vh;
        }

        /* ---------- Layout ---------- */
        .app {
            max-width: 1440px;
            margin: 0 auto;
        }

        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px 24px;
            padding-bottom: 20px;
            border-bottom: 1px solid #1e2532;
            margin-bottom: 24px;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-left h1 {
            font-size: 22px;
            font-weight: 600;
            letter-spacing: -0.3px;
            color: #f0f4ff;
        }

        .badge {
            background: #1a2233;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            color: #8b9bbd;
            border: 1px solid #2a3448;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 18px;
            font-size: 13px;
            color: #8899bb;
        }

        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #2ecc71;
            margin-right: 6px;
            animation: pulse-dot 2s ease-in-out infinite;
        }

        @keyframes pulse-dot {
            0%,
            100% {
                opacity: 1;
            }
            50% {
                opacity: 0.4;
            }
        }

        .status-dot.error {
            background: #e74c3c;
            animation: none;
        }

        .last-updated {
            font-variant-numeric: tabular-nums;
        }

        /* ---------- Stat-kort (top row) ---------- */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }

        .stat-card {
            background: #111820;
            border: 1px solid #1e2636;
            border-radius: 12px;
            padding: 18px 20px;
            transition: border-color 0.2s;
        }

        .stat-card:hover {
            border-color: #2e3a52;
        }

        .stat-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #6f82a3;
            margin-bottom: 6px;
        }

        .stat-value {
            font-size: 28px;
            font-weight: 600;
            color: #f0f4ff;
            line-height: 1.2;
        }

        .stat-sub {
            font-size: 13px;
            color: #6f82a3;
            margin-top: 4px;
        }

        /* ---------- Grid: huvudkolumner ---------- */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 28px;
        }

        @media (max-width: 960px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            body {
                padding: 16px;
            }
        }

        /* ---------- Panel ---------- */
        .panel {
            background: #111820;
            border: 1px solid #1e2636;
            border-radius: 12px;
            overflow: hidden;
        }

        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 20px;
            border-bottom: 1px solid #1a2233;
            background: #0e141e;
        }

        .panel-header h2 {
            font-size: 15px;
            font-weight: 600;
            color: #d6dfef;
        }

        .panel-header .count {
            font-size: 13px;
            color: #6f82a3;
            background: #161f2d;
            padding: 2px 10px;
            border-radius: 12px;
        }

        .panel-body {
            padding: 8px 0;
            max-height: 420px;
            overflow-y: auto;
        }

        .panel-body::-webkit-scrollbar {
            width: 4px;
        }
        .panel-body::-webkit-scrollbar-track {
            background: transparent;
        }
        .panel-body::-webkit-scrollbar-thumb {
            background: #2a3448;
            border-radius: 4px;
        }

        /* ---------- Run-rad ---------- */
        .run-row {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 20px;
            border-bottom: 1px solid #161e2c;
            transition: background 0.15s;
        }
        .run-row:hover {
            background: #0c121e;
        }
        .run-row:last-child {
            border-bottom: none;
        }

        .run-id {
            font-weight: 500;
            color: #d0d9ee;
            min-width: 80px;
            font-size: 13px;
        }

        .run-blueprint {
            color: #8b9bbd;
            font-size: 13px;
            flex: 1;
            min-width: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .run-status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            font-weight: 500;
            padding: 3px 12px;
            border-radius: 20px;
            text-transform: capitalize;
        }

        .run-status .dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .status-running .dot {
            background: #3498db;
        }
        .status-running {
            background: #1a2940;
            color: #7ab7ef;
        }

        .status-completed .dot {
            background: #2ecc71;
        }
        .status-completed {
            background: #1a2e24;
            color: #6fcf97;
        }

        .status-failed .dot {
            background: #e74c3c;
        }
        .status-failed {
            background: #2a1a1a;
            color: #e87a6b;
        }

        .status-evaluating .dot {
            background: #f39c12;
        }
        .status-evaluating {
            background: #2a2418;
            color: #f0c674;
        }

        .status-improving .dot {
            background: #9b59b6;
        }
        .status-improving {
            background: #241a2e;
            color: #c39bd3;
        }

        .status-pending .dot {
            background: #6f82a3;
        }
        .status-pending {
            background: #1a1f2a;
            color: #8b9bbd;
        }

        .run-score {
            font-size: 14px;
            font-weight: 600;
            color: #f0f4ff;
            min-width: 40px;
            text-align: right;
        }

        /* ---------- Agent-kort ---------- */
        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
            gap: 12px;
            padding: 16px 20px;
        }

        .agent-card {
            background: #0c121e;
            border: 1px solid #1a2233;
            border-radius: 10px;
            padding: 14px 16px;
            transition: border-color 0.2s;
        }
        .agent-card:hover {
            border-color: #2a3448;
        }

        .agent-name {
            font-weight: 600;
            font-size: 14px;
            color: #d6dfef;
            margin-bottom: 4px;
        }

        .agent-status {
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 4px;
            text-transform: capitalize;
        }

        .agent-status .dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .agent-blueprint {
            font-size: 12px;
            color: #6f82a3;
            margin-top: 2px;
        }

        .agent-score {
            font-size: 18px;
            font-weight: 600;
            color: #f0f4ff;
            margin-top: 6px;
        }

        /* ---------- Blueprint score-historik ---------- */
        .blueprint-list {
            padding: 8px 0;
        }

        .blueprint-item {
            padding: 12px 20px;
            border-bottom: 1px solid #161e2c;
        }
        .blueprint-item:last-child {
            border-bottom: none;
        }

        .bp-name {
            font-weight: 600;
            font-size: 14px;
            color: #d6dfef;
            margin-bottom: 6px;
        }

        .bp-scores {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        .bp-score-bar {
            flex: 1;
            min-width: 80px;
            height: 6px;
            background: #1a2233;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }

        .bp-score-bar .fill {
            height: 100%;
            border-radius: 4px;
            background: linear-gradient(90deg, #2ecc71, #3498db);
            transition: width 0.6s ease;
        }

        .bp-score-val {
            font-size: 14px;
            font-weight: 600;
            color: #f0f4ff;
            min-width: 36px;
            text-align: right;
        }

        .bp-meta {
            font-size: 12px;
            color: #6f82a3;
            margin-top: 4px;
        }

        /* ---------- Empty / error states ---------- */
        .empty-state {
            text-align: center;
            padding: 32px 20px;
            color: #4d5f7a;
            font-size: 14px;
        }

        .error-state {
            text-align: center;
            padding: 20px;
            color: #e87a6b;
            font-size: 13px;
            background: #1e1414;
            border-radius: 8px;
            margin: 12px 20px;
        }

        /* ---------- Utilities ---------- */
        .flex {
            display: flex;
        }
        .flex-center {
            align-items: center;
        }
        .gap-8 {
            gap: 8px;
        }
        .gap-12 {
            gap: 12px;
        }
        .text-muted {
            color: #6f82a3;
        }
        .text-right {
            text-align: right;
        }
        .mt-4 {
            margin-top: 4px;
        }
        .mt-8 {
            margin-top: 8px;
        }
        .truncate {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Skeleton loading */
        .skeleton {
            background: linear-gradient(90deg, #161e2c 25%, #1a2233 50%, #161e2c 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 6px;
        }

        @keyframes shimmer {
            0% {
                background-position: 200% 0;
            }
            100% {
                background-position: -200% 0;
            }
        }

        .skeleton-line {
            height: 14px;
            margin: 6px 0;
            width: 80%;
        }
        .skeleton-line.short {
            width: 50%;
        }
        .skeleton-line.long {
            width: 95%;
        }

        /* ---------- Scrollbar global (subtil) ---------- */
        ::-webkit-scrollbar {
            width: 4px;
            height: 4px;
        }
        ::-webkit-scrollbar-track {
            background: #0b0e14;
        }
        ::-webkit-scrollbar-thumb {
            background: #2a3448;
            border-radius: 4px;
        }
    </style>
</head>
<body>

    <div class="app" id="app">

        <!-- HEADER -->
        <header class="header">
            <div class="header-left">
                <h1>⚙️ Forge Command Center</h1>
                <span class="badge">v1.0</span>
            </div>
            <div class="header-right">
                <span>
                    <span class="status-dot" id="connectionDot"></span>
                    <span id="connectionLabel">Ansluter</span>
                </span>
                <span class="last-updated" id="lastUpdated">—</span>
            </div>
        </header>

        <!-- STATS ROW -->
        <section class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <div class="stat-label">Totala Runs</div>
                <div class="stat-value" id="statTotalRuns">—</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Aktiva Runs</div>
                <div class="stat-value" id="statActiveRuns">—</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Genomsnittlig Score</div>
                <div class="stat-value" id="statAvgScore">—</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Blueprints</div>
                <div class="stat-value" id="statBlueprints">—</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Agenter</div>
                <div class="stat-value" id="statAgents">—</div>
            </div>
        </section>

        <!-- DASHBOARD GRID -->
        <div class="dashboard-grid">

            <!-- Vänster kolumn: Runs -->
            <section class="panel" id="runsPanel">
                <div class="panel-header">
                    <h2>Aktiva Runs</h2>
                    <span class="count" id="runsCount">0</span>
                </div>
                <div class="panel-body" id="runsBody">
                    <div class="empty-state">Laddar runs …</div>
                </div>
            </section>

            <!-- Höger kolumn: Agenter -->
            <section class="panel" id="agentsPanel">
                <div class="panel-header">
                    <h2>Agent Status</h2>
                    <span class="count" id="agentsCount">0</span>
                </div>
                <div class="panel-body" id="agentsBody">
                    <div class="empty-state">Laddar agenter …</div>
                </div>
            </section>

        </div>

        <!-- Bottenpanel: Blueprints Score-historik -->
        <section class="panel" id="blueprintsPanel">
            <div class="panel-header">
                <h2>Score-historik per Blueprint</h2>
                <span class="count" id="blueprintsCount">0</span>
            </div>
            <div class="panel-body" id="blueprintsBody">
                <div class="empty-state">Laddar blueprints …</div>
            </div>
        </section>

    </div>

    <script>
        (function() {

            'use strict';

            // ---------- API-URL ----------
            const BASE = 'http://localhost:8000';

            // ---------- DOM-referenser ----------
            const $ = (sel) => document.querySelector(sel);
            const $$ = (sel) => document.querySelectorAll(sel);

            const lastUpdatedEl = $('#lastUpdated');
            const connDot = $('#connectionDot');
            const connLabel = $('#connectionLabel');

            // Stats
            const statTotalRuns = $('#statTotalRuns');
            const statActiveRuns = $('#statActiveRuns');
            const statAvgScore = $('#statAvgScore');
            const statBlueprints = $('#statBlueprints');
            const statAgents = $('#statAgents');

            // Runs
            const runsBody = $('#runsBody');
            const runsCount = $('#runsCount');

            // Agents
            const agentsBody = $('#agentsBody');
            const agentsCount = $('#agentsCount');

            // Blueprints
            const blueprintsBody = $('#blueprintsBody');
            const blueprintsCount = $('#blueprintsCount');

            // ---------- Hjälpfunktioner ----------

            function formatTime(isoString) {
                if (!isoString) return '—';
                try {
                    const d = new Date(isoString);
                    return d.toLocaleTimeString('sv-SE', {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                } catch (_) {
                    return '—';
                }
            }

            function nowFormatted() {
                return new Date().toLocaleTimeString('sv-SE', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
            }

            function clamp(value, min, max) {
                return Math.min(max, Math.max(min, value));
            }

            function statusClass(status) {
                const s = (status || '').toLowerCase().trim();
                if (s === 'running') return 'status-running';
                if (s === 'completed' || s === 'complete') return 'status-completed';
                if (s === 'failed') return 'status-failed';
                if (s === 'evaluating') return 'status-evaluating';
                if (s === 'improving') return 'status-improving';
                if (s === 'pending' || s === 'queued') return 'status-pending';
                return 'status-pending';
            }

            function statusDotOnly(status) {
                const s = (status || '').toLowerCase().trim();
                if (s === 'running') return 'running';
                if (s === 'completed' || s === 'complete') return 'completed';
                if (s === 'failed') return 'failed';
                if (s === 'evaluating') return 'evaluating';
                if (s === 'improving') return 'improving';
                return 'pending';
            }

            // ---------- Rendera skeleton ----------
            function renderSkeleton(container, lines = 4) {
                let html = '';
                for (let i = 0; i < lines; i++) {
                    const w = i % 2 === 0 ? 'skeleton-line' : 'skeleton-line short';
                    html += `<div class="skeleton ${w}"></div>`;
                }
                container.innerHTML =
                    `<div style="padding:16px 20px;">${html}</div>`;
            }

            // ---------- Rendera Runs ----------
            function renderRuns(runs) {
                if (!runs || runs.length === 0) {
                    runsBody.innerHTML = `<div class="empty-state">Inga aktiva runs</div>`;
                    runsCount.textContent = '0';
                    return;
                }

                // Sortera: senaste först (om created_at finns)
                const sorted = [...runs].sort((a, b) => {
                    const da = a.created_at || a.started_at || '';
                    const db = b.created_at || b.started_at || '';
                    if (da < db) return 1;
                    if (da > db) return -1;
                    return 0;
                });

                let html = '';
                for (const run of sorted) {
                    const status = run.status || 'unknown';
                    const cls = statusClass(status);
                    const dot = statusDotOnly(status);
                    const score = run.score !== null && run.score !== undefined ? run.score : '—';
                    const scoreDisplay = typeof score === 'number' ? score.toFixed(1) : score;
                    const blueprint = run.blueprint || run.blueprint_id || '—';
                    const id = run.id || run.run_id || '—';
                    const shortId = typeof id === 'string' && id.length > 12 ? id.slice(0, 12) + '…' : id;

                    html += `
                        <div class="run-row">
                            <span class="run-id truncate" title="${id}">${shortId}</span>
                            <span class="run-blueprint truncate" title="${blueprint}">${blueprint}</span>
                            <span class="run-status ${cls}">
                                <span class="dot"></span>
                                ${status}
                            </span>
                            <span class="run-score">${scoreDisplay}</span>
                        </div>
                    `;
                }

                runsBody.innerHTML = html;
                runsCount.textContent = sorted.length;
            }

            // ---------- Rendera Agenter ----------
            function renderAgents(agents) {
                if (!agents || agents.length === 0) {
                    agentsBody.innerHTML = `<div class="empty-state">Inga agenter tillgängliga</div>`;
                    agentsCount.textContent = '0';
                    return;
                }

                let html = '<div class="agent-grid">';
                for (const agent of agents) {
                    const name = agent.name || agent.id || 'Okänd';
                    const status = agent.status || 'unknown';
                    const dot = statusDotOnly(status);
                    const score = agent.score !== null && agent.score !== undefined ? agent.score : '—';
                    const scoreDisplay = typeof score === 'number' ? score.toFixed(1) : score;
                    const blueprint = agent.blueprint || agent.blueprint_id || '—';

                    html += `
                        <div class="agent-card">
                            <div class="agent-name truncate" title="${name}">${name}</div>
                            <div class="agent-status">
                                <span class="dot ${dot}"></span>
                                ${status}
                            </div>
                            <div class="agent-blueprint truncate" title="${blueprint}">${blueprint}</div>
                            <div class="agent-score">${scoreDisplay}</div>
                        </div>
                    `;
                }
                html += '</div>';

                agentsBody.innerHTML = html;
                agentsCount.textContent = agents.length;
            }

            // ---------- Rendera Blueprints (score-historik) ----------
            function renderBlueprints(blueprints) {
                if (!blueprints || blueprints.length === 0) {
                    blueprintsBody.innerHTML = `<div class="empty-state">Inga blueprints tillgängliga</div>`;
                    blueprintsCount.textContent = '0';
                    return;
                }

                let html = '<div class="blueprint-list">';
                for (const bp of blueprints) {
                    const name = bp.name || bp.id || 'Okänd';
                    const scores = bp.scores || bp.recent_scores || [];
                    const avgScore = bp.avg_score ?? bp.average_score ?? null;
                    const runCount = bp.run_count ?? bp.total_runs ?? scores.length;

                    // Visa senaste 5 scores som en mini bar
                    const recent = scores.slice(-5);
                    const maxScore = Math.max(...recent, 1);

                    let barsHtml = '';
                    for (const s of recent) {
                        const pct = (s / (bp.max_score || 100)) * 100;
                        const clamped = clamp(pct, 0, 100);
                        barsHtml += `<span class="bp-score-bar"><span class="fill" style="width:${clamped}%"></span></span>`;
                    }

                    if (!barsHtml) {
                        barsHtml = `<span class="text-muted" style="font-size:12px;">Ingen data</span>`;
                    }

                    const avgDisplay = avgScore !== null ? avgScore.toFixed(1) : '—';

                    html += `
                        <div class="blueprint-item">
                            <div class="bp-name truncate" title="${name}">${name}</div>
                            <div class="bp-scores">
                                ${barsHtml}
                                <span class="bp-score-val">${avgDisplay}</span>
                            </div>
                            <div class="bp-meta">${runCount} runs · senaste ${recent.length} värden</div>
                        </div>
                    `;
                }
                html += '</div>';

                blueprintsBody.innerHTML = html;
                blueprintsCount.textContent = blueprints.length;
            }

            // ---------- Rendera Stats ----------
            function renderStats(stats) {
                if (!stats) return;

                const total = stats.total_runs ?? stats.totalRuns ?? stats.runs ?? '—';
                const active = stats.active_runs ?? stats.activeRuns ?? stats.active ?? '—';
                const avg = stats.avg_score ?? stats.averageScore ?? stats.average ?? '—';
                const bps = stats.blueprints ?? stats.totalBlueprints ?? stats.blueprint_count ?? '—';
                const agents = stats.agents ?? stats.totalAgents ?? stats.agent_count ?? '—';

                statTotalRuns.textContent = typeof total === 'number' ? total : total;
                statActiveRuns.textContent = typeof active === 'number' ? active : active;
                statAvgScore.textContent = typeof avg === 'number' ? avg.toFixed(1) : avg;
                statBlueprints.textContent = typeof bps === 'number' ? bps : bps;
                statAgents.textContent = typeof agents === 'number' ? agents : agents;
            }

            // ---------- Hämta alla data ----------
            async function fetchAll() {
                const results = await Promise.allSettled([
                    fetch(`${BASE}/api/runs`).then(r => r.ok ? r.json() : Promise.reject(r.status)),
                    fetch(`${BASE}/api/blueprints`).then(r => r.ok ? r.json() : Promise.reject(r.status)),
                    fetch(`${BASE}/api/stats`).then(r => r.ok ? r.json() : Promise.reject(r.status)),
                    fetch(`${BASE}/api/status`).then(r => r.ok ? r.json() : Promise.reject(r.status)),
                ]);

                return {
                    runs: results[0].status === 'fulfilled' ? results[0].value : null,
                    blueprints: results[1].status === 'fulfilled' ? results[1].value : null,
                    stats: results[2].status === 'fulfilled' ? results[2].value : null,
                    status: results[3].status === 'fulfilled' ? results[3].value : null,
                    errors: results.map((r, i) => r.status === 'rejected' ? i : null).filter(i => i !== null),
                };
            }

            // ---------- Uppdatera hela dashboard ----------
            async function refreshDashboard() {
                // Visa skeletons om första laddning (innehåller "Laddar")
                const needsSkeleton = runsBody.innerHTML.includes('Laddar');

                const data = await fetchAll();

                const hasErrors = data.errors.length > 0;

                // Uppdatera anslutningsstatus
                if (hasErrors) {
                    connDot.className = 'status-dot error';
                    connLabel.textContent = 'API-fel';
                } else {
                    connDot.className = 'status-dot';
                    connLabel.textContent = 'Ansluten';
                }

                // Stats (även om delvis fel, visa det vi har)
                if (data.stats) {
                    renderStats(data.stats);
                } else {
                    // Försök extrahera stats från runs/blueprints om /api/stats misslyckades
                    const runs = data.runs;
                    const bps = data.blueprints;
                    const agents = data.status ? (data.status.agents || []) : [];

                    const total = runs ? runs.length : '—';
                    const active = runs ? runs.filter(r => (r.status || '').toLowerCase() === 'running').length : '—';
                    const avg = (runs && runs.length > 0) ?
                        runs.filter(r => r.score !== null && r.score !== undefined)
                        .reduce((sum, r, _, arr) => arr.length ? sum + r.score : 0, 0) /
                        runs.filter(r => r.score !== null && r.score !== undefined).length || '—' :
                        '—';
                    const bpsCount = bps ? bps.length : '—';
                    const agentsCountVal = agents.length || '—';

                    statTotalRuns.textContent = typeof total === 'number' ? total : total;
                    statActiveRuns.textContent = typeof active === 'number' ? active : active;
                    statAvgScore.textContent = typeof avg === 'number' ? avg.toFixed(1) : avg;
                    statBlueprints.textContent = typeof bpsCount === 'number' ? bpsCount : bpsCount;
                    statAgents.textContent = typeof agentsCountVal === 'number' ? agentsCountVal : agentsCountVal;
                }

                // Runs
                if (data.runs) {
                    renderRuns(data.runs);
                } else if (needsSkeleton) {
                    renderSkeleton(runsBody, 5);
                }

                // Blueprints
                if (data.blueprints) {
                    renderBlueprints(data.blueprints);
                } else if (needsSkeleton) {
                    renderSkeleton(blueprintsBody, 4);
                }

                // Agents — från /api/status eller fallback
                let agentsData = null;
                if (data.status && data.status.agents) {
                    agentsData = data.status.agents;
                } else if (data.status && Array.isArray(data.status)) {
                    agentsData = data.status;
                } else if (data.blueprints) {
                    // Fallback: bygg agenter från blueprints om möjligt
                    agentsData = data.blueprints.map(bp => ({
                        name: bp.name || bp.id,
                        status: 'idle',
                        score: bp.avg_score ?? null,
                        blueprint: bp.name || bp.id,
                    }));
                }

                if (agentsData) {
                    renderAgents(agentsData);
                } else if (needsSkeleton) {
                    renderSkeleton(agentsBody, 4);
                }

                // Tidstämpel
                lastUpdatedEl.textContent = `Uppdaterat ${nowFormatted()}`;
            }

            // ---------- Start polling ----------
            let pollInterval = null;

            function startPolling() {
                // Kör direkt
                refreshDashboard();

                // Därefter var 5:e sekund
                if (pollInterval) clearInterval(pollInterval);
                pollInterval = setInterval(refreshDashboard, 5000);
            }

            // ---------- Lyssnare för paus vid tab change (sparar resurser) ----------
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    if (pollInterval) {
                        clearInterval(pollInterval);
                        pollInterval = null;
                    }
                } else {
                    startPolling();
                }
            });

            // ---------- Start ----------
            startPolling();

        })();
    </script>

</body>
</html>
```
### Dashboard-funktioner

Så här fungerar de fyra huvudvyerna:

- **Statistiköversikt** – Överst visas fem kort med totala runs, aktiva runs, genomsnittlig score, antal blueprints och agenter. Värdena hämtas från `/api/stats` eller beräknas från övrig data om endpointen skulle vara otillgänglig.
- **Aktiva runs** – Listar alla runs sorterade efter tid (senaste först). Varje rad visar run-ID, blueprint-namn, färgkodad status (running, completed, failed, evaluating, improving, pending) och aktuell score.
- **Agentstatus** – Presenterar varje agent som ett kort med namn, statusindikator, blueprint-tillhörighet och score. Data hämtas från `/api/status` med automatisk nedfall till blueprints om agent-endpointen saknas.
- **Score-historik per blueprint** – För varje blueprint visas de senaste 5 score-värdena som horisontella staplar, genomsnittlig score samt antal runs. Staplarnas bredd speglar poängen relativt maxvärdet.

**Anslutningsstatus** visas i headern – en grön pulserande prick indikerar aktiv anslutning, röd prick signalerar API-fel. Alla sektioner uppdateras automatiskt var 5:e sekund, och polling pausas när fliken är osynlig för att spara resurser.