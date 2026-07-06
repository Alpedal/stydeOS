```html
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            padding: 1.5rem;
            line-height: 1.5;
            min-height: 100vh;
        }

        /* layout */
        .dashboard {
            max-width: 1440px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.25rem;
        }

        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 1.25rem 1.25rem 1.5rem;
            box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        }

        .card-full {
            grid-column: 1 / -1;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #21262d;
        }

        .card-header h2 {
            font-size: 1.1rem;
            font-weight: 600;
            letter-spacing: 0.3px;
            color: #f0f6fc;
        }

        .badge {
            background: #21262d;
            padding: 0.2rem 0.7rem;
            border-radius: 20px;
            font-size: 0.75rem;
            color: #8b949e;
        }

        /* stats row */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 0.75rem;
        }

        .stat-item {
            background: #0d1117;
            border-radius: 6px;
            padding: 0.8rem 1rem;
            border: 1px solid #21262d;
        }

        .stat-label {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #8b949e;
        }

        .stat-value {
            font-size: 1.6rem;
            font-weight: 600;
            margin-top: 0.2rem;
            color: #f0f6fc;
        }

        /* table-like lists */
        .list {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .list-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #0d1117;
            padding: 0.6rem 0.9rem;
            border-radius: 6px;
            border: 1px solid #21262d;
            font-size: 0.85rem;
        }

        .list-item .left {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            min-width: 0;
            flex: 1;
        }

        .list-item .left .name {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: #e6edf3;
        }

        .list-item .right {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            flex-shrink: 0;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            flex-shrink: 0;
        }

        .status-dot.running { background: #58a6ff; }
        .status-dot.eval    { background: #d29922; }
        .status-dot.improving { background: #a371f7; }
        .status-dot.completed { background: #3fb950; }
        .status-dot.failed  { background: #f85149; }
        .status-dot.pending { background: #8b949e; }

        .status-label {
            font-size: 0.75rem;
            padding: 0.15rem 0.6rem;
            border-radius: 12px;
            background: #21262d;
            color: #8b949e;
            min-width: 60px;
            text-align: center;
        }

        .status-label.running { background: #1f3a5f; color: #58a6ff; }
        .status-label.eval { background: #3d2e1a; color: #d29922; }
        .status-label.improving { background: #2a1f3d; color: #a371f7; }
        .status-label.completed { background: #1a3d2a; color: #3fb950; }
        .status-label.failed { background: #3d1a1a; color: #f85149; }

        .score-bar {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
        }

        .score-bar .bar {
            width: 60px;
            height: 6px;
            background: #21262d;
            border-radius: 4px;
            overflow: hidden;
        }

        .score-bar .bar .fill {
            height: 100%;
            border-radius: 4px;
            background: #58a6ff;
            transition: width 0.3s;
        }

        .score-value {
            font-weight: 600;
            min-width: 2rem;
            text-align: right;
            font-size: 0.8rem;
            color: #f0f6fc;
        }

        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.75rem;
        }

        .agent-card {
            background: #0d1117;
            border-radius: 6px;
            padding: 0.8rem 1rem;
            border: 1px solid #21262d;
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }

        .agent-card .info {
            flex: 1;
            min-width: 0;
        }

        .agent-card .name {
            font-weight: 500;
            font-size: 0.9rem;
        }

        .agent-card .sub {
            font-size: 0.7rem;
            color: #8b949e;
        }

        .empty-message {
            color: #8b949e;
            font-size: 0.85rem;
            padding: 1rem 0;
            text-align: center;
        }

        .error-message {
            color: #f85149;
            font-size: 0.8rem;
            padding: 0.5rem 0;
        }

        /* responsive */
        @media (max-width: 800px) {
            .dashboard {
                grid-template-columns: 1fr;
                gap: 1rem;
            }
            body {
                padding: 0.8rem;
            }
        }
    </style>
</head>
<body>
<div class="dashboard" id="app">

    <!-- Stats (full width) -->
    <div class="card card-full" id="stats-card">
        <div class="card-header">
            <h2>Sammanfattning</h2>
            <span class="badge" id="update-badge">uppdateras...</span>
        </div>
        <div class="stats-grid" id="stats-grid">
            <div class="stat-item">
                <div class="stat-label">Genomsnittlig score</div>
                <div class="stat-value" id="stat-avg-score">—</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Totala runs</div>
                <div class="stat-value" id="stat-total-runs">—</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Aktiva runs</div>
                <div class="stat-value" id="stat-active-runs">—</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Agenter</div>
                <div class="stat-value" id="stat-agents">—</div>
            </div>
        </div>
    </div>

    <!-- Active runs -->
    <div class="card" id="runs-card">
        <div class="card-header">
            <h2>Aktiva runs</h2>
            <span class="badge" id="runs-count">0</span>
        </div>
        <div class="list" id="runs-list">
            <div class="empty-message">Inga aktiva runs</div>
        </div>
    </div>

    <!-- Score-historik per blueprint -->
    <div class="card" id="blueprints-card">
        <div class="card-header">
            <h2>Score per blueprint</h2>
            <span class="badge" id="blueprints-count">0</span>
        </div>
        <div class="list" id="blueprints-list">
            <div class="empty-message">Inga blueprints</div>
        </div>
    </div>

    <!-- Agentstatus -->
    <div class="card card-full" id="agents-card">
        <div class="card-header">
            <h2>Agentstatus</h2>
            <span class="badge" id="agents-count">0</span>
        </div>
        <div class="agent-grid" id="agents-grid">
            <div class="empty-message">Inga agenter</div>
        </div>
    </div>
</div>

<script>
    (function() {
        const API_BASE = 'http://localhost:8000';
        const POLL_INTERVAL = 5000; // 5 seconds

        const cache = {
            runs: [],
            blueprints: [],
            stats: null,
            agents: []
        };

        // DOM references
        const $ = id => document.getElementById(id);
        const runsList = $('runs-list');
        const runsCount = $('runs-count');
        const blueprintsList = $('blueprints-list');
        const blueprintsCount = $('blueprints-count');
        const agentsGrid = $('agents-grid');
        const agentsCount = $('agents-count');
        const statAvgScore = $('stat-avg-score');
        const statTotalRuns = $('stat-total-runs');
        const statActiveRuns = $('stat-active-runs');
        const statAgents = $('stat-agents');
        const updateBadge = $('update-badge');

        // --- helpers ---
        function statusColor(status) {
            const s = (status || '').toLowerCase();
            if (s.includes('running')) return 'running';
            if (s.includes('eval')) return 'eval';
            if (s.includes('improving')) return 'improving';
            if (s.includes('complete') || s.includes('success')) return 'completed';
            if (s.includes('fail') || s.includes('error')) return 'failed';
            return 'pending';
        }

        function formatScore(score) {
            if (score === null || score === undefined) return '—';
            const num = Number(score);
            return isNaN(num) ? score : num.toFixed(1);
        }

        function scorePercent(score) {
            const num = Number(score);
            if (isNaN(num)) return 0;
            return Math.min(Math.max(num, 0), 100);
        }

        // --- rendering ---
        function renderRuns(runs) {
            if (!runs || runs.length === 0) {
                runsList.innerHTML = '<div class="empty-message">Inga aktiva runs</div>';
                runsCount.textContent = '0';
                return;
            }
            runsCount.textContent = runs.length;
            const html = runs.map(run => {
                const status = statusColor(run.status || '');
                const name = run.name || run.id || 'Run #' + Math.random().toString(36).slice(2,6);
                const score = run.score !== undefined && run.score !== null ? formatScore(run.score) : '—';
                const barWidth = score !== '—' ? scorePercent(run.score) : 0;
                return `
                    <div class="list-item">
                        <div class="left">
                            <span class="status-dot ${status}"></span>
                            <span class="name">${name}</span>
                        </div>
                        <div class="right">
                            <span class="status-label ${status}">${run.status || 'okänt'}</span>
                            <span class="score-bar">
                                <span class="bar"><span class="fill" style="width:${barWidth}%"></span></span>
                                <span class="score-value">${score}</span>
                            </span>
                        </div>
                    </div>
                `;
            }).join('');
            runsList.innerHTML = html;
        }

        function renderBlueprints(blueprints) {
            if (!blueprints || blueprints.length === 0) {
                blueprintsList.innerHTML = '<div class="empty-message">Inga blueprints</div>';
                blueprintsCount.textContent = '0';
                return;
            }
            blueprintsCount.textContent = blueprints.length;
            // Visa senaste score per blueprint (eller genomsnitt)
            const html = blueprints.map(bp => {
                const name = bp.name || bp.id || 'Blueprint';
                let score = '—';
                let barWidth = 0;
                // Om det finns en lista med scores, ta senaste
                if (bp.scores && Array.isArray(bp.scores) && bp.scores.length > 0) {
                    const lastScore = bp.scores[bp.scores.length - 1];
                    score = formatScore(lastScore);
                    barWidth = scorePercent(lastScore);
                } else if (bp.score !== undefined && bp.score !== null) {
                    score = formatScore(bp.score);
                    barWidth = scorePercent(bp.score);
                }
                return `
                    <div class="list-item">
                        <div class="left">
                            <span class="name">${name}</span>
                        </div>
                        <div class="right">
                            <span class="score-bar">
                                <span class="bar"><span class="fill" style="width:${barWidth}%"></span></span>
                                <span class="score-value">${score}</span>
                            </span>
                        </div>
                    </div>
                `;
            }).join('');
            blueprintsList.innerHTML = html;
        }

        function renderAgents(agents) {
            if (!agents || agents.length === 0) {
                agentsGrid.innerHTML = '<div class="empty-message">Inga agenter</div>';
                agentsCount.textContent = '0';
                return;
            }
            agentsCount.textContent = agents.length;
            const html = agents.map(agent => {
                const name = agent.name || agent.id || 'Agent';
                const status = statusColor(agent.status || '');
                const statusText = agent.status || 'okänd';
                const detail = agent.detail || agent.blueprint || '';
                return `
                    <div class="agent-card">
                        <span class="status-dot ${status}"></span>
                        <div class="info">
                            <div class="name">${name}</div>
                            <div class="sub">${detail ? detail : statusText}</div>
                        </div>
                        <span class="status-label ${status}">${statusText}</span>
                    </div>
                `;
            }).join('');
            agentsGrid.innerHTML = html;
        }

        function renderStats(stats) {
            if (!stats) {
                statAvgScore.textContent = '—';
                statTotalRuns.textContent = '—';
                statActiveRuns.textContent = '—';
                statAgents.textContent = '—';
                return;
            }
            statAvgScore.textContent = stats.avg_score !== undefined ? formatScore(stats.avg_score) : '—';
            statTotalRuns.textContent = stats.total_runs !== undefined ? stats.total_runs : '—';
            statActiveRuns.textContent = stats.active_runs !== undefined ? stats.active_runs : '—';
            statAgents.textContent = stats.agents !== undefined ? stats.agents : '—';
        }

        function updateBadgeTime() {
            const now = new Date();
            const time = now.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            updateBadge.textContent = 'uppdaterat ' + time;
        }

        // --- fetch all ---
        async function fetchAll() {
            const endpoints = [
                { key: 'runs', url: `${API_BASE}/api/runs` },
                { key: 'blueprints', url: `${API_BASE}/api/blueprints` },
                { key: 'stats', url: `${API_BASE}/api/stats` },
                { key: 'agents', url: `${API_BASE}/api/status` }
            ];

            const results = await Promise.allSettled(
                endpoints.map(ep => fetch(ep.url).then(res => {
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    return res.json();
                }))
            );

            const data = {};
            results.forEach((result, idx) => {
                const key = endpoints[idx].key;
                if (result.status === 'fulfilled') {
                    data[key] = result.value;
                } else {
                    console.warn(`Failed to fetch ${key}:`, result.reason);
                    data[key] = null;
                }
            });

            return data;
        }

        async function refresh() {
            try {
                const data = await fetchAll();

                // Spara i cache
                if (data.runs) cache.runs = data.runs;
                if (data.blueprints) cache.blueprints = data.blueprints;
                if (data.stats) cache.stats = data.stats;
                if (data.agents) cache.agents = data.agents;

                // Rendera med cache (fallback om null)
                renderRuns(cache.runs);
                renderBlueprints(cache.blueprints);
                renderStats(cache.stats);
                renderAgents(cache.agents);
                updateBadgeTime();
            } catch (err) {
                console.error('Refresh error:', err);
                // Visa ev fel i stats
                statAvgScore.textContent = '?';
                updateBadge.textContent = 'fel vid uppdatering';
            }
        }

        // --- start polling ---
        refresh(); // första omedelbart
        setInterval(refresh, POLL_INTERVAL);
    })();
</script>
</body>
</html>
```