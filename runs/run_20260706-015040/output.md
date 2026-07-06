Fil skapad: `/Users/oskarsellgren/projects/forge/dashboard.html`

**Dashboard UI Builder – leverans klar.**

## Sammanfattning

En komplett HTML-fil (inline CSS/JS) som uppfyller alla krav:

### Vyer & datakällor

| Vy | API-endpoint | Innehåll |
|---|---|---|
| **Stats-rad** | `/api/stats` | Aktiva runs, totala runs, genomsnittlig score, agenter online |
| **Aktiva Runs** | `/api/runs` | Lista med status-dot, badge, score, blueprint, tid |
| **Score-historik** | `/api/blueprints` | Stapeldiagram per blueprint med tooltip och snitt |
| **Agent-status** | `/api/status` | Kort med status-dot, blueprint, current run |

### Design
- Mörkt tema (`#0a0a0f`, `#16161f`, `#222233`)
- Färgkodade statusar: grön (running), gul (eval), blå (improving), röd (failed)
- Hover-effekter på kort och items
- Responsiv grid (kolumn vid <1000px)
- Anpassad scrollbar

### Beteende
- Pollar alla 4 endpoints parallellt var 5:e sekund
- Anslutningsindikator med dot (grön/gul/röd)
- Error-banner vid API-fel
- Senaste uppdateringstid
- Empty states och loading-shimmer
- Tabular-nums för siffror

Klar att användas direkt mot `localhost:8000`.