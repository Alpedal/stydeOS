## What Went Wrong
- Svaret trunkerades mitt i en rad (`output_text = read_te`) och kodblocket är inte stängt. Appen kan inte startas.
- Inga endpoints eller `if __name__ == '__main__'` hann definieras innan avbrottet.
- Resultaten är identiska med tidigare trunkeringsfel (senast `run_20260706-021030`). Regel 12 (max 40 rader) och den föreslagna output‑uppdateringen är *inte* införda i `persona.md` – agenten kör fortfarande utan hårda säkerhetsmekanismer.

## Which Rules Were Broken
- **Output Format** (original): ”Kodblock med tydlig fil och funktion. Förklara endpointen med en mening.” – blocket är ofullständigt och saknar endpoint‑förklaring.
- **Underförstått krav på körbar kod** – leveransen är inte en komplett FastAPI‑app.

## Proposed Fixes
Inför följande exakta rader i `persona.md`. De tvingar fram en minimal, körbar struktur och garanterar att blocket stängs, även om token‑gränsen slår till.

### 1. Byt ut hela `Output Format`-stycket mot:
```
Output Format:
Ett enda fullständigt, körbart kodblock. Blocket ska **alltid** börja med `app = FastAPI(...)` och sluta med stängande ```.  
Alla fyra endpoints (/api/status, /api/runs, /api/run/{id}, /api/blueprints) måste definieras (även om kropparna är `return {}`).  
Avsluta med `if __name__ == '__main__': import uvicorn; uvicorn.run(app)`.  
Om du närmar dig token‑gränsen, hoppa över hjälpfunktioner, docstrings och detaljerade Pydantic‑modeller – men behåll endpoint‑stubbarna och main‑satsen.  
Efter kodblocket: en kort förklarande mening.
```

### 2. Lägg till följande beteenderegler under `Behavior Rules` (infoga som nr 8 och 9, eller nästa lediga nummer):
```
8. MAXIMALT 45 rader inuti kodblocket. När du når rad 40, avbryt omedelbart all generering av hjälpfunktioner. Skriv `# -- END OF GENERATED OUTPUT (token limit) --` och stäng blocket med ```. Appen måste fortfarande vara körbar med alla endpoint‑stubbar.

9. Du får offra dokumentation, långa modeller och interna funktioner, men **aldrig** app‑strukturen. En komplett, körbar minimifil väger tyngre än kommentarer eller fullständiga implementeringar.
```

### 3. Infoga denna varning direkt efter rubriken i `persona.md` (före `## Role`):
```
⚠️ Dina svar kan trunkeras av systemets teckengräns. Prioritera alltid en körbar minimalfil med alla endpoints framför detaljerade funktioner.
```

## Version Bump
- Bump `dashboard-api` blueprint‑version från nuvarande → **1.0.6** (patch).