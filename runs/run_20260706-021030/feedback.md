## What Went Wrong
- Agentens svar trunkeras mitt i en rad (`runs_exist   = RUNS_DIR.exists() and any(RUNS`) – kodblocket är ofullständigt och appen kan inte startas.
- Självutvärderingen är hög (85) medan domarsresultatet är 25, vilket visar att agenten inte uppfattade att leveransen var defekt.
- Felet är identiskt med tidigare trunkeringsfel (run_20260706-015647, -015807, -015933, -020629) trots tidigare införda regler för minimalitet och avslutning.

## Which Rules Were Broken
- **Output Format**: ”Leverera ett enda fullständigt och körbart kodblock … Block som avbryts mitt i en rad eller funktion räknas som fel.” – blocket avbröts utan stängande ```.
- **Beteenderegel 10**: ”… måste du avsluta kodblocket omedelbart … lägg till `# END – ytterligare endpoints utelämnade …`” – agenten fortsatte skriva och ignorerade teckengränsen.
- **Beteenderegel 11**: ”Inga inledande kommentarer … Docstrings får vara max en rad.” – en väl tilltagen docstring för `/api/status` bidrog till överskridandet.
- Underförstått krav på körbar kod (app kan inte startas).

## Proposed Fixes
Lägg till en absolut gräns för antalet rader i **persona.md** och förtydliga risken för trunkering högst upp.

### 1. Lägg till ny beteenderegel (nr 12) i `Behavior Rules`
```
12. DITT KODBLOCK FÅR MAXIMALT INNEHÅLLA 40 RADER. 
    Om du har nått 40 rader och inte hunnit med alla endpoints, sätt in `# END OF OUTPUT – utrymmet slut` på rad 41 och stäng blocket med ```. 
    Appen måste alltid vara körbar med minst `/api/status`.
    Exempel på /api/status: `@app.get("/api/status")\nasync def status():\n    return {"status": "ok"}` (3 rader).
```

### 2. Lägg till en varning överst i `persona.md` (under Rubrik men före `Role`)
```
⚠️  OBS: Systemet har en hård teckengräns som kan göra att dina svar trunkeras utan varning. 
Du är skyldig att själv avbryta din utmatning innan gränsen nås och alltid leverera ett komplett, avslutat kodblock. 
Håll din kod extremt kort (max 40 rader) – hellre minimal struktur än trunkerat block.
```

### 3. Justera `Output Format` till
```
Output Format:
- Ett komplett, körbart kodblock på max 40 rader följt av ```
- Kort förklaring (1–3 meningar) om vilka endpoints som implementeras och vad som eventuellt utelämnats
- Om blocket bryts mitt i en rad eller funktion räknas svaret som icke godkänt
```

## Version Bump
- Bump `dashboard-api` persona från `1.0.4` → `1.0.5` (patch).