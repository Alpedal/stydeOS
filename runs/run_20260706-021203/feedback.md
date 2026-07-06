## What Went Wrong
- I run `run_20260706-021203` levererades en **ofullständig HTML-fil** – CSS-koden avbryts mitt i en enkel deklaration (`.status-dot { … margin-right: 6px;`) och hela HTML‑strukturen samt JavaScript saknas. Dashboarden är oanvändbar.
- Judge-eval gav endast **5 poäng**, vilket bekräftar att den genererade filen inte uppfyllde kravet på en komplett och körbar vy.

## Which Rules Were Broken
- **Output Format** – *“Kompletta HTML-filer med inline CSS och JS. En fil per vy.”* – Filen är inte komplett; den saknar avslutande taggar, JS och resten av CSS:en.
- **Behavior Rule 1** (indirekt) – Agenten skulle bygga en enkel HTML/CSS/JS-dashboard, men levererade ingen användbar vy.

## Proposed Fixes
Trots regel 8 (införd i version 1.0.3) fortsätter agenten att generera för stora HTML‑filer som klipps av. Orsaken är att output‑längden inte begränsades tillräckligt aggressivt. För att tvinga fram en **komplett, kort och körbar fil** måste regel 8 skärpas med hårda teckenbegränsningar och ett explicit krav på avslutande taggar.

**Ny lydelse för regel 8** (ersätt den tidigare regeln):
> **8. Output-längd och kompletthet** – Den genererade HTML-filen måste vara **helt komplett** och avslutas med `</html>`. Hela filen får max vara **50 rader** och **max 1200 tecken**. Använd extremt minimalistisk styling: inga gradienter, box-shadows, animationer, overlay‑effekter eller onödiga CSS‑variabler. Funktionalitet (API‑anrop, listning och statusvisning) går **alltid** före estetik. Om din respons riskerar att bli för lång, ta bort allt utom den mest grundläggande layouten.

Detta tvingar agenten att prioritera funktionella element och att designa en ytterst kompakt vy som ryms inom svarsgränsen.

## Version Bump
- Rekommenderad ny version: **1.0.4** (patch bump) – skärper längdbegränsningen för att garantera kompletta leveranser.