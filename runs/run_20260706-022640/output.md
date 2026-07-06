**Testfall för Forge Command Center**  
Fokus: API, UI, datapipeline. Varje test är en isolerad kontroll med PASS/FAIL-logik.

---

### 1. API – hälsoendpoint
```
Test: GET /health → PASS om status 200 och JSON med "status":"ok".
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health
  Kör: curl -s http://localhost:8000/health | jq .
  Förväntat: {"status":"ok","version":"1.0"}
  FAIL om annan status eller felaktig nyckel.
```

### 2. API – lista pipelines
```
Test: GET /pipelines → PASS om JSON-array med minst en pipeline.
  curl -s http://localhost:8000/pipelines | jq type
  Förväntat: "array" och varje objekt har fälten "id", "name", "status".
  FAIL om tom array (om förväntad data) eller saknade fält.
```

### 3. API – pipeline-statistik
```
Test: GET /pipelines/{id}/stats → PASS om JSON med fälten "total_runs", "success_rate", "avg_duration".
  Hämta först ett id från /pipelines.
  curl -s http://localhost:8000/pipelines/1/stats | jq .
  Förväntat: success_rate är float 0–100, avg_duration i sekunder.
  FAIL om nycklar saknas eller datatyper fel.
```

### 4. API – felhantering
```
Test: GET /nonexistent → PASS om status 404 och JSON med "detail".
  curl -s -w "\n%{http_code}" http://localhost:8000/nonexistent
  Förväntat: HTTP 404, JSON har nyckel "detail".
  FAIL om 500 eller annan response.
```

### 5. UI – laddning utan JS-fel
```
Test: Ladda index.html i headless browser (Puppeteer/Playwright) → PASS om console.errors = 0.
  Pseudokod:
    page.goto('http://localhost:8000')
    const errors = await page.evaluate(() => window.__jsErrors || [])
  Förväntat: inga fel, sidans DOM innehåller huvudkomponenter (#dashboard, #metrics).
  FAIL om något JS-fel eller saknade element.
```

### 6. UI – API-data synlig
```
Test: Efter laddning, kontrollera att dashboard visar data från API.
  page.waitForSelector('#pipeline-table tr')
  const rows = await page.$$('#pipeline-table tr')
  PASS om rows.length > 1 (header + data).
  FAIL om tabellen är tom (ingen data eller API-fel tyst).
```

### 7. Datapipeline – statistikproduktion
```
Test: Kör pipeline-modul med mockad indata → kontrollera utdata.
  Exempel: python -m forge.pipeline --input test/fixtures/raw.json --output /tmp/out.json
  Läs /tmp/out.json, jämför med förväntad struktur:
    {"total_events": 100, "errors": 2, "avg_latency_ms": 45.3, "percentiles": {"p50": 30, "p95": 120}}
  PASS om alla nycklar existerar och typer stämmer (int, float, dict).
  FAIL om avvikelse i nycklar eller typer.
```

### 8. Datapipeline – tom indata
```
Test: Kör pipeline med tom fil ([]) → returnera tom statistik utan crash.
  echo '[]' > /tmp/empty.json
  python forge/pipeline.py --input /tmp/empty.json --output /tmp/out2.json
  cat /tmp/out2.json | jq .
  Förväntat: {"total_events":0, "errors":0, "avg_latency_ms":null} (eller 0)
  FAIL om script kastar exception eller producerar ogiltig JSON.
```

### 9. Integration – API data = pipeline data
```
Test: Kör pipeline manuellt, lagra resultat i databas. Hämta via API och jämför.
  1. python forge/pipeline.py --input data/latest.json --db
  2. curl http://localhost:8000/pipelines/1/stats > api_stats.json
  3. diff <(jq '.total_events' api_stats.json) <(echo 100)
  PASS om statistiken matchar.
  FAIL om diskrepans (tyder på trasig pipeline->API-länk).
```

### 10. Felhantering – API svarar inte
```
Test: Stoppa servern (kill uvicorn), gör GET /health → timeout eller connection refused.
  timeout 3 curl http://localhost:8000/health 2>&1 || true
  PASS om curl returnerar exit code 7 (connection refused) eller timeoutmeddelande.
  FAIL om servern fortfarande svarar (bör ha stoppats).
```

Alla testfall kan automatiseras i ett script (bash, Python, eller testramverk). Resultat loggas som PASS/FAIL med specifik orsak.