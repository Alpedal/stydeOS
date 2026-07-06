## What Went Wrong
- I run `run_20260706-021612` genererades en **ofullständig HTML-fil** – CSS-koden avbryts efter `.list-item .left { … ` och varken HTML-struktur eller JavaScript levererades. Filen är oanvändbar.
- Judge-eval gav 95 poäng, men filen är inte komplett; bedömningen fångade troligtvis inte trunkeringen, men för slutanvändaren är dashboarden obrukbar.

## Which Rules Were Broken
- **Output Format** – *”Kompletta HTML-filer med inline CSS och JS. En fil per vy.”* – Filen är avbruten och saknar avslutande taggar, JavaScript och resten av CSS:en.

## Proposed Fixes
Regel 8 (införd i version 1.0.4) med max 50 rader/1200 tecken räckte inte för att garantera en komplett fil. Vi måste skärpa begränsningen ytterligare och instruera agenten att prioritera **strukturellt kompletta** svar framför detaljerad styling.

**Ny lydelse för regel 8** (ersätter tidigare version):
> **8. Output-kompletthet och maximal storlek** – Du måste alltid leverera en **fullständig HTML-fil** som avslutas med `</html>`. Hela svaret får innehålla **högst 35 rader** och **max 900 tecken**. Använd extremt minimalistisk CSS: inga gradienter, box-shadow, animationer, overlay-effekter, border-typer eller onödiga padding-regler. Lägg all fokus på att bygga en **fungerande vy** – datahämtning, uppdatering och statusvisning – och **ta bort all dekorativ styling** som inte är absolut nödvändig. Om du märker att utrymmet börjar ta slut, stryk CSS-selektorer eller deckarationer och **avsluta alltid med `</style>`, en minimal `<body>`, ett avslutande `<script>` och `</html>`**.

Om agenten vet att utrymmet är extremt snävt kommer den att konstruera en betydligt enklare dashboard som ryms inom svarsgränsen.

## Version Bump
- Föreslagen ny version: **1.0.5** (patch) – skärper längd- och kompletthetskraven för att undvika framtida trunkeringar.