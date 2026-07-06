## What Went Wrong
- In `run_20260706-014930`, the agent again hit the **max tool turns** limit and **did not produce** the required HTML file.  
- No dashboard was delivered – the agent spent all available turns on tool calls instead of generating output.

## Which Rules Were Broken
- **Output Format** – “Kompletta HTML-filer med inline CSS och JS. En fil per vy.” – No file was produced at all.  
- **Behavior Rule 1** – The agent was supposed to build a simple HTML/CSS/JS dashboard, but never executed any UI construction.  
- **Previously added rule 6** (Verktygsanvändning) – Even though it limited tool calls to 3 and asked for immediate HTML generation, it did **not** prevent the loop. The rule still assumed some data fetching was required, which led the agent to continue using tools.

## Proposed Fixes
The root cause is that the agent incorrectly tried to **fetch API data via tool calls** before building the dashboard. However, the persona already states: “All data hämtas från API — inga hårdkodade värden.” This applies to the **generated HTML’s JavaScript**, not the agent’s own actions. The agent’s job is solely to produce an HTML file that contains `fetch` calls to the listed endpoints at runtime.

### New rule to add under `## Behavior Rules`
> **7. Ingen datahämtning via verktyg** – Använd **inga** verktygsanrop för att hämta data från API-endpoints ( `/api/runs`, `/api/blueprints`, `/api/stats`, `/api/status` ). All datahämtning ska utföras av JavaScript-koden **inuti** den genererade HTML-filen. Skapa alltså filen **direkt** utan föregående API-anrop, och inkludera inline JS som anropar rätt endpoint.  

This makes it explicit that the agent must **never** use tools to fetch API data, breaking the infinite-tool loop entirely.

Optionally, remove or simplify rule 6 to avoid confusion.

## Version Bump
- Recommended new version: **1.0.2** (patch bump) – this is a targeted improvement on top of the previous fix.