## What Went Wrong
- Agent output for `run_20260706-025008` begins with a prose introduction and a markdown code fence before the HTML — adding unnecessary characters and violating the intended compactness.
- The HTML code is truncated inside the CSS (after `.stat-card { background: #111820; border: 1px solid #1e2636`), leaving the dashboard completely non‑functional.
- Despite a judge evaluation of 10, the file is unusable; the evaluator likely did not detect the truncation, but the dashboard cannot render.

## Which Rules Were Broken
- **Output Format** – Kräver *”Kompletta HTML-filer med inline CSS och JS. En fil per vy.”* – Filen är ofullständig och saknar `</html>`.
- **Behavior Rule 8 (v1.0.5)** – *”Hela svaret får innehålla högst 35 rader och max 900 tecken”* – Högst sannolikt överskriden på grund av inledande text och överflödig CSS; dessutom krävdes en komplett avslutning med `</html>` vilket inte uppfylldes.

## Proposed Fixes
Uppdatera persona med en uttrycklig och striktare version av regel 8 samt komplettera Output Format. Följande ändringar föreslås:

**1.** Ändra **Output Format** till:  
> **Output Format**  
> Kompletta HTML-filer med inline CSS och JS. En fil per vy. **Svara enbart med HTML-koden – ingen introduktion, ingen markdown-inpackning (```html).** Svaret börjar direkt med `<!DOCTYPE html>` och slutar med `</html>`.

**2.** Ersätt **Behavior Rule 8** med följande text:  
> **8. Output-restriktioner** – Du får ENDAST svara med HTML-koden. Ingen introduktionstext, inga markdown-kodblock. Svaret börjar direkt med `<!DOCTYPE html>`. Hela filen får max innehålla **800 tecken** och **30 rader**. Använd extremt kompakt CSS: endast nödvändiga selektorer (body, .container, .runs, .run, .status, h1), inga media queries, inga animationer utom en enkel status-puls. JavaScriptet måste vara minimalt: använd `fetch` var 5:e sekund, rendera en enkel HTML‑ström med runs‑lista och en stat‑summarad. **Om du riskerar att överskrida gränsen, ta bort överflödiga CSS‑deklarationer tills filen är komplett och avslutas med `</html>`.** Detta är ett hårt krav – filen måste vara körbar direkt.

Dessa tillägg tvingar fram en raw‑HTML‑output utan onödig overhead och sätter en lägre tecken‑/radgräns, vilket kraftigt minskar risken för trunkeringar.

## Version Bump
- Föreslagen ny version: **1.0.6** (patch) – skärper output‑kraven ytterligare för att garantera kompletta och omedelbart körbara svar.