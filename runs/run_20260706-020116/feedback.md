## What Went Wrong
- I run `run_20260706-020116` levererades en **ofullständig HTML-fil** – CSS-koden bröts mitt i en deklaration (``.stat-card:hover``) och filen saknar avslutande HTML-taggar, JS och resten av layouten.  
- Dashboard:en är därmed inte användbar. Judge-eval gav endast 20 poäng (av förmodat 100), vilket bekräftar att leveransen inte uppfyllde kraven.

## Which Rules Were Broken
- **Output Format**: “Kompletta HTML-filer med inline CSS och JS. En fil per vy.” – Filen är inte komplett, utan abrupt avbruten.  
- **Behavior Rule 1** (indirekt): Agenten skulle bygga en enkel HTML/CSS/JS-dashboard, men misslyckades med att leverera en fullständig vy.  
- (Ingen verktygsanvändning syntes i output, så tidigare fixar (regel 6 och 7) är inte orsaken.)

## Proposed Fixes
Problemet är att den genererade HTML-filen blev för stor och klipptes av i svaret. För att tvinga fram en hel, körbar fil behövs en ny regel som uppmuntrar till **minimalism och kontroll av längd**:

**Ny regel att lägga till under `## Behavior Rules`:**
> **8. Output-längd** – Den genererade HTML-filen ska vara **komplett och körbar** i ett enda svar. Håll designen ren och minimalistisk. Max 250 rader totalt (inkl. CSS och JS). Använd endast nödvändig styling. Prioritera funktion över estetiskt överflöd.

Detta förhindrar att agenten bygger för många detaljer och riskerar att klippas av. Vidare kan den tidigare regel 6 (om verktygsanvändning) lämnas orörd, då den inte är relevant här.

## Version Bump
- Rekommenderad ny version: **1.0.3** (patch bump) – riktad förbättring för att garantera kompletta leveranser.