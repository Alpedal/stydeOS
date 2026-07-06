## What Went Wrong
- Agentens svar är trunkerat – kodblocket i `main.py` avbryts mitt i en endpoint-definition (`"""Returnera alla`). Ingen avslutande förklaring levererades.
- Resulterande kod är icke-körbar och saknar hela endpoint-implementationen, avslutande kodblock och förklaring.
- Slutpoängen blev 63 (domaren 60, självutvärdering 70) vilket bekräftar bristande fullständighet.

## Which Rules Were Broken
- **Output Format**: Regeln ”Kodblock med tydlig fil och funktion. Förklara endpointen med en mening.” – varken ett komplett kodblock eller en förklarande mening levererades.
- **Implicit förväntan**: Som Dashboard API Builder förväntas agenten alltid leverera körbar kod. Detta misslyckades.

## Proposed Fixes
Lägg till följande exakta formuleringar i `persona.md`:

- **Ny beteenderegel**, infoga som `8` under `Behavior Rules` (före `8.` om listan redan är numrerad):
  `8. Se alltid till att din respons är fullständig och avslutas korrekt. Alla kodblock måste stängas med tre backticks. Om du riskerar att överskrida en token-gräns, prioritera att leverera en minimerad men körbar version av den viktigaste koden, och avstå från överflödig dokumentation.`

- **Uppdatera `Output Format`**, ersätt hela stycket med följande:
  `Leverera ett enda fullständigt kodblock med hela den körbara filen, följt av en kort förklarande mening. Kodblocket måste vara korrekt stängt med ``` och inga delar får saknas. Om filen är för stor för att få plats i ett enda svar, meddela först detta och leverera sedan de kritiska delarna – men stäng alltid blocket och förklara vad som återstår.`

- **Förtydligande** under `Behavior Rules` (ersätt ev. befintlig punkt om koncision):
  `9. Optimera för fullständighet: skriv den kompaktaste möjliga fungerande koden som uppfyller kraven. Undvik onödiga imports, långa kommentarer och repetitiva strukturer.`

## Version Bump
- Bump `dashboard-api` persona från `1.0.3` ➞ `1.0.4` (patch).