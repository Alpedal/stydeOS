## What Went Wrong
- Agentens slutgiltiga svar innehöll ett ofullständigt, avbrutet kodblock (`if run.e` följt av inget mer) och avslutades utan stängande kodblocksmarkör och förklaring.
- Slutpoängen landade på 39.5 (domare 35, självutvärdering 50), vilket bekräftar att leveransen är icke‑körbar.
- Problemet är identiskt med tidigare trunkeringsfel (run_20260706-015647 och run_20260706-015807), trots införandet av regler som kräver fullständighet.

## Which Rules Were Broken
- **Output Format**: ”Kodblock med tydlig fil och funktion. Förklara endpointen med en mening.” – kodblocket var ofullständigt och ingen förklaring lämnades.
- **Beteenderegel 5** (befintlig): ”Avsluta alltid ditt svar med en tydlig kod och en förklaring…” – uppfylldes inte.
- **Beteenderegel 7** (tillagd tidigare): ”Ditt slutgiltiga svar måste innehålla ett kodblock som är syntaktiskt korrekt och fullständigt…” – trunkerat kodblock, ej körbart.
- Underförstått: Koden måste vara körbar för att uppfylla uppdraget.

## Proposed Fixes
Lägg till följande exakta rader i `persona.md` under `Behavior Rules` (ny punkt 8):

```
8. Kodblock som riskerar att bli för långa för ett enda svar måste komprimeras till en minimal, körbar version. Prioritera att definiera alla fyra endpoints med fungerande `app.include_router()` och `if __name__ == '__main__':`. Hjälpfunktioner (t.ex. `get_all_runs`, `load_json`) får innehålla ett `pass` eller returnera tomma listor – det viktiga är att all infrastruktur finns. Förklara i texten vad som utelämnats.
```

Förtydliga `Output Format` ytterligare:

```
Output Format:
- Kodblock med tydlig fil och funktion. 
- Kodblocket måste vara komplett och körbart – det ska innehålla minst en fungerande app-struktur och avslutas med en stängande ```.
- Förklara endpointen med en mening.
- Om fullständig kod inte får plats, leverera den minimala struktur med alla endpoints och notera utelämnade delar.
```

## Version Bump
- Bump `dashboard-api` persona från `1.0.3` → `1.0.4` (patch).