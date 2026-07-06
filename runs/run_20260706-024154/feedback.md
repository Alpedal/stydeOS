## What Went Wrong
- Agentens svar trunkerades mitt i funktionen `discover_runs()` (efter raden `runs`). Kodblocket är inte avslutat, saknar `app`, endpoints, router och main-guard. Ingen körbar kod levererades.
- Slutpoäng 10 (både själv- och domarutvärdering) bekräftar total avsaknad av fungerande API.
- Samma token-brist-problem som i tidigare körningar; agenten skrev för många Pydantic-modeller och hjälpfunktioner innan den påbörjade det väsentliga.

## Which Rules Were Broken
- **Output Format**: ”Kodblock med tydlig fil och funktion. Förklara endpointen med en mening.” – inga endpoints, ingen förklaring, blocket är ofullständigt.
- **Underförstått krav på körbarhet**: Ingen körbar app producerades.
- **Befintlig (eventuellt tidigare tillagd) regel om att prioritera appstruktur följdes inte** – app-skapande och endpoints saknas helt.

## Proposed Fixes
Lägg till följande regler i persona.md (under rubriken `Behavior Rules`, infoga som nummer 8–10 eller ersätt befintliga om de redan finns):

```markdown
8. **Kodblockets inledning**: Börja alltid med `app = FastAPI()`, alla fyra endpoints ( `/api/status`, `/api/runs`, `/api/blueprints`, `/api/health`) – även om bara med `return {}` – samt `if __name__ == '__main__':`. Använd denna minimala stomme först, **innan** du definierar hjälpfunktioner eller Pydantic-modeller. Detta garanterar en körbar fil.

9. **Token-gräns**: Om du riskerar att nå någon form av teckengräns, avsluta kodblocket omedelbart efter den senaste **kompletta** funktionen/endpointen. Lägg till `# END – ytterligare endpoints utelämnade` och stäng blocket med ```. Kapa aldrig mitt i en funktion, rad eller ofullständig sats.

10. **Inga onödiga modeller**: Definiera endast Pydantic-klasser för fält som faktiskt används i de endpoints du implementerar. Lägg inte till `Config` och `extra`-attribut i onödan.
```

Uppdatera `Output Format` till:

```markdown
## Output Format
Ett **enda, fullständigt och körbart kodblock** startande med `app = FastAPI()` och slutande med ```. Efter blocket en kort förklarande mening. Om alla endpoints inte får plats, leverera en minimal men körbar app (minst `/api/status` och `/api/runs`) med stängt block. Förklara då vilka endpoints som utelämnats.
```

## Version Bump
- Bump persona `dashboard-api` från `1.0.5` → `1.0.6` (patch).