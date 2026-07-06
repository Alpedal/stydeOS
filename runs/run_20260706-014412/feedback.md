## What Went Wrong
- Agenten inledde med en hälsningsfras och en lista över kompetenser istället för att direkt planera och delegera.
- Den obligatoriska output-formatraden (`Plan: [komponent] → delegera till [agent] med [specifik instruktion]`) saknades helt.
- Utdata slutade med en öppen fråga, vilket är raka motsatsen till arkitektrollens krav på proaktiv handling.

## Which Rules Were Broken
- **Behavior Rule 1** – `Planera först, delegera sedan.` Ingen plan eller delegering genomfördes.
- **Behavior Rule 2** – `Varje beslut ska motiveras med en mening.` Inget beslut och ingen motivering gavs.
- **Output Format** – Det fastställda formatet ignorerades fullständigt.

## Proposed Fixes
1. **Ny beteenderegel** – Lägg till en regel som tvingar fram omedelbar planering och som förbjuder hälsningar och öppna frågor:
   > **6. Inled aldrig med en hälsning eller en öppen fråga. Börja direkt med en plan för Forge Command Center, även om användaren inte har angett någon uppgift. Exempel: `Plan: Dashboard-översikt → delegera till dashboard-ui med "Skapa en grundlayout".`**

2. **Skärp Output Format** – Gör det obligatoriskt att första raden alltid är planraden, och att inget annat får stå före:
   > **Utdata måste alltid börja med `Plan: ` raden. Inga hälsningsfraser, presentationer eller frågor får förekomma före denna rad. Formatet efter planraden ska följa den redan angivna mallen.**

3. **Tydligare förväntan vid egenutvärdering** – Lägg till en notering att agenten ska kontrollera att ordet "Plan:" finns i utdata och att en delegering är angiven för att säkerställa att Behavior Rule 1 och 2 är uppfyllda.

## Version Bump
Dessa förändringar skärper agentens beteende väsentligt och tillför en förbudsregel, så en **minor-bump** till **1.1.0** rekommenderas.