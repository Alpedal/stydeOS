## What Went Wrong
- I run `run_20260706-020251` är HTML-filen inte komplett – den avbryts mitt i CSS-koden efter animeringen av `.dot.offline`. Därmed saknas resten av CSS:en, hela HTML-strukturen och all JavaScript. Dashboard:en är oanvändbar.
- Judge-eval ger **10 poäng**, vilket bekräftar att leveransen bröt mot kravet på en komplett vy.
- Problemet är identiskt med tidigare körning `run_20260706-020116` – den genererade koden blir för lång och trängs bort av plattformens svarstak.

## Which Rules Were Broken
- **Output Format**: ”Kompletta HTML-filer med inline CSS och JS. En fil per vy.” – Filen är avbruten och saknar både HTML och JS.
- **Behavior Rule 1** (indirekt): Agenten skulle bygga en enkel dashboard, men misslyckades med att leverera en fullständig vy.

## Proposed Fixes
Lägg till en ny regel i `## Behavior Rules` som tvingar agenten att hålla sig inom en storleksgräns och prioritera kompakthet:

> **8. Maximal filstorlek** – Den genererade HTML-filen får inte överstiga 200 rader eller ~7 KB (inklusive inline CSS och JavaScript). Håll CSS kompakt (t.ex. shorthand, inga överflödiga animationer), undvik onödiga kommentarer, och fokusera på funktionell styling framför dekorativ detaljrikedom. Om filen riskerar att bli för stor, prioritera bort icke-kritiska delar av layouten för att garantera en komplett och körbar leverans.

Detta kompletterar den tidigare ofullständiga feedbacken från `run_20260706-020116` och bör förhindra framtida trunkeringar.

## Version Bump
- Föreslagen ny version: **1.0.3** (patch – bygger vidare på 1.0.2 med en storleksbegränsning).