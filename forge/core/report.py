"""Forge v2 run report generator.

Generates a standalone, visually stunning HTML report (report.html) inside
the run directory, showing scores, metrics, judge comments, logs, and prompt diffs.
"""

import json
from pathlib import Path
from typing import Optional

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Forge Run Report - {run_id}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #090b11;
            --surface: #131722;
            --surface-glass: rgba(19, 23, 34, 0.7);
            --border: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.15);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.15);
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.15);
            --warning: #f59e0b;
            --warning-glow: rgba(245, 158, 11, 0.15);
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.15);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg);
            color: var(--text-primary);
            font-family: 'Plus Jakarta Sans', sans-serif;
            line-height: 1.6;
            padding: 2rem 1rem;
            min-height: 100vh;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.08) 0px, transparent 50%);
            background-attachment: fixed;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        /* Header Card */
        header {{
            background: var(--surface-glass);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            padding: 2rem;
            border-radius: 24px;
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1.5rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }}

        .header-left h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}

        .header-left p {{
            color: var(--text-secondary);
            font-size: 1rem;
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.5rem 1rem;
            border-radius: 99px;
            font-weight: 600;
            font-size: 0.85rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .badge-completed {{
            background: var(--success-glow);
            color: var(--success);
            border: 1px solid var(--success);
        }}

        .badge-failed {{
            background: var(--danger-glow);
            color: var(--danger);
            border: 1px solid var(--danger);
        }}

        .badge-running {{
            background: rgba(99, 102, 241, 0.15);
            color: var(--primary);
            border: 1px solid var(--primary);
        }}

        /* Dashboard Grid */
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1.5rem;
            transition: all 0.3s ease;
        }}

        .card:hover {{
            border-color: var(--border-hover);
            transform: translateY(-2px);
        }}

        .card-title {{
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        /* Score Gauge */
        .score-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 1rem 0;
        }}

        .gauge-svg {{
            width: 140px;
            height: 140px;
            transform: rotate(-90deg);
        }}

        .gauge-bg {{
            fill: none;
            stroke: #1f2937;
            stroke-width: 12;
        }}

        .gauge-fill {{
            fill: none;
            stroke-width: 12;
            stroke-linecap: round;
            transition: stroke-dasharray 1s ease;
        }}

        .gauge-text {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            margin-top: -95px;
            margin-bottom: 40px;
        }}

        /* Metadata lists */
        .meta-list {{
            list-style: none;
        }}

        .meta-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }}

        .meta-item:last-child {{
            border-bottom: none;
        }}

        .meta-label {{
            color: var(--text-secondary);
        }}

        .meta-val {{
            font-weight: 600;
            color: var(--text-primary);
        }}

        .meta-val-mono {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            background: rgba(255, 255, 255, 0.03);
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
        }}

        /* Sections */
        .section-header {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.5rem;
            font-weight: 600;
            margin-top: 2rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
            color: var(--text-primary);
        }}

        /* Accordion / Expandables */
        .accordion-item {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            margin-bottom: 1rem;
            overflow: hidden;
        }}

        .accordion-header {{
            padding: 1.25rem 1.5rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
            background: rgba(255, 255, 255, 0.01);
            transition: background 0.2s ease;
        }}

        .accordion-header:hover {{
            background: rgba(255, 255, 255, 0.03);
        }}

        .accordion-content {{
            display: none;
            padding: 1.5rem;
            border-top: 1px solid var(--border);
            background: rgba(0, 0, 0, 0.15);
        }}

        .accordion-item.active .accordion-content {{
            display: block;
        }}

        .arrow-icon {{
            transition: transform 0.2s ease;
        }}

        .accordion-item.active .arrow-icon {{
            transform: rotate(180deg);
        }}

        /* Code & Text Area Display */
        .code-block {{
            background: #06080d;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            overflow-x: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            color: #d1d5db;
            margin-bottom: 1rem;
        }}

        /* Benchmark Case detail card */
        .case-card {{
            border-left: 4px solid var(--primary);
            padding-left: 1rem;
            margin-bottom: 1.5rem;
        }}

        .case-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}

        .case-title {{
            font-weight: 700;
            font-size: 1.1rem;
        }}

        .case-score {{
            font-weight: 600;
            font-size: 1rem;
        }}

        .case-detail-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 0.75rem;
            font-size: 0.9rem;
        }}

        .kw-tag {{
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 99px;
            font-size: 0.8rem;
            margin-right: 0.25rem;
            margin-bottom: 0.25rem;
            font-weight: 500;
        }}

        .kw-found {{
            background: rgba(16, 185, 129, 0.12);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.2);
        }}

        .kw-missing {{
            background: rgba(239, 68, 68, 0.12);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <div class="header-left">
                <h1>Forge Run Report</h1>
                <p>Run ID: <span style="font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #a5b4fc;">{run_id}</span></p>
            </div>
            <div>
                <span class="badge {badge_class}">{status}</span>
            </div>
        </header>

        <!-- Dashboard Widgets -->
        <div class="grid">
            <!-- Score Card -->
            <div class="card" style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <div class="card-title">Training Score</div>
                <div class="score-container">
                    <svg class="gauge-svg" viewBox="0 0 100 100">
                        <circle class="gauge-bg" cx="50" cy="50" r="40" />
                        <circle class="gauge-fill" cx="50" cy="50" r="40" 
                                stroke="{gauge_color}" 
                                stroke-dasharray="{gauge_dasharray} 251.2" />
                    </svg>
                    <div class="gauge-text" style="color: {gauge_color};">{score_text}</div>
                </div>
            </div>

            <!-- Metadata Card -->
            <div class="card">
                <div class="card-title">Run Details</div>
                <ul class="meta-list">
                    <li class="meta-item">
                        <span class="meta-label">Blueprint ID</span>
                        <span class="meta-val">{blueprint_id}</span>
                    </li>
                    <li class="meta-item">
                        <span class="meta-label">Git Commit</span>
                        <span class="meta-val-mono">{git_commit}</span>
                    </li>
                    <li class="meta-item">
                        <span class="meta-label">Workspace Clean</span>
                        <span class="meta-val" style="color: {dirty_color};">{dirty_text}</span>
                    </li>
                    <li class="meta-item">
                        <span class="meta-label">Evaluated At</span>
                        <span class="meta-val" style="font-size: 0.9rem;">{evaluated_at}</span>
                    </li>
                </ul>
            </div>

            <!-- LLM Evaluator Judges -->
            <div class="card">
                <div class="card-title">Impartial Judges</div>
                <ul class="meta-list">
                    <li class="meta-item">
                        <span class="meta-label">Self Evaluation Score</span>
                        <span class="meta-val">{self_eval}/100</span>
                    </li>
                    <li class="meta-item">
                        <span class="meta-label">Impartial Judge Score</span>
                        <span class="meta-val">{judge_eval}/100</span>
                    </li>
                    <li class="meta-item">
                        <span class="meta-label">Benchmark Test Score</span>
                        <span class="meta-val">{benchmark_score}/100</span>
                    </li>
                </ul>
            </div>
        </div>

        <!-- Detail Expanders -->
        <div class="section-header">Evaluation Logs & Output</div>

        <!-- 1. Agent Generated Output -->
        <div class="accordion-item">
            <div class="accordion-header" onclick="toggleAccordion(this)">
                <span>Agent Generated Output (output.md)</span>
                <span class="arrow-icon">&#9662;</span>
            </div>
            <div class="accordion-content">
                <div class="code-block" style="white-space: pre-wrap; font-family: inherit; font-size: 0.95rem; line-height: 1.7; background: #0b0d14;">{agent_output}</div>
            </div>
        </div>

        <!-- 1.5. Persona Diff -->
        <div class="accordion-item">
            <div class="accordion-header" onclick="toggleAccordion(this)">
                <span>Persona Config Unified Diff (compared to previous run)</span>
                <span class="arrow-icon">&#9662;</span>
            </div>
            <div class="accordion-content">
                {persona_diff}
            </div>
        </div>

        <!-- 2. Benchmark Case Results -->
        <div class="accordion-item">
            <div class="accordion-header" onclick="toggleAccordion(this)">
                <span>Benchmark Case Breakdown</span>
                <span class="arrow-icon">&#9662;</span>
            </div>
            <div class="accordion-content">
                {benchmark_cases_html}
            </div>
        </div>

        <!-- 3. Teacher Feedback -->
        <div class="accordion-item">
            <div class="accordion-header" onclick="toggleAccordion(this)">
                <span>Teacher Feedback & Improvements</span>
                <span class="arrow-icon">&#9662;</span>
            </div>
            <div class="accordion-content">
                <div class="code-block" style="white-space: pre-wrap; font-family: inherit; font-size: 0.95rem; line-height: 1.7; background: #0b0d14;">{teacher_feedback}</div>
            </div>
        </div>

        <!-- 4. Execution Logs -->
        <div class="accordion-item">
            <div class="accordion-header" onclick="toggleAccordion(this)">
                <span>Console & API Execution Logs (forge.log)</span>
                <span class="arrow-icon">&#9662;</span>
            </div>
            <div class="accordion-content">
                <pre class="code-block" style="max-height: 400px; overflow-y: auto;">{forge_logs}</pre>
            </div>
        </div>
    </div>

    <script>
        function toggleAccordion(header) {{
            const item = header.parentElement;
            item.classList.toggle('active');
        }}
    </script>
</body>
</html>
"""

def _generate_persona_diff(root: Path, run_id: str, prev_run_id: Optional[str]) -> str:
    """Compare persona.md of the current run against the previous run's persona.md."""
    if not prev_run_id:
        return '<div style="color: var(--text-muted);">No previous run found to compare persona.md.</div>'
    
    curr_path = root / "runs" / run_id / "persona.md"
    prev_path = root / "runs" / prev_run_id / "persona.md"
    
    if not curr_path.exists():
        return '<div style="color: var(--text-muted);">Current persona.md not found in run folder.</div>'
    if not prev_path.exists():
        return f'<div style="color: var(--text-muted);">Previous persona.md (from {prev_run_id}) not found.</div>'
        
    try:
        curr_lines = curr_path.read_text(encoding="utf-8").splitlines()
        prev_lines = prev_path.read_text(encoding="utf-8").splitlines()
        
        import difflib
        import html
        diff_lines = list(difflib.unified_diff(
            prev_lines, curr_lines, 
            fromfile=f"run_{prev_run_id}/persona.md", 
            tofile=f"run_{run_id}/persona.md", 
            lineterm=""
        ))
        
        if not diff_lines:
            return '<div style="color: var(--success); font-weight: 600;">No changes made to persona.md compared to previous run.</div>'
            
        html_lines = []
        for line in diff_lines:
            escaped = html.escape(line)
            if line.startswith("+"):
                html_lines.append(f'<span style="color: var(--success); background: rgba(16, 185, 129, 0.1); display: block;">{escaped}</span>')
            elif line.startswith("-"):
                html_lines.append(f'<span style="color: var(--danger); background: rgba(239, 68, 68, 0.1); display: block;">{escaped}</span>')
            elif line.startswith("@@"):
                html_lines.append(f'<span style="color: var(--primary); display: block; font-weight: 600; margin-top: 0.5rem; margin-bottom: 0.5rem;">{escaped}</span>')
            else:
                html_lines.append(f'<span style="color: var(--text-secondary); display: block;">{escaped}</span>')
                
        return f'<pre class="code-block" style="font-family: \'JetBrains Mono\', monospace; font-size: 0.85rem; line-height: 1.5; background: #06080d; padding: 1rem; border-radius: 8px; max-height: 500px; overflow-y: auto;">{"".join(html_lines)}</pre>'
    except Exception as e:
        return f'<div style="color: var(--danger);">Failed to compute diff: {e}</div>'


def generate_report(root: Path, run_id: str) -> None:
    """Generate a report.html file in the run folder."""
    run_dir = root / "runs" / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_id}")

    # Read inputs
    import json
    from forge.core.engine import load_run_data, load_manifest

    run_data = load_run_data(run_dir)
    input_raw = run_data.get("input")
    input_json = json.loads(input_raw) if input_raw else {}

    blueprint_id = input_json.get("blueprint_id", "unknown")
    git_commit = input_json.get("git_commit", "-")
    git_dirty = input_json.get("git_dirty", False)

    # Find previous run ID from manifest
    prev_run_id = None
    try:
        manifest = load_manifest(root)
        runs = manifest.get("runs", [])
        runs_sorted = sorted(runs, key=lambda r: r["run_id"])
        for idx, r in enumerate(runs_sorted):
            if r["run_id"] == run_id:
                for p_idx in range(idx - 1, -1, -1):
                    if runs_sorted[p_idx]["blueprint_id"] == blueprint_id:
                        prev_run_id = runs_sorted[p_idx]["run_id"]
                        break
                break
    except Exception:
        pass

    # Generate Diff
    persona_diff = _generate_persona_diff(root, run_id, prev_run_id)

    # Read evaluation
    eval_raw = run_data.get("eval")
    eval_json = json.loads(eval_raw) if eval_raw else {}

    final_score = eval_json.get("final_score", 0.0)
    self_eval = eval_json.get("self_eval", "-")
    judge_eval = eval_json.get("judge_eval", "-")
    evaluated_at = eval_json.get("evaluated_at", "-")

    # Read benchmark details
    bench_data = eval_json.get("benchmark", {})
    benchmark_score = bench_data.get("score", "-")
    cases = bench_data.get("results", [])

    # Format benchmark cases html
    cases_html_list = []
    for c in cases:
        case_id = c.get("id", "unknown")
        score = c.get("score", 0.0)
        output = c.get("output", "")
        reason = c.get("reason", "")
        expected_found = c.get("expected_found", [])
        expected_missing = c.get("expected_missing", [])
        forbidden_found = c.get("forbidden_found", [])

        # Color based on score
        color = "var(--success)" if score >= 85.0 else ("var(--warning)" if score >= 50.0 else "var(--danger)")
        
        expected_tags = []
        for kw in expected_found:
            expected_tags.append(f'<span class="kw-tag kw-found">{kw} (found)</span>')
        for kw in expected_missing:
            expected_tags.append(f'<span class="kw-tag kw-missing">{kw} (missing)</span>')
        for kw in forbidden_found:
            expected_tags.append(f'<span class="kw-tag kw-missing">{kw} (forbidden found!)</span>')

        case_html = f"""
        <div class="case-card" style="border-left-color: {color}; margin-bottom: 2rem;">
            <div class="case-header">
                <span class="case-title">{case_id}</span>
                <span class="case-score" style="color: {color}; font-weight: bold;">{score}/100</span>
            </div>
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                <strong>Judge Comment:</strong> {reason}
            </div>
            <div style="margin-bottom: 0.5rem;">
                {"".join(expected_tags)}
            </div>
            <div class="code-block" style="font-size: 0.85rem; max-height: 200px; overflow-y: auto; background: #06080d;">{output}</div>
        </div>
        """
        cases_html_list.append(case_html)

    if not cases_html_list:
        benchmark_cases_html = '<div style="color: var(--text-muted);">No benchmark cases executed.</div>'
    else:
        benchmark_cases_html = "\n".join(cases_html_list)

    # Read output.md
    agent_output = run_data.get("output") or "(No output generated)"

    # Read feedback.md
    teacher_feedback = run_data.get("feedback") or "(No feedback available)"

    # Read forge.log
    log_path = run_dir / "forge.log"
    forge_logs = ""
    if log_path.exists():
        try:
            forge_logs = log_path.read_text(encoding="utf-8")
        except Exception:
            pass
    if not forge_logs:
        forge_logs = "(No logs recorded)"

    # Determine status and badges
    score_val = float(final_score) if final_score != "-" else 0.0
    status = "running"
    badge_class = "badge-running"
    if eval_raw:
        if score_val >= 85.0:
            status = "completed"
            badge_class = "badge-completed"
        else:
            status = "failed"
            badge_class = "badge-failed"

    # SVG Dasharray computation
    gauge_dasharray = (score_val / 100.0) * 251.2
    gauge_color = "var(--success)" if score_val >= 85.0 else ("var(--warning)" if score_val >= 50.0 else "var(--danger)")

    # Dirty status
    dirty_text = "No" if not git_dirty else "Yes"
    dirty_color = "var(--success)" if not git_dirty else "var(--danger)"

    score_text = f"{final_score}%" if final_score != "-" else "-%"

    html_content = HTML_TEMPLATE.format(
        run_id=run_id,
        status=status,
        badge_class=badge_class,
        score_text=score_text,
        gauge_color=gauge_color,
        gauge_dasharray=gauge_dasharray,
        blueprint_id=blueprint_id,
        git_commit=git_commit,
        dirty_text=dirty_text,
        dirty_color=dirty_color,
        evaluated_at=evaluated_at,
        self_eval=self_eval,
        judge_eval=judge_eval,
        benchmark_score=benchmark_score,
        agent_output=agent_output,
        persona_diff=persona_diff,
        benchmark_cases_html=benchmark_cases_html,
        teacher_feedback=teacher_feedback,
        forge_logs=forge_logs
    )

    report_file = run_dir / "report.html"
    report_file.write_text(html_content, encoding="utf-8")
    print(f"  [OK] Run report generated: {report_file}")
