Test: API health endpoint → PASS  
  curl localhost:8000/health returnerar 200 och {"status":"ok"}

Test: API dashboard summary → PASS  
  GET /api/v1/dashboard/summary ger 200 med fälten widgets, total_metrics, last_updated

Test: API metrics list → PASS  
  GET /api/v1/metrics returnerar JSON-array med minst en post och korrekt schema (id, name, value)

Test: API 404-hantering → PASS  
  GET /nonexistent returnerar 404 med JSON som innehåller "detail" och status_code

Test: UI index.html → PASS  
  curl -s localhost:8000/ | head -1 innehåller "<!DOCTYPE html>" och status 200

Test: UI JavaScript-resurser → PASS  
  Alla script-taggar i index.html pekar på filer som returnerar 200 (testas med curl på varje src)

Test: UI laddning utan JS-fel → PASS  
  headless Chrome (puppeteer) laddar sidan; console.log visar inga error-meddelanden

Test: Pipeline generering → PASS  
  python pipeline/run.py --input testdata.csv genererar output.json med nycklarna "total", "average", "count"

Test: Pipeline statistik korrekthet → PASS  
  Verifiering: summan av numeriska fält i testdata matchar total i output.json (felmarginal < 0.01)

Test: Pipeline felhantering → PASS  
  Körning med saknad input returnerar exit code 1 och skriver felmeddelande till stderr