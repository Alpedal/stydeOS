## What Went Wrong
- Agentens output för run_20260706-021406 är avbruten mitt i CSS-koden (efter `.stat-card .value {`). HTML-strukturen och JavaScript saknas helt.
- Dashboarden är oanvändbar – bekräftas av judge-eval: 5 poäng.
- Problemet är identiskt med tidigare körningar: filen blir för lång och klipps av plattformens svarstak.

## Which Rules Were Broken
- **Output Format** – Kravet *”Kompletta HTML-filer med inline CSS och JS. En fil per vy.”* uppfylls inte då filen är ofullständig.
- **Behavior Rule 1** (indirekt) – Agenten skulle skapa en enkel, fungerande dashboard men misslyckades med att leverera en körbar fil.

## Proposed Fixes
Lägg till en ny beteenderegel under `## Behavior Rules` som tvingar fram en komplett och kompakt fil:

> **8. Output-längd** – Hela HTML-filen måste rymmas i ett enda svar och vara körbar. Håll designen extremt minimalistisk: max 200 rader totalt. Använd shorthand-CSS, minimera antalet selektorer, undvik överflödiga animationer och dekorativa element. Fokusera på funktion: polling var 5:e sekund, statusvisning, nyckeltal. Om layouten riskerar att överskrida gränsen, prioritera bort icke‑kritiska detaljer. Verifiera alltid att filen avslutas med korrekta stängande taggar.

Detta kompletterar tidigare feedback och förhindrar framtida trunkeringar.

## Version Bump
- Föreslagen ny version: **1.0.3** (patch – bygger vidare på tidigare förbättringar med en uttrycklig längdbegränsning).