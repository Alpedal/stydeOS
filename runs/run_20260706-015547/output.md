Jag skisserar arkitekturen i tre komponenter, med motivering för varje val.

**Övergripande plan**  
All data hämtas från Forge v2 API via en lättviktig pipeline som pollar med 5-sekunders intervall. Data lagras i en in-memory cache (ingen databas) för att minimera komplexitet. Realtidsflödet sker via Server-Sent Events (SSE) – enklare än WebSocket och tillräckligt för envägsuppdateringar. Ett REST API serverar både statisk data och SSE, och UI prenumererar på strömmen.

---

**Datapipeline**  
Varför polling? Forge v2 API har rate limits, 5-sekunders intervall är säkert och ger nära-realtid.  
In-memory cache håller koll på senaste runs, blueprint-status och aggregerad statistik. Servern uppdaterar den vid varje poll och pushar förändringar via SSE.

*Delegering* till **dashboard-data agent**:  
"Skapa en Node.js-tjänst som pollar Forge v2 API (`/runs`, `/blueprints`) var 5:e sekund. Normalisera svaren till en enhetlig datamodell (runs: id, status, blueprint, starttid, duration; blueprints: id, status, senaste run). Lagra i ett enkelt JavaScript-objekt. Exponera metoder för åtkomst: `getRuns()`, `getBlueprints()`, `getStats()`. Starta en Express SSE-server på port 4000 med endpoint `/events` som sänder ut diff-uppdateringar (nya runs, statusändringar) varje pollingcykel."

---

**API**  
Varför REST + SSE? Ger både direkt åtkomst till nuvarande data och ett push-meddelandesystem för UI.

*Delegering* till **dashboard-api agent**:  
"Bygg ett Express.js API som använder datapipelinen ovan. Implementera följande endpoints:  
- `GET /runs` – returnerar lista med alla runs  
- `GET /blueprints` – returnerar alla blueprints med status  
- `GET /stats` – returnerar aggregerad statistik (antal runs per status, genomsnittlig duration)  
- `GET /events` – SSE-endpoint som skickar uppdateringar från pipelinen  
Koppla ihop med dashboard-data genom att importera dess cache-objekt och lyssna på uppdateringar. Kör på port 3000."

---

**UI**  
Varför React? Vanligast, enkelt att integrera med SSE via `EventSource`.  
Enkel layout: en tabell över runs (sorterbar), en statusruta för blueprints, och en KPI-panel med statistik. Uppdateras per automatik när SSE-meddelanden anländer.

*Delegering* till **dashboard-ui agent**:  
"Skapa en React-app med Create React App eller Vite. Huvudkomponenter:  
- `Dashboard` – sammanhållande komponent som ansluter till `/api/events` med EventSource.  
- `RunsTable` – visar senaste runs, uppdateras vid SSE-meddelanden.  
- `BlueprintStatus` – visar varje blueprint och dess senaste run-status.  
- `StatsPanel` – visar totalt antal runs, lyckade/misslyckade, genomsnittstid.  
Använd hårdkodad mockdata i utvecklingsfasen, byt ut mot API-anrop innan färdigställande. Styla med enkel CSS (inga tunga ramverk). Kör på port 5173."