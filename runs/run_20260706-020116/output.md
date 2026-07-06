Här är ett komplett, mörkt dashboard för Forge Command Center som pollar ditt API var 5:e sekund.
```html
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Forge Command Center</title>
    <style>
        /* ───────── Reset & Base ───────── */
        *,
        *::before,
        *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background: #0b0e14;
            color: #d4d9e3;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            font-size: 14px;
            line-height: 1.5;
            min-height: 100vh;
            padding: 24px 32px;
        }

        /* ───────── Scrollbar ───────── */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #131820;
        }
        ::-webkit-scrollbar-thumb {
            background: #2a3342;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #3a465a;
        }

        /* ───────── Layout ───────── */
        .app {
            max-width: 1440px;
            margin: 0 auto;
        }

        /* header */
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 28px;
            padding-bottom: 16px;
            border-bottom: 1px solid #1e2632;
        }

        .header h1 {
            font-size: 22px;
            font-weight: 600;
            letter-spacing: 0.3px;
            color: #f0f4fc;
        }

        .header h1 span {
            color: #6c8cff;
            font-weight: 500;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 24px;
        }

        .last-updated {
            font-size: 12px;
            color: #6b7a93;
        }

        .last-updated strong {
            color: #b0c0d8;
            font-weight: 500;
        }

        .poll-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #2a6e3b;
            box-shadow: 0 0 8px rgba(42, 110, 59, 0.5);
            transition: background 0.3s;
        }

        .poll-indicator.idle {
            background: #6b7a93;
            box-shadow: none;
        }

        /* ───────── Stats Bar ───────── */
        .stats-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin-bottom: 28px;
        }

        .stat-card {
            background: #111820;
            border: 1px solid #1e2632;
            border-radius: 10px;
            padding: 16px 20px;
            transition: border-color 0.2s;
        }

        .stat-card:hover {
            border-color: #2a3342;
        }

        .stat-card .label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: #6b7a93;
            font-weight: 500;
        }

        .stat-card .value {
            font-size: 28px;
            font-weight: 600;
            color: #f0f4fc;
            margin-top: 4px;
            line-height: 1.2;
        }

        .stat-card .sub {
            font-size: 12px;
            color: #6b7a93;
            margin-top: 2px;
        }

        /* ───────── Grid ───────── */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }

        .card {
            background: #111820;
            border: 1px solid #1e2632;
            border-radius: 12px;
            padding: 20px 24px;
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }

        .card-header h2 {
            font-size: 15px;
            font-weight: 600;
            color: #e8edf6;
            letter-spacing: 0.2px;
        }

        .card-header .badge {
            font-size: 11px;
            padding: 2px 10px;
            border-radius: 20px;
            background: #1e2632;
            color: #8b9bb5;
            font-weight: 500;
        }

        /* ───────── Runs Table ───────── */
        .runs-table {
            width: 100%;
            border-collapse: collapse;
        }

        .runs-table th {
            text-align: left;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #6b7a93;
            font-weight: 500;
            padding: 0 0 8px 0;
            border-bottom: 1px solid #1e2632;
        }

        .runs-table td {
            padding: 10px 0;
            border-bottom: 1px solid #181f2a;
            font-size: 13px;
            vertical-align: middle;
        }

        .runs-table tr:last-child td {
            border-bottom: none;
        }

        .runs-table .run-id {
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 12px;
            color: #8b9bb5;
        }

        .status-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.2px;
            white-space: nowrap;
        }

        .status-badge.running {
            background: #1a3a4a;
            color: #5fc3e8;
        }
        .status-badge.completed {
            background: #1a3a2a;
            color: #5ae08a;
        }
        .status-badge.failed {
            background: #3a1a1a;
            color: #f06060;
        }
        .status-badge.pending {
            background: #2a2a1a;
            color: #d4c04a;
        }
        .status-badge.eval {
            background: #2a1a3a;
            color: #b080e8;
        }
        .status-badge.improving {
            background: #1a2a3a;
            color: #70b8f0;
        }

        .score-cell {
            font-weight: 500;
            color: #e8edf6;
        }

        .score-cell.high {
            color: #5ae08a;
        }
        .score-cell.mid {
            color: #d4c04a;
        }
        .score-cell.low {
            color: #f06060;
        }

        /* ───────── Blueprint Scores ───────── */
        .blueprint-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .blueprint-item {
            background: #0f1520;
            border-radius: 8px;
            padding: 12px 16px;
            border: 1px solid #1a212e;
        }

        .blueprint-item .bp-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 6px;
        }

        .blueprint-item .bp-name {
            font-weight: 500;
            color: #e0e6f0;
            font-size: 13px;
        }

        .blueprint-item .bp-score {
            font-weight: 600;
            font-size: 15px;
        }

        .blueprint-item .bp-score.high {
            color: #5ae08a;
        }
        .blueprint-item .bp-score.mid {
            color: #d4c04a;
        }
        .blueprint-item .bp-score.low {
            color: #f06060;
        }

        .bp-bar-track {
            width: 100%;
            height: 4px;
            background: #1a212e;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 4px;
        }

        .bp-bar-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.6s ease;
            background: #4a6cf7;
        }

        .bp-bar-fill.high {
            background: #2a8e4a;
        }
        .bp-bar-fill.mid {
            background: #b8a030;
        }
        .bp-bar-fill.low {
            background: #b84242;
        }

        .bp-history {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 6px;
            font-size: 11px;
            color: #6b7a93;
        }

        .bp-history .dot {
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
        }

        /* ───────── Agent Status ───────── */
        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
            gap: 10px;
        }

        .agent-card {
            background: #0f1520;
            border: 1px solid #1a212e;
            border-radius: 10px;
            padding: 14px 16px;
            text-align: center;
            transition: border-color 0.2s;
        }

        .agent-card:hover {
            border-color: #2a3342;
        }

        .agent-card .agent-name {
            font-size: 13px;
            font-weight: 500;
            color: #d0d8e6;
            margin-bottom: 6px;
        }

        .agent-card .agent-status {
            display: inline-block;
            padding: 2px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 500;
        }

        .agent-card .agent-status.running {
            background: #1a3a4a;
            color: #5fc3e8;
        }
        .agent-card .agent-status.eval {
            background: #2a1a3a;
            color: #b080e8;
        }
        .agent-card .agent-status.improving {
            background: #1a2a3a;
            color: #70b8f0;
        }
        .agent-card .agent-status.idle {
            background: #1a1a22;
            color: #6b7a93;
        }

        .agent-card .agent-score {
            font-size: 20px;
            font-weight: 600;
            color: #f0f4fc;
            margin-top: 4px;
        }

        .agent-card .agent-score-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            color: #6b7a93;
        }

        /* ───────── Full-width card ───────── */
        .card-full {
            grid-column: 1 / -1;
        }

        /* ───────── Empty / Error states ───────── */
        .empty-state {
            text-align: center;
            padding: 32px 16px;
            color: #6b7a93;
            font-size: 13px;
        }

        .error-state {
            text-align: center;
            padding: 16px;
            color: #f06060;
            font-size: 13px;
            background: #1a0e0e;
            border-radius: 8px;
            border: 1px solid #3a1a1a;
        }

        /* ───────── Responsive ───────── */
        @media (max-width: 900px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }

            body {
                padding: 16px;
            }

            .header {
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }

            .header-right {
                width: 100%;
                justify-content: space-between;
            }

            .stats-bar {
                grid-template-columns: repeat(2, 1fr);
            }

            .agent-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 480px) {
            .stats-bar {
                grid-template-columns: 1fr;
            }

            .agent-grid {
                grid-template-columns: 1fr;
            }

            .runs-table th:nth-child(3),
            .runs-table td:nth-child(3) {
                display: none;
            }
        }

        /* ───────── Utilities ───────── */
        .mt-8 {
            margin-top: 8px;
        }
        .text-muted {
            color: #6b7a93;
        }
        .text-center {
            text-align: center;
        }
        .flex {
            display: flex;
        }
        .flex-between {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .gap-8 {
            gap: 8px;
        }
        .gap-12 {
            gap: 12px;
        }
    </style>
</head>
<body>

    <div class="app" id="app">
        <!-- Header -->
        <header class="header">
            <h1>⚙️ Forge <span>Command Center</span></h1>
            <div class="header-right">
                <div class="last-updated">
                    Senast uppdaterad: <strong id="lastUpdated">—</strong>
                </div>
                <div class="poll-indicator" id="pollIndicator"></div>
            </div>
        </header>

        <!-- Stats -->
        <section class="stats-bar" id="statsBar">
            <div class="stat-card">
                <div class="label">Totala runs</div>
                <div class="value" id="statTotalRuns">—</div>
            </div>
            <div class="stat-card">
                <div class="label">Aktiva runs</div>
                <div class="value" id="statActiveRuns">—</div>
            </div>
            <div class="stat-card">
                <div class="label">Genomsnittlig score</div>
                <div class="value" id="statAvgScore">—</div>
                <div class="sub" id="statAvgScoreSub"></div>
            </div>
            <div class="stat-card">
                <div class="label">Agenter online</div>
                <div class="value" id="statAgentsOnline">—</div>
                <div class="sub" id="statAgentsSub"></div>
            </div>
        </section>

        <!-- Grid -->
        <div class="dashboard-grid">
            <!-- Aktiva runs -->
            <div class="card">
                <div class="card-header">
                    <h2>Aktiva runs</h2>
                    <span class="badge" id="runsBadge">0</span>
                </div>
                <div id="runsContainer">
                    <div class="empty-state">Laddar runs...</div>
                </div>
            </div>

            <!-- Agent status -->
            <div class="card">
                <div class="card-header">
                    <h2>Agentstatus</h2>
                    <span class="badge" id="agentsBadge">0</span>
                </div>
                <div id="agentsContainer">
                    <div class="empty-state">Laddar agenter...</div>
                </div>
            </div>

            <!-- Score-historik per blueprint (full width) -->
            <div class="card card-full">
                <div class="card-header">
                    <h2>Score-historik per blueprint</h2>
                    <span class="badge" id="blueprintsBadge">0</span>
                </div>
                <div id="blueprintsContainer">
                    <div class="empty-state">Laddar blueprints...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        (function() {
            'use strict';

            // ─── DOM refs ────────────────────────────────────────────
            const $ = id => document.getElementById(id);
            const lastUpdated = $('lastUpdated');
            const pollIndicator = $('pollIndicator');

            const statTotalRuns = $('statTotalRuns');
            const statActiveRuns = $('statActiveRuns');
            const statAvgScore = $('statAvgScore');
            const statAvgScoreSub = $('statAvgScoreSub');
            const statAgentsOnline = $('statAgentsOnline');
            const statAgentsSub = $('statAgentsSub');

            const runsContainer = $('runsContainer');
            const agentsContainer = $('agentsContainer');
            const blueprintsContainer = $('blueprintsContainer');

            const runsBadge = $('runsBadge');
            const agentsBadge = $('agentsBadge');
            const blueprintsBadge = $('blueprintsBadge');

            // ─── Helpers ────────────────────────────────────────────
            function formatTime(isoString) {
                if (!isoString) return '—';
                const d = new Date(isoString);
                return d.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            }

            function nowFormatted() {
                return new Date().toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            }

            function statusClass(status) {
                const s = (status || '').toLowerCase();
                if (s.includes('run') || s === 'active') return 'running';
                if (s.includes('complete') || s === 'done') return 'completed';
                if (s.includes('fail') || s === 'error') return 'failed';
                if (s.includes('pend') || s === 'waiting') return 'pending';
                if (s.includes('eval')) return 'eval';
                if (s.includes('improv')) return 'improving';
                if (s === 'idle') return 'idle';
                return 'pending';
            }

            function scoreLevel(score) {
                if (score === null || score === undefined) return 'mid';
                if (score >= 80) return 'high';
                if (score >= 50) return 'mid';
                return 'low';
            }

            function scoreColor(score) {
                const level = scoreLevel(score);
                if (level === 'high') return '#5ae08a';
                if (level === 'mid') return '#d4c04a';
                return '#f06060';
            }

            // ─── Render functions ───────────────────────────────────

            function renderRuns(runs) {
                if (!runs || runs.length === 0) {
                    runsContainer.innerHTML = `<div class="empty-state">Inga aktiva runs just nu.</div>`;
                    runsBadge.textContent = '0';
                    return;
                }

                const active = runs.filter(r => {
                    const s = (r.status || '').toLowerCase();
                    return s === 'running' || s === 'active' || s === 'pending' || s === 'eval' || s === 'improving';
                });

                runsBadge.textContent = active.length;

                let html = `
                    <table class="runs-table">
                        <thead>
                            <tr>
                                <th>Run ID</th>
                                <th>Blueprint</th>
                                <th>Status</th>
                                <th>Score</th>
                                <th>Uppdaterad</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                runs.forEach(run => {
                    const status = run.status || 'unknown';
                    const sClass = statusClass(status);
                    const score = run.score !== null && run.score !== undefined ? run.score : '—';
                    const scoreVal = typeof score === 'number' ? score : null;
                    const sLevel = scoreLevel(scoreVal);

                    html += `
                        <tr>
                            <td><span class="run-id">${run.id ? run.id.slice(0, 12) : '—'}</span></td>
                            <td>${run.blueprint || '—'}</td>
                            <td><span class="status-badge ${sClass}">${status}</span></td>
                            <td class="score-cell ${sLevel}">${score !== '—' ? score : '—'}</td>
                            <td class="text-muted">${formatTime(run.updated_at)}</td>
                        </tr>
                    `;
                });

                html += `</tbody></table>`;
                runsContainer.innerHTML = html;
            }

            function renderAgents(agents) {
                if (!agents || agents.length === 0) {
                    agentsContainer.innerHTML = `<div class="empty-state">Inga agenter hittades.</div>`;
                    agentsBadge.textContent = '0';
                    statAgentsOnline.textContent = '—';
                    statAgentsSub.textContent = '';
                    return;
                }

                agentsBadge.textContent = agents.length;

                const online = agents.filter(a => {
                    const s = (a.status || '').toLowerCase();
                    return s !== 'idle' && s !== 'offline';
                });
                statAgentsOnline.textContent = online.length;
                statAgentsSub.textContent = `av ${agents.length} agenter`;

                let html = `<div class="agent-grid">`;

                agents.forEach(agent => {
                    const status = agent.status || 'idle';
                    const sClass = statusClass(status);
                    const score = agent.score !== null && agent.score !== undefined ? agent.score : '—';
                    const scoreVal = typeof score === 'number' ? score : null;
                    const sLevel = scoreLevel(scoreVal);

                    html += `
                        <div class="agent-card">
                            <div class="agent-name">${agent.name || agent.id || 'Okänd'}</div>
                            <div><span class="agent-status ${sClass}">${status}</span></div>
                            <div class="agent-score" style="color:${scoreColor(scoreVal)}">${score !== '—' ? score : '—'}</div>
                            <div class="agent-score-label">Score</div>
                        </div>
                    `;
                });

                html += `</div>`;
                agentsContainer.innerHTML = html;
            }

            function renderBlueprints(blueprints) {
                if (!blueprints || blueprints.length === 0) {
                    blueprintsContainer.innerHTML = `<div class="empty-state">Inga blueprints tillgängliga.</div>`;
                    blueprintsBadge.textContent = '0';
                    return;
                }

                blueprintsBadge.textContent = blueprints.length;

                let html = `<div class="blueprint-list">`;

                blueprints.forEach(bp => {
                    const score = bp.average_score !== null && bp.average_score !== undefined ? bp.average_score :
                        bp.score !== null && bp.score !== undefined ? bp.score : null;
                    const scoreVal = typeof score === 'number' ? score : null;
                    const sLevel = scoreLevel(scoreVal);
                    const displayScore = scoreVal !== null ? scoreVal.toFixed(1) : '—';
                    const pct = scoreVal !== null ? Math.min(Math.max(scoreVal, 0), 100) : 0;
                    const history = bp.history || bp.scores || [];

                    html += `
                        <div class="blueprint-item">
                            <div class="bp-header">
                                <span class="bp-name">${bp.name || bp.blueprint || 'Okänd'}</span>
                                <span class="bp-score ${sLevel}">${displayScore}</span>
                            </div>
                            <div class="bp-bar-track">
                                <div class="bp-bar-fill ${sLevel}" style="width:${pct}%"></div>
                            </div>
                            <div class="bp-history">
                                <span>${history.length} mätpunkter</span>
                                ${
                                    history.slice(-5).map(h => {
                                        const v = typeof h === 'number' ? h : (h.score || h.value || 0);
                                        const l = scoreLevel(v);
                                        return `<span class="dot" style="background:${scoreColor(v)}" title="${v}"></span>`;
                                    }).join('')
                                }
                                <span style="margin-left:auto;color:#6b7a93;">senaste 5</span>
                            </div>
                        </div>
                    `;
                });

                html += `</div>`;
                blueprintsContainer.innerHTML = html;
            }

            function renderStats(stats) {
                if (!stats) return;

                if (stats.total_runs !== undefined) statTotalRuns.textContent = stats.total_runs;
                if (stats.active_runs !== undefined) statActiveRuns.textContent = stats.active_runs;
                if (stats.average_score !== undefined) {
                    const avg = typeof stats.average_score === 'number' ? stats.average_score.toFixed(1) : stats.average_score;
                    statAvgScore.textContent = avg;
                    statAvgScoreSub.textContent = `över alla blueprints`;
                }
                if (stats.agents_online !== undefined) {
                    statAgentsOnline.textContent = stats.agents_online;
                    statAgentsSub.textContent = stats.agents_total ? `av ${stats.agents_total} agenter` : '';
                }
            }

            // ─── Main fetch ─────────────────────────────────────────

            const BASE = 'http://localhost:8000';

            async function fetchAll() {
                // Tänd indikator
                pollIndicator.classList.remove('idle');

                try {
                    const [runsRes, blueprintsRes, statsRes, statusRes] = await Promise.all([
                        fetch(`${BASE}/api/runs`).catch(() => null),
                        fetch(`${BASE}/api/blueprints`).catch(() => null),
                        fetch(`${BASE}/api/stats`).catch(() => null),
                        fetch(`${BASE}/api/status`).catch(() => null),
                    ]);

                    // Runs
                    if (runsRes && runsRes.ok) {
                        const data = await runsRes.json();
                        renderRuns(Array.isArray(data) ? data : data.runs || []);
                    } else {
                        runsContainer.innerHTML = `<div class="error-state">Kunde inte ladda runs (${runsRes ? runsRes.status : 'nätverksfel'})</div>`;
                        runsBadge.textContent = '!';
                    }

                    // Blueprints
                    if (blueprintsRes && blueprintsRes.ok) {
                        const data = await blueprintsRes.json();
                        renderBlueprints(Array.isArray(data) ? data : data.blueprints || []);
                    } else {
                        blueprintsContainer.innerHTML =
                        `<div class="error-state">Kunde inte ladda blueprints (${blueprintsRes ? blueprintsRes.status : 'nätverksfel'})</div>`;
                        blueprintsBadge.textContent = '!';
                    }

                    // Stats
                    if (statsRes && statsRes.ok) {
                        const data = await statsRes.json();
                        renderStats(data);
                    }

                    // Status (agents)
                    if (statusRes && statusRes.ok) {
                        const data = await statusRes.json();
                        const agents = Array.isArray(data) ? data : data.agents || data.status || [];
                        renderAgents(agents);
                    } else {
                        agentsContainer.innerHTML =
                        `<div class="error-state">Kunde inte ladda status (${statusRes ? statusRes.status : 'nätverksfel'})</div>`;
                        agentsBadge.textContent = '!';
                    }

                    // Uppdatera tidsstämpel
                    lastUpdated.textContent = nowFormatted();

                } catch (err) {
                    const errMsg = `Nätverksfel: ${err.message || 'okänt fel'}`;
                    if (!runsContainer.querySelector('.error-state')) {
                        runsContainer.innerHTML = `<div class="error-state">${errMsg}</div>`;
                    }
                    if (!agentsContainer.querySelector('.error-state')) {
                        agentsContainer.innerHTML = `<div class="error-state">${errMsg}</div>`;
                    }
                    if (!blueprintsContainer.querySelector('.error-state')) {
                        blueprintsContainer.innerHTML = `<div class="error-state">${errMsg}</div>`;
                    }
                    console.error('Forge Dashboard fetch error:', err);
                } finally {
                    // Släck indikator efter kort dröjsmål
                    setTimeout(() => pollIndicator.classList.add('idle'), 400);
                }
            }

            // ─── Polling ────────────────────────────────────────────

            let pollInterval = null;

            function startPolling(intervalMs = 5000) {
                // Omedelbart första anrop
                fetchAll();

                if (pollInterval) clearInterval(pollInterval);
                pollInterval = setInterval(fetchAll, intervalMs);
            }

            function stopPolling() {
                if (pollInterval) {
                    clearInterval(pollInterval);
                    pollInterval = null;
                }
                pollIndicator.classList.add('idle');
            }

            // ─── Init ───────────────────────────────────────────────

            // Starta polling när sidan laddats
            document.addEventListener('DOMContentLoaded', () => {
                startPolling(5000);
            });

            // Stoppa polling om sidan blir osynlig (sparar resurser)
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    stopPolling();
                } else {
                    startPolling(5000);
                }
            });

            // Exponera för debugging
            window.__forge = {
                fetchAll,
                startPolling,
                stopPolling,
                BASE
            };

        })();
    </script>

</body>
</html>
```
### Dashboard-översikt

Sidan ger dig en komplett överblick över dina pipelines i en mörk, avskalad design.

*   **Topplistan (Stats Bar):** Visar aggregerad data – totala runs, aktiva runs, genomsnittlig score och antal agenter online. Siffrorna uppdateras automatiskt.
*   **Aktiva runs-tabell:** Listar varje run med ID, blueprint, status (färgkodad), score och senaste uppdatering. Tabellen visar bara de mest relevanta kolumnerna för snabb överblick.
*   **Agentstatus (kort):** Varje agent visas som ett eget kort med status (running/eval/improving/idle) och aktuell score. Färgerna hjälper dig att snabbt identifiera agenternas tillstånd.
*   **Score-historik per blueprint:** Varje blueprint får ett eget kort med genomsnittlig score, en färgad progress-bar och en visuell historik över de senaste 5 mätpunkterna. Detta ger dig en snabb bild av trender över tid.

All data pollas var 5:e sekund från ditt lokala API, och en grön indikator i hörnet blinkar till vid varje uppdatering.