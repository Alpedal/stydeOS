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
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #0b0b1a;
            color: #e0e0e0;
            padding: 1.5rem;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        h1 {
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
            letter-spacing: 0.5px;
            color: #f0f0f0;
        }

        .subtitle {
            font-size: 0.9rem;
            color: #8888aa;
            margin-bottom: 1.5rem;
        }

        /* Stats row */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .stat-card {
            background: #12122a;
            border: 1px solid #2a2a4a;
            border-radius: 10px;
            padding: 1rem 1.2rem;
            transition: border-color 0.2s;
        }

        .stat-card:hover {
            border-color: #4a4a7a;
        }

        .stat-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #7a7a9a;
            margin-bottom: 0.3rem;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 600;
            line-height: 1.2;
            color: #f0f0ff;
        }

        .stat-value.accent {
            color: #6fc3df;
        }

        /* Two column layout */
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }

        @media (max-width: 800px) {
            .two-column {
                grid-template-columns: 1fr;
            }
        }

        .panel {
            background: #12122a;
            border: 1px solid #2a2a4a;
            border-radius: 10px;
            padding: 1rem 1.2rem;
        }

        .panel h2 {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            color: #b0b0d0;
            letter-spacing: 0.3px;
            border-bottom: 1px solid #2a2a4a;
            padding-bottom: 0.5rem;
        }

        .run-list, .agent-list {
            list-style: none;
            margin: 0;
        }

        .run-item, .agent-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.6rem 0;
            border-bottom: 1px solid #1e1e3a;
            font-size: 0.9rem;
        }

        .run-item:last-child, .agent-item:last-child {
            border-bottom: none;
        }

        .run-name {
            font-weight: 500;
            color: #d0d0f0;
        }

        .run-status, .agent-state {
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .status-active {
            background: #1d3d2d;
            color: #6fcf97;
        }
        .status-running {
            background: #1d3d2d;
            color: #6fcf97;
        }
        .status-completed {
            background: #1d2d4d;
            color: #6fa3cf;
        }
        .status-failed {
            background: #3d1d1d;
            color: #cf6f6f;
        }
        .status-eval {
            background: #3d351d;
            color: #cfb06f;
        }
        .status-improving {
            background: #2d3d2d;
            color: #8fcf8f;
        }
        .status-idle {
            background: #2a2a3a;
            color: #8888aa;
        }

        .agent-message {
            color: #9999bb;
            font-size: 0.85rem;
            margin-left: 0.5rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 200px;
        }

        /* Blueprint history */
        .blueprint-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 1rem;
        }

        .blueprint-card {
            background: #12122a;
            border: 1px solid #2a2a4a;
            border-radius: 10px;
            padding: 1rem 1.2rem;
            transition: border-color 0.2s;
        }

        .blueprint-card:hover {
            border-color: #4a4a7a;
        }

        .blueprint-name {
            font-size: 0.95rem;
            font-weight: 600;
            color: #c0c0e0;
            margin-bottom: 0.5rem;
        }

        .score-list {
            list-style: none;
            margin: 0;
        }

        .score-list li {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.2rem 0;
            font-size: 0.85rem;
            color: #b0b0c0;
        }

        .score-value {
            font-weight: 600;
            padding: 0.1rem 0.5rem;
            border-radius: 6px;
            font-size: 0.8rem;
        }

        .score-high {
            background: #1d3d2d;
            color: #6fcf97;
        }
        .score-mid {
            background: #3d351d;
            color: #cfb06f;
        }
        .score-low {
            background: #3d1d1d;
            color: #cf6f6f;
        }
        .score-unknown {
            background: #2a2a3a;
            color: #8888aa;
        }

        .no-data {
            color: #666688;
            font-style: italic;
            padding: 0.5rem 0;
        }

        .error-message {
            background: #2a1a1a;
            border: 1px solid #5a2a2a;
            border-radius: 8px;
            padding: 0.8rem 1rem;
            margin-bottom: 1rem;
            color: #cf7f7f;
            font-size: 0.9rem;
        }

        .timestamp {
            font-size: 0.7rem;
            color: #55557a;
            margin-top: 0.5rem;
            text-align: right;
        }

        .loading-dots::after {
            content: "•";
            animation: dots 1.5s steps(3, end) infinite;
            display: inline-block;
            width: 1ch;
            text-align: left;
        }

        @keyframes dots {
            0% { content: "•"; }
            33% { content: "••"; }
            66% { content: "•••"; }
            100% { content: "•"; }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>Forge Command Center</h1>
    <div class="subtitle">Realtidsöversikt · Uppdateras var 5:e sekund</div>

    <div id="error-area"></div>

    <div class="stats-grid" id="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Totala runs</div>
            <div class="stat-value" id="stat-total-runs">—</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Genomsnittlig score</div>
            <div class="stat-value accent" id="stat-avg-score">—</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Aktiva agenter</div>
            <div class="stat-value accent" id="stat-active-agents">—</div>
        </div>
    </div>

    <div class="two-column">
        <div class="panel">
            <h2>Aktiva runs</h2>
            <ul class="run-list" id="active-runs-list">
                <li class="no-data">Inga data ännu</li>
            </ul>
        </div>
        <div class="panel">
            <h2>Agentstatus</h2>
            <ul class="agent-list" id="agent-status-list">
                <li class="no-data">Inga data ännu</li>
            </ul>
        </div>
    </div>

    <div class="panel" style="margin-top: 0.5rem;">
        <h2>Score-historik per blueprint</h2>
        <div class="blueprint-grid" id="blueprint-grid">
            <div class="no-data">Inga blueprints tillgängliga</div>
        </div>
    </div>

    <div class="timestamp" id="update-timestamp">Senast uppdaterad: —</div>
</div>

<script>
    (function() {
        const API_BASE = 'http://localhost:8000';
        const POLL_INTERVAL = 5000; // 5 sekunder

        // DOM-referenser
        const errorArea = document.getElementById('error-area');
        const statTotalRuns = document.getElementById('stat-total-runs');
        const statAvgScore = document.getElementById('stat-avg-score');
        const statActiveAgents = document.getElementById('stat-active-agents');
        const activeRunsList = document.getElementById('active-runs-list');
        const agentStatusList = document.getElementById('agent-status-list');
        const blueprintGrid = document.getElementById('blueprint-grid');
        const updateTimestamp = document.getElementById('update-timestamp');

        // Hjälp: visa fel
        function showError(msg) {
            errorArea.innerHTML = `<div class="error-message">⚠ ${msg}</div>`;
        }

        function clearError() {
            errorArea.innerHTML = '';
        }

        // Hjälp: status-klass
        function statusClass(status) {
            if (!status) return 'status-idle';
            const s = status.toLowerCase();
            if (s === 'running' || s === 'active') return 'status-active';
            if (s === 'completed') return 'status-completed';
            if (s === 'failed') return 'status-failed';
            if (s === 'eval') return 'status-eval';
            if (s === 'improving') return 'status-improving';
            return 'status-idle';
        }

        // score-klass
        function scoreClass(score) {
            if (score === null || score === undefined || isNaN(score)) return 'score-unknown';
            if (score >= 0.7) return 'score-high';
            if (score >= 0.4) return 'score-mid';
            return 'score-low';
        }

        // Formatera tid till svensk tid
        function formatTimestamp(iso) {
            if (!iso) return '—';
            try {
                const d = new Date(iso);
                return d.toLocaleString('sv-SE', {
                    year: 'numeric', month: '2-digit', day: '2-digit',
                    hour: '2-digit', minute: '2-digit', second: '2-digit'
                });
            } catch {
                return iso;
            }
        }

        // Formatera score för visning (0-1 eller %)
        function formatScore(score) {
            if (score === null || score === undefined || isNaN(score)) return '—';
            return (Number(score) * 100).toFixed(1) + '%';
        }

        // Uppdatera tidstämpel
        function updateTimestampNow() {
            const now = new Date();
            updateTimestamp.textContent = 'Senast uppdaterad: ' + now.toLocaleString('sv-SE');
        }

        // Hämta all data parallellt
        async function fetchAllData() {
            const endpoints = [
                { key: 'runs', url: `${API_BASE}/api/runs` },
                { key: 'blueprints', url: `${API_BASE}/api/blueprints` },
                { key: 'stats', url: `${API_BASE}/api/stats` },
                { key: 'status', url: `${API_BASE}/api/status` }
            ];

            const results = await Promise.allSettled(
                endpoints.map(ep => fetch(ep.url).then(res => {
                    if (!res.ok) throw new Error(`HTTP ${res.status} för ${ep.url}`);
                    return res.json();
                }))
            );

            const data = {};
            results.forEach((result, idx) => {
                const key = endpoints[idx].key;
                if (result.status === 'fulfilled') {
                    data[key] = result.value;
                } else {
                    console.warn(`Misslyckades att hämta ${key}:`, result.reason);
                    data[key] = null;
                }
            });

            return data;
        }

        // Rendera alla sektioner
        function renderDashboard(data) {
            // Stats
            const stats = data.stats || {};
            statTotalRuns.textContent = stats.total_runs !== undefined ? stats.total_runs : '—';
            if (stats.average_score !== undefined && stats.average_score !== null) {
                statAvgScore.textContent = formatScore(stats.average_score);
            } else {
                statAvgScore.textContent = '—';
            }
            statActiveAgents.textContent = stats.active_agents !== undefined ? stats.active_agents : '—';

            // Aktiva runs (filtrera de som är running/active)
            const runs = Array.isArray(data.runs) ? data.runs : [];
            const activeRuns = runs.filter(r => {
                const s = (r.status || '').toLowerCase();
                return s === 'running' || s === 'active';
            });

            if (activeRuns.length === 0) {
                activeRunsList.innerHTML = '<li class="no-data">Inga aktiva runs</li>';
            } else {
                activeRunsList.innerHTML = activeRuns.map(run => {
                    const status = run.status || 'unknown';
                    const cls = statusClass(status);
                    const name = run.name || run.blueprint || `Run #${run.id}`;
                    return `
                        <li class="run-item">
                            <span class="run-name">${name}</span>
                            <span>
                                <span class="run-status ${cls}">${status}</span>
                                ${run.score !== undefined && run.score !== null ? `<span style="margin-left:0.4rem;font-size:0.75rem;color:#aaa;">${formatScore(run.score)}</span>` : ''}
                            </span>
                        </li>
                    `;
                }).join('');
            }

            // Agentstatus (förväntar sig objekt med state, message)
            const status = data.status || {};
            const agentState = status.state || 'idle';
            const agentMessage = status.message || '';
            const agentCls = statusClass(agentState);
            agentStatusList.innerHTML = `
                <li class="agent-item">
                    <span>
                        <span class="agent-state ${agentCls}">${agentState}</span>
                        ${agentMessage ? `<span class="agent-message" title="${agentMessage}">${agentMessage}</span>` : ''}
                    </span>
                </li>
            `;

            // Blueprint-score-historik
            const blueprints = Array.isArray(data.blueprints) ? data.blueprints : [];
            if (blueprints.length === 0) {
                blueprintGrid.innerHTML = '<div class="no-data" style="grid-column:1/-1;">Inga blueprints tillgängliga</div>';
            } else {
                blueprintGrid.innerHTML = blueprints.map(bp => {
                    const name = bp.name || bp.id || 'Okänd';
                    const scores = Array.isArray(bp.scores) ? bp.scores : [];
                    // visa max 5 senaste scores
                    const recentScores = scores.slice(-5);
                    let scoresHtml;
                    if (recentScores.length === 0) {
                        scoresHtml = '<li class="no-data">Inga scores</li>';
                    } else {
                        scoresHtml = recentScores.map(s => {
                            const scoreVal = s.score !== undefined ? s.score : null;
                            const time = formatTimestamp(s.timestamp);
                            const cls = scoreClass(scoreVal);
                            const displayScore = scoreVal !== null ? formatScore(scoreVal) : '—';
                            return `
                                <li>
                                    <span>${time}</span>
                                    <span class="score-value ${cls}">${displayScore}</span>
                                </li>
                            `;
                        }).join('');
                    }

                    return `
                        <div class="blueprint-card">
                            <div class="blueprint-name">${name}</div>
                            <ul class="score-list">${scoresHtml}</ul>
                        </div>
                    `;
                }).join('');
            }

            updateTimestampNow();
        }

        // Huvudloop
        async function poll() {
            try {
                const data = await fetchAllData();
                clearError();
                renderDashboard(data);
            } catch (err) {
                showError('Kunde inte hämta data från API. Kontrollera att servern körs på ' + API_BASE);
                console.error('Poll error:', err);
                // Försök rendera med befintlig data om möjligt?
            }
        }

        // Starta polling
        poll(); // första direkt
        setInterval(poll, POLL_INTERVAL);
    })();
</script>
</body>
</html>
```