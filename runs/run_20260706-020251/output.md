Här är ett mörkt dashboard som pollar ditt API var 5:e sekund och visar aktiva runs, score-historik och agentstatus – allt i en enda HTML-fil utan externa beroenden.
```html
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Forge Command Center</title>
    <style>
        /* ===== RESET & BASE ===== */
        *,
        *::before,
        *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
            background: #0d0f14;
            color: #e4e7ed;
            padding: 24px 32px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* ===== SCROLLBAR ===== */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #1a1d24;
        }
        ::-webkit-scrollbar-thumb {
            background: #2f3540;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #3f4652;
        }

        /* ===== HEADER ===== */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid #1f232b;
            margin-bottom: 24px;
            flex-wrap: wrap;
            gap: 12px;
        }
        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .header-left h1 {
            font-size: 22px;
            font-weight: 600;
            letter-spacing: 0.3px;
            color: #f0f3f8;
        }
        .badge-version {
            font-size: 11px;
            background: #1f232b;
            color: #7a8394;
            padding: 2px 10px;
            border-radius: 12px;
            border: 1px solid #2a2f3a;
        }
        .header-right {
            display: flex;
            align-items: center;
            gap: 18px;
            font-size: 13px;
            color: #7a8394;
        }
        .last-updated {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .last-updated .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #2a8f5e;
            display: inline-block;
            animation: pulse-dot 2s infinite;
        }
        @keyframes pulse-dot {
            0%,
            100% {
                opacity: 1;
                transform: scale(1);
            }
            50% {
                opacity: 0.5;
                transform: scale(0.85);
            }
        }
        .last-updated .dot.offline {
            background: #5a3e3e;
            animation: none;
        }
        .refresh-btn {
            background: #1f232b;
            border: 1px solid #2a2f3a;
            color: #aab2c0;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: background 0.15s;
        }
        .refresh-btn:hover {
            background: #2a2f3a;
            color: #e4e7ed;
        }
        .refresh-btn:active {
            background: #333945;
        }

        /* ===== STATS ROW ===== */
        .stats-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }
        .stat-card {
            background: #12151b;
            border: 1px solid #1f232b;
            border-radius: 10px;
            padding: 16px 18px;
            transition: border-color 0.2s;
        }
        .stat-card:hover {
            border-color: #2f3540;
        }
        .stat-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #6b7382;
            margin-bottom: 6px;
        }
        .stat-value {
            font-size: 28px;
            font-weight: 600;
            color: #f0f3f8;
            line-height: 1.2;
        }
        .stat-value .unit {
            font-size: 16px;
            font-weight: 400;
            color: #6b7382;
            margin-left: 4px;
        }
        .stat-sub {
            font-size: 12px;
            color: #4e5563;
            margin-top: 4px;
        }

        /* ===== GRID LAYOUT ===== */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            flex: 1;
        }
        .panel {
            background: #12151b;
            border: 1px solid #1f232b;
            border-radius: 10px;
            padding: 18px 20px 20px;
            display: flex;
            flex-direction: column;
            min-height: 300px;
        }
        .panel-full {
            grid-column: 1 / -1;
            min-height: 200px;
        }
        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
            flex-wrap: wrap;
            gap: 8px;
        }
        .panel-header h2 {
            font-size: 15px;
            font-weight: 600;
            color: #d0d5df;
            letter-spacing: 0.2px;
        }
        .panel-header .count-badge {
            font-size: 11px;
            background: #1f232b;
            color: #8a94a6;
            padding: 1px 10px;
            border-radius: 10px;
            border: 1px solid #2a2f3a;
        }
        .panel-body {
            flex: 1;
            overflow-y: auto;
            min-height: 0;
        }

        /* ===== RUNS TABLE ===== */
        .runs-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        .runs-table th {
            text-align: left;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            color: #5e6675;
            padding: 6px 8px 8px 0;
            border-bottom: 1px solid #1f232b;
            font-weight: 500;
        }
        .runs-table td {
            padding: 8px 8px 8px 0;
            border-bottom: 1px solid #181b22;
            color: #cdd2dc;
            vertical-align: middle;
        }
        .runs-table tr:last-child td {
            border-bottom: none;
        }
        .runs-table .col-id {
            width: 40px;
            color: #5e6675;
            font-size: 12px;
        }
        .runs-table .col-name {
            min-width: 110px;
        }
        .runs-table .col-blueprint {
            color: #7a8394;
            font-size: 12px;
        }
        .runs-table .col-status {
            width: 100px;
        }
        .runs-table .col-score {
            width: 70px;
            text-align: right;
            font-variant-numeric: tabular-nums;
        }

        /* ===== STATUS BADGES ===== */
        .status-badge {
            display: inline-block;
            font-size: 11px;
            font-weight: 500;
            padding: 2px 12px;
            border-radius: 12px;
            letter-spacing: 0.2px;
            background: #1a1d24;
            border: 1px solid #2a2f3a;
            color: #8a94a6;
        }
        .status-badge.running {
            background: #0f2a1f;
            border-color: #1f6b44;
            color: #4bc689;
        }
        .status-badge.eval {
            background: #1f2633;
            border-color: #3b5080;
            color: #7a9ce0;
        }
        .status-badge.improving {
            background: #2a1f1a;
            border-color: #7a4a2a;
            color: #dba05a;
        }
        .status-badge.completed {
            background: #0f1a1f;
            border-color: #1a4a5a;
            color: #5ab8d0;
        }
        .status-badge.failed {
            background: #2a0f0f;
            border-color: #6b2a2a;
            color: #d05a5a;
        }
        .status-badge.idle {
            background: #1a1d24;
            border-color: #2a2f3a;
            color: #6b7382;
        }

        .score-value {
            font-weight: 500;
            font-variant-numeric: tabular-nums;
        }
        .score-value.high {
            color: #4bc689;
        }
        .score-value.mid {
            color: #dba05a;
        }
        .score-value.low {
            color: #d05a5a;
        }

        /* ===== SCORE HISTORY (bars) ===== */
        .blueprint-list {
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .blueprint-item {
            background: #0f1218;
            border-radius: 6px;
            padding: 12px 14px;
            border: 1px solid #1a1e26;
        }
        .blueprint-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            flex-wrap: wrap;
            gap: 6px;
        }
        .blueprint-name {
            font-weight: 500;
            font-size: 13px;
            color: #d8dde8;
        }
        .blueprint-avg {
            font-size: 12px;
            color: #6b7382;
        }
        .blueprint-avg strong {
            color: #c8cedb;
            font-weight: 500;
        }
        .bar-chart {
            display: flex;
            gap: 3px;
            align-items: flex-end;
            height: 40px;
            padding-top: 4px;
        }
        .bar {
            flex: 1;
            min-width: 4px;
            border-radius: 2px 2px 0 0;
            background: #1f2733;
            transition: background 0.2s, height 0.3s ease;
            position: relative;
        }
        .bar.filled {
            background: #2a6b4a;
        }
        .bar.filled.mid {
            background: #6b5a2a;
        }
        .bar.filled.low {
            background: #5a2a2a;
        }
        .bar.empty {
            background: #181c24;
        }

        /* ===== AGENT STATUS ===== */
        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 10px;
        }
        .agent-card {
            background: #0f1218;
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 12px 14px;
            transition: border-color 0.2s;
        }
        .agent-card:hover {
            border-color: #2a2f3a;
        }
        .agent-name {
            font-size: 13px;
            font-weight: 500;
            color: #d0d5df;
            margin-bottom: 4px;
        }
        .agent-status-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 2px;
        }
        .agent-status-badge {
            font-size: 10px;
            padding: 1px 10px;
            border-radius: 10px;
            font-weight: 500;
            background: #1a1d24;
            border: 1px solid #2a2f3a;
            color: #6b7382;
            text-transform: lowercase;
        }
        .agent-status-badge.running {
            background: #0f2a1f;
            border-color: #1f6b44;
            color: #4bc689;
        }
        .agent-status-badge.eval {
            background: #1f2633;
            border-color: #3b5080;
            color: #7a9ce0;
        }
        .agent-status-badge.improving {
            background: #2a1f1a;
            border-color: #7a4a2a;
            color: #dba05a;
        }
        .agent-status-badge.idle {
            background: #1a1d24;
            border-color: #2a2f3a;
            color: #5e6675;
        }
        .agent-run-id {
            font-size: 10px;
            color: #4e5563;
        }

        /* ===== EMPTY STATE ===== */
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            min-height: 120px;
            color: #3f4652;
            font-size: 13px;
            gap: 4px;
        }
        .empty-state .icon {
            font-size: 28px;
            opacity: 0.4;
            margin-bottom: 4px;
        }

        /* ===== FOOTER ===== */
        .footer {
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid #1f232b;
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: #3f4652;
            flex-wrap: wrap;
            gap: 8px;
        }
        .footer .errors {
            color: #6b3f3f;
        }
        .footer .ok {
            color: #2a6b4a;
        }

        /* ===== RESPONSIVE ===== */
        @media (max-width: 960px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            body {
                padding: 16px;
            }
        }
        @media (max-width: 480px) {
            .header {
                flex-direction: column;
                align-items: flex-start;
            }
            .stats-row {
                grid-template-columns: 1fr 1fr;
            }
            .agent-grid {
                grid-template-columns: 1fr 1fr;
            }
            .runs-table .col-blueprint {
                display: none;
            }
            .runs-table .col-id {
                width: 28px;
            }
        }
    </style>
</head>
<body>

    <!-- ===== HEADER ===== -->
    <header class="header">
        <div class="header-left">
            <h1>Forge Command Center</h1>
            <span class="badge-version">v0.5.2</span>
        </div>
        <div class="header-right">
            <span class="last-updated" id="lastUpdated">
                <span class="dot" id="statusDot"></span>
                <span id="lastUpdatedText">väntar...</span>
            </span>
            <button class="refresh-btn" id="refreshBtn">⟳ uppdatera</button>
        </div>
    </header>

    <!-- ===== STATS ROW ===== -->
    <section class="stats-row" id="statsRow">
        <div class="stat-card">
            <div class="stat-label">Totala runs</div>
            <div class="stat-value" id="statTotalRuns">—</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Aktiva runs</div>
            <div class="stat-value" id="statActiveRuns">—</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Medelpoäng</div>
            <div class="stat-value" id="statAvgScore">—<span class="unit"></span></div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Agenter</div>
            <div class="stat-value" id="statAgents">—</div>
            <div class="stat-sub" id="statAgentsSub"></div>
        </div>
    </section>

    <!-- ===== DASHBOARD GRID ===== -->
    <div class="dashboard-grid">

        <!-- ACTIVE RUNS -->
        <section class="panel">
            <div class="panel-header">
                <h2>Aktiva runs</h2>
                <span class="count-badge" id="runsCount">0</span>
            </div>
            <div class="panel-body" id="runsBody">
                <div class="empty-state">
                    <div class="icon">⏳</div>
                    <span>Laddar runs...</span>
                </div>
            </div>
        </section>

        <!-- SCORE HISTORY PER BLUEPRINT -->
        <section class="panel">
            <div class="panel-header">
                <h2>Score-historik per blueprint</h2>
                <span class="count-badge" id="blueprintsCount">0</span>
            </div>
            <div class="panel-body" id="blueprintsBody">
                <div class="empty-state">
                    <div class="icon">📊</div>
                    <span>Laddar blueprints...</span>
                </div>
            </div>
        </section>

        <!-- AGENT STATUS (full width) -->
        <section class="panel panel-full">
            <div class="panel-header">
                <h2>Agent-status</h2>
                <span class="count-badge" id="agentsCount">0</span>
            </div>
            <div class="panel-body" id="agentsBody">
                <div class="empty-state">
                    <div class="icon">🤖</div>
                    <span>Laddar agenter...</span>
                </div>
            </div>
        </section>
    </div>

    <!-- ===== FOOTER ===== -->
    <footer class="footer">
        <span>Forge Command Center · pollar var 5:e sekund</span>
        <span id="footerStatus" class="ok">✓ uppkopplad</span>
    </footer>

    <script>
        (function() {
            'use strict';

            // ===== DOM REFS =====
            const $ = (id) => document.getElementById(id);
            const lastUpdatedText = $('lastUpdatedText');
            const statusDot = $('statusDot');
            const footerStatus = $('footerStatus');

            const statTotalRuns = $('statTotalRuns');
            const statActiveRuns = $('statActiveRuns');
            const statAvgScore = $('statAvgScore');
            const statAgents = $('statAgents');
            const statAgentsSub = $('statAgentsSub');

            const runsBody = $('runsBody');
            const blueprintsBody = $('blueprintsBody');
            const agentsBody = $('agentsBody');

            const runsCount = $('runsCount');
            const blueprintsCount = $('blueprintsCount');
            const agentsCount = $('agentsCount');

            const refreshBtn = $('refreshBtn');

            // ===== STATE =====
            let pollInterval = null;
            let isPolling = true;

            // ===== HELPERS =====
            function formatTime(isoStr) {
                if (!isoStr) return '—';
                try {
                    const d = new Date(isoStr);
                    return d.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                } catch (_) { return isoStr; }
            }

            function statusClass(status) {
                const s = (status || '').toLowerCase();
                if (s === 'running') return 'running';
                if (s === 'eval' || s === 'evaluating') return 'eval';
                if (s === 'improving') return 'improving';
                if (s === 'completed' || s === 'done') return 'completed';
                if (s === 'failed' || s === 'error') return 'failed';
                return 'idle';
            }

            function scoreLevel(score) {
                if (score === null || score === undefined) return '';
                if (score >= 0.7) return 'high';
                if (score >= 0.4) return 'mid';
                return 'low';
            }

            function barLevel(score) {
                if (score === null || score === undefined) return 0;
                return Math.max(4, Math.min(100, Math.round(score * 100)));
            }

            function barClass(score) {
                if (score === null || score === undefined) return 'empty';
                const l = scoreLevel(score);
                if (l === 'high') return 'filled';
                if (l === 'mid') return 'filled mid';
                if (l === 'low') return 'filled low';
                return 'empty';
            }

            // ===== RENDER FUNCTIONS =====

            function renderStats(data) {
                // data from /api/stats
                const stats = data || {};
                const total = stats.total_runs ?? stats.total ?? '—';
                const active = stats.active_runs ?? stats.active ?? '—';
                const avg = stats.average_score ?? stats.avg_score ?? stats.avg ?? null;
                const agents = stats.agents ?? stats.agent_count ?? stats.total_agents ?? '—';
                const agentsActive = stats.active_agents ?? stats.agents_active ?? null;

                statTotalRuns.textContent = total;
                statActiveRuns.textContent = active;

                if (avg !== null && avg !== undefined) {
                    const pct = (typeof avg === 'number' ? avg : parseFloat(avg) || 0);
                    statAvgScore.innerHTML = (pct * 100).toFixed(1) + '<span class="unit">%</span>';
                } else {
                    statAvgScore.textContent = '—';
                }

                statAgents.textContent = agents;
                if (agentsActive !== null) {
                    statAgentsSub.textContent = agentsActive + ' aktiva';
                } else {
                    statAgentsSub.textContent = '';
                }
            }

            function renderRuns(runs) {
                if (!runs || !Array.isArray(runs) || runs.length === 0) {
                    runsBody.innerHTML = `
                        <div class="empty-state">
                            <div class="icon">📭</div>
                            <span>Inga runs än</span>
                        </div>`;
                    runsCount.textContent = '0';
                    return;
                }
                runsCount.textContent = runs.length;
                // Show only active (running/eval/improving) or last 20
                const active = runs.filter(r => {
                    const s = (r.status || '').toLowerCase();
                    return s === 'running' || s === 'eval' || s === 'evaluating' || s === 'improving';
                });
                const display = active.length > 0 ? active : runs.slice(-20);

                let html = `
                    <table class="runs-table">
                        <thead>
                            <tr>
                                <th class="col-id">#</th>
                                <th class="col-name">Namn</th>
                                <th class="col-blueprint">Blueprint</th>
                                <th class="col-status">Status</th>
                                <th class="col-score">Score</th>
                            </tr>
                        </thead>
                        <tbody>`;
                display.forEach(r => {
                    const id = r.id ?? r.run_id ?? '—';
                    const name = r.name || r.run_name || 'Run ' + id;
                    const bp = r.blueprint || r.blueprint_name || r.blueprint_id || '—';
                    const status = r.status || 'unknown';
                    const score = r.score ?? r.result ?? null;
                    const sClass = statusClass(status);
                    const sc = score !== null ? (typeof score === 'number' ? score : parseFloat(score) || 0) : null;
                    const scDisplay = sc !== null ? (sc * 100).toFixed(1) + '%' : '—';
                    const scLvl = scoreLevel(sc);
                    html += `
                        <tr>
                            <td class="col-id">${String(id).substring(0,6)}</td>
                            <td class="col-name">${name}</td>
                            <td class="col-blueprint">${bp}</td>
                            <td class="col-status"><span class="status-badge ${sClass}">${status}</span></td>
                            <td class="col-score"><span class="score-value ${scLvl}">${scDisplay}</span></td>
                        </tr>`;
                });
                html += `</tbody></table>`;
                runsBody.innerHTML = html;
            }

            function renderBlueprints(blueprints) {
                if (!blueprints || !Array.isArray(blueprints) || blueprints.length === 0) {
                    blueprintsBody.innerHTML = `
                        <div class="empty-state">
                            <div class="icon">📊</div>
                            <span>Inga blueprints</span>
                        </div>`;
                    blueprintsCount.textContent = '0';
                    return;
                }
                blueprintsCount.textContent = blueprints.length;
                let html = '<div class="blueprint-list">';
                blueprints.forEach(bp => {
                    const name = bp.name || bp.blueprint || bp.blueprint_name || 'Blueprint';
                    const scores = bp.scores || bp.score_history || bp.recent_scores || [];
                    const avg = bp.average_score ?? bp.avg_score ?? null;
                    const avgDisplay = avg !== null ? (typeof avg === 'number' ? avg : parseFloat(avg) || 0) : null;
                    const avgStr = avgDisplay !== null ? (avgDisplay * 100).toFixed(1) + '%' : '—';

                    html += `
                        <div class="blueprint-item">
                            <div class="blueprint-header">
                                <span class="blueprint-name">${name}</span>
                                <span class="blueprint-avg">snitt <strong>${avgStr}</strong></span>
                            </div>
                            <div class="bar-chart">`;
                    const bars = scores.length > 0 ? scores : [null, null, null, null, null];
                    bars.forEach(sc => {
                        const level = barLevel(sc);
                        const cls = barClass(sc);
                        html += `<div class="bar ${cls}" style="height:${level}%"></div>`;
                    });
                    html += `</div></div>`;
                });
                html += '</div>';
                blueprintsBody.innerHTML = html;
            }

            function renderAgents(agents) {
                if (!agents || !Array.isArray(agents) || agents.length === 0) {
                    agentsBody.innerHTML = `
                        <div class="empty-state">
                            <div class="icon">🤖</div>
                            <span>Inga agenter</span>
                        </div>`;
                    agentsCount.textContent = '0';
                    return;
                }
                agentsCount.textContent = agents.length;
                let html = '<div class="agent-grid">';
                agents.forEach(a => {
                    const name = a.name || a.agent_name || a.id || 'Agent';
                    const status = a.status || 'idle';
                    const runId = a.current_run || a.run_id || a.run || null;
                    const sClass = statusClass(status);
                    html += `
                        <div class="agent-card">
                            <div class="agent-name">${name}</div>
                            <div class="agent-status-row">
                                <span class="agent-status-badge ${sClass}">${status}</span>
                                ${runId ? `<span class="agent-run-id">${String(runId).substring(0,8)}</span>` : ''}
                            </div>
                        </div>`;
                });
                html += '</div>';
                agentsBody.innerHTML = html;
            }

            // ===== FETCH ALL =====
            async function fetchAll() {
                const base = 'http://localhost:8000';
                const results = {};

                const fetchers = [
                    { key: 'stats', url: base + '/api/stats' },
                    { key: 'runs', url: base + '/api/runs' },
                    { key: 'blueprints', url: base + '/api/blueprints' },
                    { key: 'agents', url: base + '/api/status' },
                ];

                const errors = [];

                for (const f of fetchers) {
                    try {
                        const resp = await fetch(f.url, { cache: 'no-store' });
                        if (!resp.ok) throw new Error('HTTP ' + resp.status);
                        results[f.key] = await resp.json();
                    } catch (err) {
                        errors.push(f.key + ': ' + err.message);
                        results[f.key] = null;
                    }
                }

                return { results, errors };
            }

            // ===== UPDATE UI =====
            async function updateDashboard(manual = false) {
                const { results, errors } = await fetchAll();

                const now = new Date();
                lastUpdatedText.textContent = now.toLocaleTimeString('sv-SE', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });

                if (errors.length > 0) {
                    statusDot.className = 'dot offline';
                    footerStatus.className = 'errors';
                    footerStatus.textContent = '⚠ ' + errors.join('; ');
                } else {
                    statusDot.className = 'dot';
                    footerStatus.className = 'ok';
                    footerStatus.textContent = '✓ uppkopplad';
                }

                // Render
                if (results.stats) renderStats(results.stats);
                if (results.runs) renderRuns(results.runs);
                if (results.blueprints) renderBlueprints(results.blueprints);
                if (results.agents) renderAgents(results.agents);

                // Counts fallback
                if (!results.runs) runsCount.textContent = '?';
                if (!results.blueprints) blueprintsCount.textContent = '?';
                if (!results.agents) agentsCount.textContent = '?';
            }

            // ===== POLL =====
            function startPolling() {
                if (pollInterval) clearInterval(pollInterval);
                pollInterval = setInterval(() => {
                    updateDashboard(false);
                }, 5000);
            }

            function stopPolling() {
                if (pollInterval) {
                    clearInterval(pollInterval);
                    pollInterval = null;
                }
            }

            // ===== MANUAL REFRESH =====
            refreshBtn.addEventListener('click', () => {
                updateDashboard(true);
            });

            // ===== INIT =====
            async function init() {
                await updateDashboard(true);
                startPolling();
            }

            // Handle visibility change – pause polling when tab hidden
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    stopPolling();
                } else {
                    updateDashboard(true);
                    startPolling();
                }
            });

            // Cleanup on page unload
            window.addEventListener('beforeunload', () => {
                stopPolling();
            });

            init().catch(err => {
                console.error('Init error:', err);
                footerStatus.textContent = '⚠ init-fel: ' + err.message;
                footerStatus.className = 'errors';
            });

        })();
    </script>

</body>
</html>
```
### Dashboard-översikt

Sidan samlar in data från fyra API-endpoints och visar allt i en kompakt vy:

- **Statistiköversikt** – Fyra kort längst upp visar totalt antal runs, aktiva runs, medelpoäng (i procent) samt antal agenter (med aktiva agenter som delvärde).
- **Aktiva runs** – En tabell som listar pågående eller senaste runs med namn, blueprint, status (färgkodad badge) och score. Tabellen filtrerar automatiskt fram aktiva runs (running/eval/improving) om sådana finns.
- **Score-historik per blueprint** – Varje blueprint visas som ett kort med ett stapeldiagram som representerar senaste scores. Staplarna färgas efter poängnivå (grön > 70 %, gul 40–70 %, röd < 40 %) och medelvärdet visas tydligt.
- **Agent-status** – Ett rutnät med agentkort där varje agent visas med namn, statusbadge (running/eval/improving/idle) och eventuellt aktuellt run-ID.

**Uppdateringslogik:** Sidan pollar alla fyra endpoints var 5:e sekund. En grön prick i headern indikerar aktiv anslutning – vid fel blir den röd och en varning visas i footern. Du kan också klicka på "uppdatera" för en manuell refresh. Pollingen pausas när fliken blir inaktiv för att spara resurser.