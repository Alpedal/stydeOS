## What Went Wrong
- Agentens svar trunkerades mitt i en `except`-sats; kodblocket avslutades inte och saknar helt FastAPI-appen, endpoints, routers och `if __name__ == '__main__'`.
- Inga endpoints definierades, vilket gör leveransen totalt icke‑körbar.
- Slutpoäng 25.5 (domare 30, självutvärdering 15) bekräftar grava brister i fullständighet.

## Which Rules Were Broken
- **Output Format**: ”Kodblock med tydlig fil och funktion. Förklara endpointen med en mening.” – kodblocket är ofullständigt och ingen förklaring lämnades.
- **Ev. befintlig beteenderegel om fullständighet** (t.ex. tidigare tillagd regel 8) – svaret är inte syntaktiskt korrekt eller fullständigt.
- **Underförstått krav**: Dashboard API Builder ska leverera körbar kod. Det misslyckades helt.

## Proposed Fixes
Lägg till följande exakta rader i `persona.md`:

1. **Ny beteenderegel** (infoga som nummer 8 eller nästa lediga nummer under `Behavior Rules`):
```
8. Före varje hjälpfunktion måste du skriva FastAPI‑appdefinitionen, alla fyra endpoints (med router och `app.include_router()`), samt `if __name__ == '__main__':`. Använd placeholder‑kroppar (`return {}` eller `pass`) för att garantera att filen är körbar. Om du närmar dig token‑gränsen, stoppa all övrig text och leverera denna minimala struktur – med stängt kodblock.
```

2. **Uppdatera `Output Format`**, ersätt stycket med:
```
Output Format:
Ett enda fullständigt, körbart kodblock med hela filen. Kodblocket ska alltid börja med app‑skapandet och sluta med stängande ```. Efter blocket: en kort förklarande mening. Om utrymmet inte räcker, prioritera att inkludera app‑struktur, endpoints och main‑sats; förklara då vilka hjälpfunktioner som utelämnats.
```

3. **Förtydligande** under `Behavior Rules` (lägg till eller ersätt befintlig regel om koncision):
```
9. Du får offra dokumentation och hjälpfunktioner, men aldrig app‑strukturen. En fullständig, körbar minimalfil är alltid viktigare än kommentarer, pydantiska modeller i detalj eller fullt implementerade hjälpmetoder.
```

## Version Bump
- Bump `dashboard-api` från nuvarande version (troligen 1.0.4) → **1.0.5** (patch).