## Plan: Forge Command Center — Arkitekturöversikt

**Mål:** Ett realtidsdashboard som visar alla Forge-runs, blueprint-status och statistik.  
**Prioritering:** Enkel, robust, minimal latens. Inga onödiga abstraktioner.

---

### 1. API-lager
Delegera till **dashboard-api agent**:  
Skapa ett Node.js/Express-API med två vägar:  
- **REST** för initial data och historik (`GET /api/runs`, `GET /api/blueprints`, `GET /api/stats`)  
- **WebSocket** (`ws://server/socket`) för strömmande uppdateringar var 5:e sekund  
Motivering: REST ger enkel initial rendering, WebSocket minimerar polling för realtid.  
Anslut till Forge v2 API med en intern adapterklass som översätter datamodeller.

---

### 2. UI-lager
Delegera till **dashboard-ui agent**:  
Bygg en React SPA med tre huvudkomponenter:  
- `RunTable` – tabell över aktiva/avslutade runs, sorterbar  
- `BlueprintStatusCards` – statuskort per blueprint (grön/gul/röd) med förklaring  
- `StatsPanel` – statistik: totalt antal runs, genomsnittlig duration, felfrekvens  
WebSocket-anslutning i en `useDashboardSocket`-hook som synkar Redux/TanStack Query store.  
Motivering: Component-baserad arkitektur gör det lätt att lägga till nya vyer. En hook isolerar socket-logik.

---

### 3. Datapipeline
Delegera till **dashboard-data agent**:  
Implementera en lättviktsaggregeringsfunktion:  
- Hämta senaste runs från Forge API (limit 200).  
- Beräkna statistik (snittduration, statusfördelning) i minnet.  
- Cacha resultat i en in-memory-map, uppdatera var 5:e sekund.  
- Skicka delta-uppdateringar (endast ändrade poster) via WebSocket till API-servern.  
Motivering: Aggregerar på serversidan för att minska last på Forge API och hålla UI responsivt. Caching undviker onödiga anrop.

---

### Övergripande flöde
1. Användaren öppnar dashboard → UI anropar REST för initial tillstånd.  
2. Datapipeline startar en interval-loop: polla Forge API → aggregera → pusha via WebSocket.  
3. API-servern vidarebefordrar delta-uppdateringar till alla anslutna klienter.  
4. UI uppdaterar lokalt store och renderar ändringar utan full reload.

**Ingen överengineering:** En server (Express) hostar både API och statisk React-build. WebSocket och REST delar samma port. Datapipeline körs i samma process. Vid hög belastning kan pipeline skalas ut separat, men initialt räcker detta.