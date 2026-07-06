"""tools_impl.py — Dynamic tool implementations for Hund AI.

If a function matching the tool name exists here, it will be called directly
with the agent's arguments. Falls back to mock_responses.yaml if a function
is not defined.

Each tool function receives keyword arguments matching the tool's parameters
and should return a plain string (the tool's result).
"""

from pathlib import Path


def file_read(path: str, **_) -> str:
    """Read a file from the workspace and return its content (first 2000 chars)."""
    try:
        p = Path(path)
        if not p.exists():
            return f"(Error: File not found: {path})"
        if not p.is_file():
            return f"(Error: Path is not a file: {path})"
        content = p.read_text(encoding="utf-8")
        if len(content) > 2000:
            return content[:2000] + f"\n\n... (truncated, {len(content)} chars total)"
        return content
    except Exception as e:
        return f"(Error reading file: {e})"


def list_active_agents(**_) -> str:
    """Return a mock list of active agents on the styde.ai platform."""
    return (
        "Aktiva agenter:\n"
        "- invoice-reviewer-agent  (status: nere,   senast aktiv: 2026-07-05 14:32)\n"
        "- data-processor-agent    (status: aktiv,  KPI: 99.2% framgang)\n"
        "- customer-support-agent  (status: aktiv,  KPI: 4.8/5 kundnojdhet)\n"
    )


def get_agent_status(agent_id: str, **_) -> str:
    """Return status for a specific agent."""
    statuses = {
        "invoice-reviewer-agent": (
            "Status: nere. Senaste krasch: 2026-07-05 14:32. Felkod: SIGTERM.\n"
            "KPI: 0/100 (inaktiv). Senaste framgangsrika korning: 2026-07-04."
        ),
        "data-processor-agent": (
            "Status: aktiv. Drifttid: 48h. KPI: 99.2% framgang (last 1000 jobb)."
        ),
        "customer-support-agent": (
            "Status: aktiv. KPI: 4.8/5 kundnojdhet (sista 30 dagarna)."
        ),
    }
    return statuses.get(agent_id, f"Status: okand. Ingen information tillganglig for agent '{agent_id}'.")


def search_knowledge_base(query: str, scope: str = "all", **_) -> str:
    """Search the styde.ai knowledge base (simulated)."""
    return (
        f"Sokresultat for '{query}' (scope={scope}):\n"
        "- Forge v2 agent training guide (docs/forge-v2.md)\n"
        "- Blueprint schema reference (docs/blueprint-schema.md)\n"
        "- styde.ai platform overview (docs/platform.md)\n"
    )
