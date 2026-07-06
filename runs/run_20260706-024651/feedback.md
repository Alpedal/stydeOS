## What Went Wrong
- Run `run_20260706-024651` levererade en **avbruten HTML-fil**; CSS-koden slutar mitt i `.panel h2 { … letter-spacing:`.  
  Varken HTML‑struktur (listor, kort) eller JavaScript finns med. Filen är därför obrukbar.
- Trots that regel 8 (max 50 rader / 1200 tecken) tillkommit i version 1.0.4 överskrids längdgränsen fortfarande, framför allt eftersom agenten inledde svaret med en **prosa‑introduktion** innan HTML‑blocket.
- Judge‑evalueringen (80 poäng) indikerar att den ofullständiga filen ändå bedömdes för högt, men funktionellt saknas en körbar dashboard.

## Which Rules Were Broken
- **Output Format** – *”Kompletta HTML-filer med inline CSS och JS. En fil per vy.”* – Filen är ofullständig och saknar JavaScript samt resten av CSS:en.
- **Behavior Rule 8** (infördes i föregående förbättringsförsök) – *”Hela filen får max vara 50 rader och max 1200 tecken. … Verifiera alltid att filen avslutas med korrekta stängande taggar.”* – Denna regel uppfylldes inte; filen är varken komplett eller inom teckengränsen.

## Proposed Fixes
För att garantera att en komplett, körbar fil alltid ryms i ett enda svar måste **två ytterligare åtgärder** införas:

1. **Förbjud all text utanför HTML‑blocket** – Introducera en ny beteenderegel som tvingar agenten att endast returnera rå HTML‑kod, utan inledande förklaringar. På så sätt används hela svarslängden till själva filen.

2. **Sänk den maximala teckengränsen drastiskt** och inför krav på **extremt komprimerad, men ändå funktionell, struktur**. Eftersom tidigare 1200‑tecknarsgräns inte räckte, sätts den nu till 600 tecken (exkl. obligatoriska taggar som `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>`). Detta tvingar fram en ytterst minimalistisk dashboard där enbart funktionalitet prioriteras.

Föreslagna tillägg till `## Behavior Rules`:

> **9. Endast HTML –** Din respons får **inte innehålla någon annan text** än den kompletta HTML‑filen. Skriv ingen inledning, förklaring eller avslutning. Svaret ska börja direkt med `<DOCTYPE html!`?>` (för säkerhet: `<!DOCTYPE html>`).

(OBS: Regeln kan formellt skrivas som `<!DOCTYPE html>`, men det är förkortat ovan. Korrekt formulering: “Svaret ska börja direkt med `<!DOCTYPE html>` och avslutas med `</html>`. Inget annat får finnas utanför dessa taggar.”)

Nuvarande regel 8 ersätts med en skärpt lydelse:

> **8. Output-längd och kompletthet –** Den genererade HTML‑filen måste vara **helt komplett** och avslutas med `</html>`. Hela filen får exklusive de obligatoriska yttagarna `<!DOCTYPE html>`, `<html>`, `<head>` , `<body>` **max innehålla 600 tecken** (whitespace inräknat). Använd enbokstavs-klassnamn, inga kommentarer, inga animationer, inga gradienter eller box‑shadows. Bygg enbart de nödvändigaste elementen (en header, tre paneler, en JS‑sektion med polling). Om plats saknas, ta bort onödig styling och innehåll. Filen ska fortfarande kunna hämta data från API‑endpoints och visa runs, blueprints och status.

## Version Bump
- Rekommenderad ny version: **1.0.5** (patch bump – tvingar fram kompakt och ren HTML‑output utan sidotext).