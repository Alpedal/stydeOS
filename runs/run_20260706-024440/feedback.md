## What Went Wrong
- Agentens kodblock trunkerades mitt i en endpoint (`async def list_ru`), saknar stängande ```, ingen körbar app, inga ytterligare endpoints eller `if __name__ == '__main__'`.
- Samma tokenbrist som tidigare orsakade att många hjälpfunktioner och Pydantic-modeller fyllde utrymmet innan det kritiska delarna hann slutföras.
- Slutresultat: slutpoäng 28.5 (själv: 25, domare: 30) – långt under godkänt.

## Which Rules Were Broken
- **Output Format** (”Kodblock med tydlig fil och funktion. Förklara endpointen med en mening.”) – inget komplett block, ingen förklaring.
- **Underförstått krav på körbarhet** – leveransen kan inte startas, ingen `app`-instans exporterad.
- Eventuell tidigare införd regel om att inleda med skeletons (app + alla endpoints + main) ignorerades; agenten definierade först hjälpfunktioner och modeller.

## Proposed Fixes
1. Lägg till en ny beteenderegel (ersätter eller kompletterar tidigare, efter nummer 9):
   ```
   10. **Absolut minimal stomme först**: Innan du definierar någon hjälpfunktion eller Pydantic-modell, skriv hela den körbara stommen i högst 10 rader:
       ```python
       from fastapi import FastAPI
       import os, json, pathlib
       app = FastAPI()
       @app.get("/api/status")
       def status(): return {"status":"ok"}
       @app.get("/api/runs")
       def runs(): return []
       @app.get("/api/blueprints")
       def blueprints(): return []
       @app.get("/api/health")
       def health(): return {"healthy":True}
       if __name__ == "__main__": import uvicorn; uvicorn.run(app, host="0.0.0.0", port=8000)
       ```
       Ditt kodblock måste alltid börja med denna stomme och sedan omedelbart stängas med ```. Därefter kan du förklara vad som saknas. Om du vill utöka, utöka maximalt till 15 rader totalt.
   ```

2. Förtydliga regeln om Pydantic i **Behavior Rules** (modifiera befintlig punkt 3):
   ```
   3. Validera all input med Pydantic **endast för POST/PUT-endpoints med request body**. GET-endpoints ska returnera dict direkt – inga Pydantic-modeller för responser. För samtliga endpoints i den här bluprinten (alla är GET) ska Pydantic inte användas alls.
   ```

3. Lägg till en rad högst upp i persona, efter rubriken och före role:
   ```
   ⚠️ VIKTIGT: Systemets teckenbudget är mycket begränsad. Din leverans måste vara extremt kort (max 20 rader Python). Prioritera att leverera ett avslutat, körbart block framför pedantisk struktur. Om du tvekar, använd stommen från regel 10 och avsluta omedelbart.
   ```

## Version Bump
- Bump `dashboard-api` persona från `1.0.5` → `1.0.6` (patch).