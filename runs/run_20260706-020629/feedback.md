## What Went Wrong
- Agentens svar trunkeras åter mitt i ett kodblock. I `main.py` avbryts utdata efter `bp_dir = Path(FORGE_ROOT) / "bluepri` – mitt i ett funktionsnamn.
- Ingen förklaring, inget avslutande ```.
- Slutpoäng: 20.5 (självutvärdering 10, domare 25). Detta är identiskt med tidigare trunkeringsfel (run 20260706-015647, 20260706-015807 och 20260706-015933).

## Which Rules Were Broken
- **Output Format**: Regeln ”Kodblock med tydlig fil och funktion. Förklara endpointen med en mening.” – blocket är inte komplett och förklaring saknas.
- Underförstått krav på körbar kod bryts.
- Orsaken är att agenten skriver för mycket kod (t.ex. Pydantic-klasser för både `Run`, `Blueprint`, `Stats`, `StatusResponse` och funktioner för att läsa alla JSON-filer) tills utrymmet tar slut.

## Proposed Fixes
Lägg till följande exakta rader i `persona.md`:

### Ny beteenderegel (punkt 10 under Behavior Rules)
```
10. Om du når någon form av teckengräns måste du avsluta kodblocket omedelbart efter den senaste fullständiga funktionen/endpointen. 
    Lägg till en kommentsats `# END – ytterligare endpoints utelämnade p.g.a. utrymmesbrist` på sista raden.
    Prioritera alltid att leverera en **körbar app** med minst `/api/status` och `/api/runs`.
```
### Ändring i Output Format
Ersätt befintlig paragraf med:
```
Leverera ett **enda fullständigt och körbart kodblock** följt av en kort förklaring. 
Om hela API-definitionen inte får plats, leverera en delmängd med de viktigaste endpoints och stäng blocket med ```. 
Ange då tydligt vilka endpoints som utelämnats. Block som avbryts mitt i en rad eller funktion räknas som fel.
```

### Förtydligande i Behavior Rules för minskad längd
Lägg till punkt 11:
```
11. Inga inledande kommentarer som listar endpoints. Börja med imports och minimala datamodeller. 
    Ta endast med Pydantic-klasser för de endpoints du faktiskt implementerar. 
    Docstrings får vara max en rad. Undvik explicita type hints om de inte krävs för att koden ska fungera.
```

## Version Bump
- Bump `dashboard-api` persona från `1.0.4` ➞ `1.0.5` (patch).