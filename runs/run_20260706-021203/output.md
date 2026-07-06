Här är ett komplett mörkt dashboard som pollar ditt API var 5:e sekund och visar all förfrågad data i en enda HTML-fil.
```html
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Forge Command Center</title>
    <style>
        *,
        *::before,
        *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        :root {
            --bg-primary: #0d0f12;
            --bg-secondary: #15181d;
            --bg-card: #1a1e25;
            --bg-card-hover: #212730;
            --border: #2a2f3a;
            --text-primary: #e8edf5;
            --text-secondary: #8b95a8;
            --text-muted: #5a6478;
            --accent-blue: #4f8cf7;
            --accent-green: #34d399;
            --accent-yellow: #fbbf24;
            --accent-red: #f87171;
            --accent-purple: #a78bfa;
            --accent-cyan: #22d3ee;
            --radius: 10px;
            --radius-sm: 6px;
            --shadow: 0 2px 12px rgba(0, 0, 0, 0.5);
            --font: 'Segoe UI', system-ui, -apple-system, sans-serif;
        }

        html {
            font-size: 15px;
            scroll-behavior: smooth;
        }

        body {
            font-family: var(--font);
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 24px 32px;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        /* ---------- Header ---------- */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-left h1 {
            font-size: 1.6rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .badge {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 4px 14px;
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--text-secondary);
            letter-spacing: 0.3px;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 20px;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .status-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--accent-green);
            margin-right: 6px;
            animation: pulse-dot 2s ease-in-out infinite;
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

        .status-dot.warn {
            background: var(--accent-yellow);
        }
        .status-dot.error {
            background: var(--accent-red);
        }

        /* ---------- Stats row ---------- */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
        }

        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 16px 20px;
            display: flex;
            flex-direction: column;
            gap: 4px;
            transition: border-color 0.2s;
        }

        .stat-card:hover {
            border-color: #3a4150;
        }

        .stat-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            font-weight: 500;
        }

        .stat-value {
            font-size: 1.8rem;
            font-weight: 600;
            line-height: 1.2;
            color: var(--text-primary);
        }

        .stat-sub {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        /* ---------- Main grid ---------- */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            flex: 1;
        }

        @media (max-width: 1100px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            body {
                padding: 16px;
            }
        }

        .panel {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            min-height: 280px;
        }

        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .panel-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .panel-title .count {
            font-size: 0.75rem;
            font-weight: 400;
            background: var(--bg-card);
            border-radius: 12px;
            padding: 2px 10px;
            color: var(--text-secondary);
        }

        .panel-body {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-height: 0;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }

        .panel-body::-webkit-scrollbar {
            width: 4px;
        }
        .panel-body::-webkit-scrollbar-track {
            background: transparent;
        }
        .panel-body::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }

        /* ---------- Run cards ---------- */
        .run-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 12px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            transition: border-color 0.2s;
        }

        .run-card:hover {
            border-color: #3a4150;
        }

        .run-info {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }

        .run-id {
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 0.8rem;
            color: var(--text-secondary);
            background: var(--bg-secondary);
            padding: 2px 8px;
            border-radius: 4px;
        }

        .run-blueprint {
            font-weight: 500;
            font-size: 0.9rem;
            color: var(--accent-cyan);
        }

        .run-score {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--accent-green);
        }

        .run-score.low {
            color: var(--accent-red);
        }
        .run-score.mid {
            color: var(--accent-yellow);
        }

        .status-tag {
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            padding: 3px 10px;
            border-radius: 12px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            color: var(--text-secondary);
        }

        .status-tag.running {
            border-color: var(--accent-blue);
            color: var(--accent-blue);
        }
        .status-tag.eval {
            border-color: var(--accent-purple);
            color: var(--accent-purple);
        }
        .status-tag.improving {
            border-color: var(--accent-yellow);
            color: var(--accent-yellow);
        }
        .status-tag.completed {
            border-color: var(--accent-green);
            color: var(--accent-green);
        }
        .status-tag.failed {
            border-color: var(--accent-red);
            color: var(--accent-red);
        }

        .run-progress {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        .progress-bar {
            width: 60px;
            height: 4px;
            background: var(--bg-primary);
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: var(--accent-blue);
            border-radius: 4px;
            transition: width 0.5s ease;
        }

        /* ---------- Blueprint score history ---------- */
        .blueprint-row {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 12px 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            transition: border-color 0.2s;
        }

        .blueprint-row:hover {
            border-color: #3a4150;
        }

        .blueprint-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 6px;
        }

        .blueprint-name {
            font-weight: 500;
            font-size: 0.9rem;
            color: var(--accent-purple);
        }

        .blueprint-stats {
            font-size: 0.75rem;
            color: var(--text-muted);
            display: flex;
            gap: 12px;
        }

        .blueprint-scores {
            display: flex;
            align-items: flex-end;
            gap: 4px;
            height: 36px;
            padding-top: 4px;
        }

        .score-bar {
            width: 16px;
            border-radius: 3px 3px 0 0;
            background: var(--accent-blue);
            min-height: 4px;
            transition: height 0.4s ease;
            opacity: 0.8;
        }

        .score-bar:hover {
            opacity: 1;
        }

        .score-bar.high {
            background: var(--accent-green);
        }
        .score-bar.mid {
            background: var(--accent-yellow);
        }
        .score-bar.low {
            background: var(--accent-red);
        }

        /* ---------- Agent status ---------- */
        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 8px;
        }

        .agent-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 4px;
            transition: border-color 0.2s;
        }

        .agent-card:hover {
            border-color: #3a4150;
        }

        .agent-name {
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--text-primary);
        }

        .agent-status {
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            padding: 2px 8px;
            border-radius: 8px;
            align-self: flex-start;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            color: var(--text-secondary);
        }

        .agent-status.running {
            border-color: var(--accent-blue);
            color: var(--accent-blue);
        }
        .agent-status.eval {
            border-color: var(--accent-purple);
            color: var(--accent-purple);
        }
        .agent-status.improving {
            border-color: var(--accent-yellow);
            color: var(--accent-yellow);
        }
        .agent-status.idle {
            border-color: var(--text-muted);
            color: var(--text-muted);
        }

        .agent-meta {
            font-size: 0.7rem;
            color: var(--text-muted);
        }

        /* ---------- Empty / loading ---------- */
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 32px 16px;
            color: var(--text-muted);
            font-size: 0.9rem;
            gap: 6px;
            text-align: center;
        }

        .empty-state .icon {
            font-size: 2rem;
            opacity: 0.3;
        }

        .loading-dots::after {
            content: '';
            animation: dots 1.2s steps(3, end) infinite;
        }

        @keyframes dots {
            0% {
                content: '';
            }
            33% {
                content: '.';
            }
            66% {
                content: '..';
            }
            100% {
                content: '...';
            }
        }

        /* ---------- Footer ---------- */
        .footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.7rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border);
            padding-top: 16px;
            margin-top: 4px;
        }

        .footer .last-updated {
            font-family: 'SF Mono', 'Fira Code', monospace;
        }

        .refresh-btn {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            color: var(--text-secondary);
            padding: 6px 14px;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s;
            font-family: var(--font);
        }

        .refresh-btn:hover {
            background: var(--bg-card-hover);
            border-color: #3a4150;
            color: var(--text-primary);
        }

        .refresh-btn:active {
            transform: scale(0.96);
        }

        /* ---------- Responsive fine-tune ---------- */
        @media (max-width: 600px) {
            .header-left h1 {
                font-size: 1.2rem;
            }
            .stat-value {
                font-size: 1.4rem;
            }
            .run-card {
                flex-direction: column;
                align-items: stretch;
            }
            .run-info {
                justify-content: space-between;
            }
            .blueprint-scores {
                height: 28px;
            }
            .score-bar {
                width: 12px;
            }
            .agent-grid {
                grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
            }
        }
    </style>
</head>
<body>

    <!-- HEADER -->
    <header class="header">
        <div class="header-left">
            <h1>⚙ Forge Command Center</h1>
            <span class="badge">v1.0</span>
        </div>
        <div class="header-right">
            <span><span class="status-dot" id="connectionDot"></span><span id="connectionStatus">Ansluter...</span></span>
            <span id="runCountBadge">0 runs</span>
        </div>
    </header>

    <!-- STATS -->
    <section class="stats-grid" id="statsGrid">
        <div class="stat-card">
            <span class="stat-label">Totalt runs</span>
            <span class="stat-value" id="statTotalRuns">—</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">Aktiva runs</span>
            <span class="stat-value" id="statActiveRuns">—</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">Genomsnittlig score</span>
            <span class="stat-value" id="statAvgScore">—</span>
            <span class="stat-sub" id="statAvgSub"></span>
        </div>
        <div class="stat-card">
            <span class="stat-label">Agenter</span>
            <span class="stat-value" id="statAgents">—</span>
            <span class="stat-sub" id="statAgentsSub"></span>
        </div>
        <div class="stat-card">
            <span class="stat-label">Blueprints</span>
            <span class="stat-value" id="statBlueprints">—</span>
        </div>
    </section>

    <!-- MAIN GRID -->
    <div class="dashboard-grid">

        <!-- Active Runs -->
        <section class="panel" id="runsPanel">
            <div class="panel-header">
                <span class="panel-title">
                    Aktiva runs
                    <span class="count" id="runsCount">0</span>
                </span>
                <span style="font-size:0.7rem;color:var(--text-muted)">senaste först</span>
            </div>
            <div class="panel-body" id="runsList">
                <div class="empty-state">
                    <span class="icon">◌</span>
                    <span>Laddar runs...</span>
                </div>
            </div>
        </section>

        <!-- Score History per Blueprint -->
        <section class="panel" id="blueprintsPanel">
            <div class="panel-header">
                <span class="panel-title">
                    Score-historik per blueprint
                    <span class="count" id="blueprintsCount">0</span>
                </span>
            </div>
            <div class="panel-body" id="blueprintsList">
                <div class="empty-state">
                    <span class="icon">◌</span>
                    <span>Laddar blueprints...</span>
                </div>
            </div>
        </section>

        <!-- Agent Status -->
        <section class="panel" id="agentsPanel" style="grid-column: 1 / -1;">
            <div class="panel-header">
                <span class="panel-title">
                    Agent-status
                    <span class="count" id="agentsCount">0</span>
                </span>
                <span style="font-size:0.7rem;color:var(--text-muted)">running · eval · improving</span>
            </div>
            <div class="panel-body" id="agentsList">
                <div class="empty-state">
                    <span class="icon">◌</span>
                    <span>Laddar agenter...</span>
                </div>
            </div>
        </section>

    </div>

    <!-- FOOTER -->
    <footer class="footer">
        <span class="last-updated" id="lastUpdated">Senast uppdaterad: —</span>
        <button class="refresh-btn" id="refreshBtn">↻ Uppdatera nu</button>
    </footer>

    <script>
        (function() {
            'use strict';

            const API_BASE = 'http://localhost:8000';
            const POLL_INTERVAL = 5000;

            // DOM refs
            const $ = (id) => document.getElementById(id);
            const runsList = $('runsList');
            const runsCount = $('runsCount');
            const blueprintsList = $('blueprintsList');
            const blueprintsCount = $('blueprintsCount');
            const agentsList = $('agentsList');
            const agentsCount = $('agentsCount');
            const lastUpdated = $('lastUpdated');
            const connectionDot = $('connectionDot');
            const connectionStatus = $('connectionStatus');
            const runCountBadge = $('runCountBadge');
            const refreshBtn = $('refreshBtn');

            // Stat elements
            const statTotalRuns = $('statTotalRuns');
            const statActiveRuns = $('statActiveRuns');
            const statAvgScore = $('statAvgScore');
            const statAvgSub = $('statAvgSub');
            const statAgents = $('statAgents');
            const statAgentsSub = $('statAgentsSub');
            const statBlueprints = $('statBlueprints');

            let pollTimer = null;
            let isPolling = false;

            // ---------- helpers ----------
            function formatTime(iso) {
                if (!iso) return '—';
                const d = new Date(iso);
                return d.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            }

            function timeAgo(iso) {
                if (!iso) return '—';
                const diff = Date.now() - new Date(iso).getTime();
                const sec = Math.floor(diff / 1000);
                if (sec < 10) return 'precis nu';
                if (sec < 60) return sec + 's sedan';
                const min = Math.floor(sec / 60);
                if (min < 60) return min + 'm sedan';
                return formatTime(iso);
            }

            function scoreClass(score) {
                if (score == null) return '';
                if (score >= 0.8) return 'high';
                if (score >= 0.5) return 'mid';
                return 'low';
            }

            function statusClass(status) {
                if (!status) return '';
                const s = status.toLowerCase();
                if (s.includes('run')) return 'running';
                if (s.includes('eval')) return 'eval';
                if (s.includes('improve')) return 'improving';
                if (s.includes('complete') || s.includes('done')) return 'completed';
                if (s.includes('fail') || s.includes('error')) return 'failed';
                return '';
            }

            function statusTag(status) {
                const cls = statusClass(status);
                const label = status ? status : 'unknown';
                return `<span class="status-tag ${cls}">${label}</span>`;
            }

            // ---------- fetch with timeout ----------
            async function fetchJSON(url, timeout = 4000) {
                const controller = new AbortController();
                const id = setTimeout(() => controller.abort(), timeout);
                try {
                    const res = await fetch(url, { signal: controller.signal });
                    clearTimeout(id);
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    return await res.json();
                } catch (err) {
                    clearTimeout(id);
                    throw err;
                }
            }

            // ---------- render functions ----------
            function renderRuns(runs) {
                if (!runs || runs.length === 0) {
                    runsList.innerHTML = `<div class="empty-state"><span class="icon">◌</span><span>Inga aktiva runs</span></div>`;
                    runsCount.textContent = '0';
                    return;
                }
                runsCount.textContent = runs.length;
                runsList.innerHTML = runs.map(r => {
                    const score = r.score != null ? r.score : r.average_score;
                    const scoreVal = score != null ? score.toFixed(2) : '—';
                    const sClass = scoreClass(score);
                    const progress = r.progress != null ? r.progress : (r.steps ? Math.min(100, Math.round((r.steps
                        .completed || 0) / (r.steps.total || 1) * 100)) : null);
                    return `
                        <div class="run-card">
                            <div class="run-info">
                                <span class="run-id">${r.id ? r.id.slice(0, 8) : '—'}</span>
                                <span class="run-blueprint">${r.blueprint_name || r.blueprint || '—'}</span>
                                <span class="run-score ${sClass}">${scoreVal}</span>
                                ${statusTag(r.status)}
                            </div>
                            <div class="run-progress">
                                ${progress !== null ? `<span>${progress}%</span><div class="progress-bar"><div class="progress-fill" style="width:${progress}%"></div></div>` : ''}
                                <span>${timeAgo(r.updated_at || r.created_at || r.timestamp)}</span>
                            </div>
                        </div>
                    `;
                }).join('');
            }

            function renderBlueprints(blueprints) {
                if (!blueprints || blueprints.length === 0) {
                    blueprintsList.innerHTML =
                    `<div class="empty-state"><span class="icon">◌</span><span>Inga blueprints</span></div>`;
                    blueprintsCount.textContent = '0';
                    return;
                }
                blueprintsCount.textContent = blueprints.length;
                blueprintsList.innerHTML = blueprints.map(bp => {
                    const scores = bp.scores || bp.recent_scores || [];
                    const maxH = 32;
                    const maxScore = scores.length ? Math.max(...scores) : 1;
                    const bars = scores.slice(-20).map(s => {
                        const h = maxScore > 0 ? Math.max(4, (s / maxScore) * maxH) : 4;
                        const cls = scoreClass(s);
                        return `<div class="score-bar ${cls}" style="height:${h}px" title="${s != null ? s.toFixed(2) : '—'}"></div>`;
                    }).join('');

                    const avg = bp.average_score != null ? bp.average_score.toFixed(2) : '—';
                    const count = bp.run_count || bp.count || scores.length || '—';
                    return `
                        <div class="blueprint-row">
                            <div class="blueprint-top">
                                <span class="blueprint-name">${bp.name || bp.blueprint_name || '—'}</span>
                                <span class="blueprint-stats">
                                    <span>📊 ${avg}</span>
                                    <span>#${count}</span>
                                </span>
                            </div>
                            <div class="blueprint-scores">
                                ${bars || '<span style="font-size:0.7rem;color:var(--text-muted)">inga scores</span>'}
                            </div>
                        </div>
                    `;
                }).join('');
            }

            function renderAgents(agents) {
                if (!agents || agents.length === 0) {
                    agentsList.innerHTML =
                    `<div class="empty-state"><span class="icon">◌</span><span>Inga agenter</span></div>`;
                    agentsCount.textContent = '0';
                    return;
                }
                agentsCount.textContent = agents.length;
                agentsList.innerHTML = `
                    <div class="agent-grid">
                        ${agents.map(a => {
                            const status = a.status || a.state || 'idle';
                            const cls = statusClass(status) || 'idle';
                            const bp = a.blueprint_name || a.blueprint || '—';
                            const last = timeAgo(a.updated_at || a.last_active || a.timestamp);
                            return `
                                <div class="agent-card">
                                    <span class="agent-name">${a.name || a.id || '—'}</span>
                                    <span class="agent-status ${cls}">${status}</span>
                                    <span class="agent-meta">${bp} · ${last}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }

            function renderStats(stats, runs, agents, blueprints) {
                const total = stats?.total_runs ?? (runs ? runs.length : '—');
                const active = stats?.active_runs ?? (runs ? runs.filter(r => r.status && !r.status.toLowerCase()
                    .includes('complete') && !r.status.toLowerCase().includes('fail')).length : '—');
                const avg = stats?.average_score ?? stats?.avg_score;
                const avgStr = avg != null ? avg.toFixed(2) : '—';
                const agentCount = stats?.agents ?? (agents ? agents.length : '—');
                const bpCount = stats?.blueprints ?? (blueprints ? blueprints.length : '—');

                statTotalRuns.textContent = total;
                statActiveRuns.textContent = active;
                statAvgScore.textContent = avgStr;
                statAvgSub.textContent = avg != null ? 'per run' : '';
                statAgents.textContent = agentCount;
                const runningAgents = agents ? agents.filter(a => {
                    const s = (a.status || a.state || '').toLowerCase();
                    return s.includes('run') || s.includes('eval') || s.includes('improve');
                }).length : '—';
                statAgentsSub.textContent = runningAgents !== '—' ? runningAgents + ' aktiva' : '';
                statBlueprints.textContent = bpCount;
                runCountBadge.textContent = (runs ? runs.length : '0') + ' runs';
            }

            // ---------- main fetch ----------
            async function fetchAll() {
                let runs = null,
                    blueprints = null,
                    agents = null,
                    stats = null;
                let hasError = false;

                try {
                    const [runsData, bpsData, agentsData, statsData] = await Promise.allSettled([
                        fetchJSON(API_BASE + '/api/runs'),
                        fetchJSON(API_BASE + '/api/blueprints'),
                        fetchJSON(API_BASE + '/api/status'),
                        fetchJSON(API_BASE + '/api/stats')
                    ]);

                    if (runsData.status === 'fulfilled') runs = runsData.value;
                    else console.warn('Runs fetch failed:', runsData.reason);

                    if (bpsData.status === 'fulfilled') blueprints = bpsData.value;
                    else console.warn('Blueprints fetch failed:', bpsData.reason);

                    if (agentsData.status === 'fulfilled') agents = agentsData.value;
                    else console.warn('Status fetch failed:', agentsData.reason);

                    if (statsData.status === 'fulfilled') stats = statsData.value;
                    else console.warn('Stats fetch failed:', statsData.reason);

                    hasError = runsData.status !== 'fulfilled' && bpsData.status !== 'fulfilled' &&
                        agentsData.status !== 'fulfilled' && statsData.status !== 'fulfilled';

                } catch (err) {
                    console.error('Fetch error:', err);
                    hasError = true;
                }

                // Update connection indicator
                if (hasError) {
                    connectionDot.className = 'status-dot error';
                    connectionStatus.textContent = 'Anslutningsfel';
                } else {
                    connectionDot.className = 'status-dot';
                    connectionStatus.textContent = 'Ansluten';
                }

                // Normalize data
                const runsArr = Array.isArray(runs) ? runs : (runs?.runs || runs?.data || []);
                const bpsArr = Array.isArray(blueprints) ? blueprints : (blueprints?.blueprints || blueprints?.data ||
                []);
                const agentsArr = Array.isArray(agents) ? agents : (agents?.agents || agents?.status || agents?.data ||
                []);
                const statsObj = stats || {};

                renderRuns(runsArr);
                renderBlueprints(bpsArr);
                renderAgents(agentsArr);
                renderStats(statsObj, runsArr, agentsArr, bpsArr);

                const now = new Date();
                lastUpdated.textContent = 'Senast uppdaterad: ' + now.toLocaleTimeString('sv-SE', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
            }

            // ---------- polling ----------
            function startPolling() {
                if (isPolling) return;
                isPolling = true;
                fetchAll();
                pollTimer = setInterval(fetchAll, POLL_INTERVAL);
            }

            function stopPolling() {
                isPolling = false;
                if (pollTimer) {
                    clearInterval(pollTimer);
                    pollTimer = null;
                }
            }

            function manualRefresh() {
                stopPolling();
                fetchAll().then(() => startPolling());
            }

            // ---------- init ----------
            refreshBtn.addEventListener('click', manualRefresh);

            // Start
            startPolling();

            // Cleanup on page unload (optional, good practice)
            window.addEventListener('beforeunload', stopPolling);

        })();
    </script>

</body>
</html>
```
### Dashboardöversikt

Panelerna uppdateras automatiskt och ger dig en kontinuerlig bild av systemets tillstånd.

- **Statistikraden** visar nyckeltal som totala runs, aktiva körningar, genomsnittlig score, antal agenter och blueprints. Värdena hämtas från `/api/stats` och uppdateras vid varje pollning.
- **Aktiva runs** listar pågående körningar med ID, blueprint-namn, score, status (färgkodad) och förlopp. Status-taggarna använder färger: blå för running, lila för eval, gul för improving, grön för completed och röd för failed.
- **Score-historik per blueprint** visar varje blueprints senaste scores som staplar – höga scores är gröna, medel är gula, låga är röda. Du ser snabbt trender och genomsnitt.
- **Agent-status** presenterar alla agenter i ett kortgrid med deras nuvarande tillstånd (running/eval/improving/idle) och senaste aktivitet. Du ser omedelbart vilka agenter som är aktiva.
- **Manuell uppdatering** via knappen "Uppdatera nu" återställer polling-cykeln och hämtar färsk data direkt.

---

**Optimeringstips:** API-endpoints förväntas returnera JSON. Om dina svar har annan struktur (t.ex. `{ "runs": [...] }`), justera normaliseringsloggen i `fetchAll()` där `runsArr`, `bpsArr` och `agentsArr` skapas.