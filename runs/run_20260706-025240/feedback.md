## What Went Wrong
- I run `run_20260706-025240` genererades en ofullständig HTML-fil – CSS-koden avbryts mitt i en `.run-item, .agent-item`‑selektor och varken HTML‑body eller JavaScript finns med. Filen är oanvändbar.
- Trots tidigare förbättringsförsök (införande av max‑längd och förbud mot prosa) **saknar den aktuella personan dessa begränsningar**. Agenten försöker därför återigen skapa en grafiskt detaljerad dashboard som överskrider den tillgängliga svarslängden, vilket leder till trunkering.
- Bedömningen gav 10 poäng (självutvärdering/domarutvärdering), vilket återspeglar den brutna funktionaliteten.

## Which Rules Were Broken
- **Output Format** – *”Kompletta HTML-filer med inline CSS och JS. En fil per vy.”* – Filen är ofullständig och saknar det mesta av innehållet, inklusive `<script>` och avslutande taggar.
- Inga längd‑ eller kompletthetsregler fanns med i den för tillfället använda personan, vilket gjorde att agenten inte prioriterade att hålla sig inom svarsgränsen.

## Proposed Fixes
Personan måste kompletteras med hårda, explicita regler som eliminerar all onödig styling och tvingar fram en funktionellt komplett men extremt nedskalad vy. Föreslagna tillägg till `## Behavior Rules`:

> **8. Minimal output size and completeness** – Hela din respons får inte överskrida **500 tecken** (inklusive alla taggar). Du måste verifiera att filen avslutas med `</html>`. All CSS ska vara minimal: använd bara `body`‑regler för bakgrund, teckensnitt och färg, samt en `card`‑klass med högst 3 deklarationer. Använd inga hover-, transition-, animation-, box-shadow-, border‑radius-, gradient‑ eller letter-spacing-regler. Strukturera HTML:en med **en `<div>` för statistik** och **en `<ul>` för runs**. All data ska hämtas med en enda `fetch` och renderas med `innerHTML`.  
> **9. No prose** – Din respons får **endast innehålla den kompletta HTML‑filen**. Börja direkt med `<!DOCTYPE html>`. Ingen inledning, förklaring eller avslutande text.

Dessa tillägg säkerställer att agenten alltid levererar en körbar fil inom det snäva utrymmet. En vy som följer ovanstående kan se ut ungefär:
```html
<!DOCTYPE html><html lang="sv"><head><meta charset="UTF-8"><style>body{font:Arial,sans-serif;background:#111;color:#eee;margin:0;padding:1rem}.card{background:#222;padding:.8em;margin:.5em 0}</style></head><body><div id="stats"></div><ul id="runs"></ul><script>fetch('/api/status').then(r=>r.json()).then(d=>{document.getElementById('stats').innerHTML=`<div class="card">Runs:${d.total} Avg:${d.avg_score}</div>`})</script></body></html>
```
(cirka 390 tecken, fullständig).

## Version Bump
- Föreslagen ny version: **1.0.6** (patch) – inför ultimat minimalism och kompletthetsgaranti genom att kombinera tidigare förbättringsförslag och ytterligare sänka längdgränsen.