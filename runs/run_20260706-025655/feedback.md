## What Went Wrong
- Agentens output trunkerades mitt i funktionen `_compute_blueprint_stats`. Koden är ofullständig och kan inte köras. Detta är den fjärde körningen i rad med samma problem.
- All statistikfunktionalitet efter avbrottet saknas, inklusive huvudfunktionen och JSON-serialisering.

## Which Rules Were Broken
- **Output Format** (ursprunglig persona): *Python-moduler med tydliga funktioner. Varje funktion har en docstring.* En trunkerad modul är ingen modul.
- **Implicit krav på kompletthet**: agenten levererar inte en körbar pipeline.
- **Tidigare lärarförslag** (regel 6 och 7 om fullständighet och radgräns) har uppenbarligen inte varit tillräckliga för att undvika trunkering.

## Proposed Fixes
1. **Ersätt nuvarande radgräns med en strikt tokenbudget** (lägg till under *Behavior Rules*):
   > 7. Modulen får max bestå av 200 rader kod. Om den är längre, skriv om logiken så att den blir kompakt:  
   >    - använd list comprehensions istället för explicita loopar  
   >    - slå ihop `_compute_blueprint_stats` och `_read_eval` till en enda funktion som processar allt direkt  
   >    - ta bort alla typannoteringar  
   >    - ersätt långa `if`-kedjor med ternära uttryck  
   >    - använd `pass` istället för `if not path: return None` när möjligt  
   >    - alla docstrings får vara högst en rad, eller utelämnas helt om funktionsnamnet är självförklarande.

2. **Skärp kravet på Output Format** (modifiera nuvarande punkt):
   > **Output Format**  
   > Svaret ska endast innehålla Python-koden, innesluten i \`\`\`python … \`\`\`. Koden måste vara **komplett, körbar och under 200 rader**. Inga förklarande kommentarer utanför kodblocket. Om modulen riskerar att bli för stor, prioritera att leverera hela logiken framför stilistisk kvalitet – till exempel genom att ha en enda `main()`-funktion som gör allt med minimal felhantering.

3. **Inför ett explicit token-test i agentinstruktionen** (under *Context*):
   > **Tokenbegränsning**  
   > Du har begränsat antal tokens. Om din fullständiga modul är kortare än 200 rader men ändå klipps, betyder det att du måste förkorta ytterligare. Använd endast de absolut nödvändigaste funktionerna. Vid tvekan, prioritera att läsa forge.json, iterera över runs och returnera ett minimalt statistikobjekt – allt på under 100 rader.

4. **Ta bort överflödig logik** (under *Behavior Rules*):
   > `_is_fail` och liknande småhjälpare är onödiga; inline:a logiken direkt i `_compute_blueprint_stats`. `_read_eval` kan baka in sin logik i samma funktion. Ingen funktion får vara kortare än 3 rader användbar kod – då ska den inlinas.

## Version Bump
- **0.1.2 → 0.1.3** (patch bump för att stärka anti-trunkeringsreglerna).