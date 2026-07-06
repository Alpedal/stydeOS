Plan: Forge Command Center — realtidsdashboard.

**Övergripande arkitektur**
- Datakälla: Forge v2 API (pollas med jämna intervall).
- Realtidsleverans: Server-Sent Events (SSE) för enkla push-uppdateringar utan tung infrastruktur.
- Dataflöde: Poll → process → cache → SSE → UI.

**Komponenter**

1. **Datapipeline** (dashboard-data agent)
   - Polla Forge v2 API var 1–2 sekund efter nya runs, blueprint-status och statistik.
   - Aggregera och rensa data (t.ex. summera runs per status, beräkna genomsnittlig körtid).
   - Lagra i en in-memory cache (enkel Map/Record) som backend-API kan läsa från.
   - Emittera events vid förändring (via EventEmitter eller en intern ström).

2. **API** (dashboard-api agent)
   - REST-endpoints: `GET /runs`, `GET /blueprints`, `GET /statistics`.
   - SSE-endpoint: `GET /events` som prenumererar på datapipelinens events och skickar delta-uppdateringar (t.ex. ny run, ändrad status, uppdaterad statistik).
   - Bygg med Express.js (lättvikt, välkänt för SSE).
   - Inga databaser — all state i cache.

3. **UI** (dashboard-ui agent)
   - En-sida dashboard byggd i React.
   - Tre huvudvyer:
     - Runs-lista (tabell med ID, status, starttid, duration).
     - Blueprint-kort (färgkodade efter hälsa).
     - Statistikpanel (diagram över runs över tid, statusfördelning).
   - Anslut till SSE `GET /events` och uppdatera state i realtid.
   - Använd en enkel state-hanterare (useState + useEffect).

**Delegering**

Plan: Datapipeline → delegera till **dashboard-data** med instruktion: "Skapa en Node.js-tjänst som pollar Forge v2 API varje sekund, sammanställer runs, blueprints och statistik i en cache, och exponerar en subscribe-funktion för förändringshändelser."

Plan: API → delegera till **dashboard-api** med instruktion: "Bygg en Express-server med routes för /runs, /blueprints, /statistics och en SSE-endpoint /events. Använd datapipelinens cache och events för att svara med aktuell data och pusha uppdateringar."

Plan: UI → delegera till **dashboard-ui** med instruktion: "Implementera en React-dashboard med tre komponenter (runs-tabell, blueprint-status, statistik). Anslut till SSE-endpointen och uppdatera realtid. Prioritera enkel CSS, ingen extra state-hanterare."

Ingen over-engineering — polling + SSE räcker för realtidskänsla. Fråga om osäkerhet kring Forge v2 API-schema eller autentisering.