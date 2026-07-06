## What Went Wrong
- Agenten levererade ett trunkerat kodblock (`main.py`) som saknar slut: funktionen `load_all_runs` är ofullständig (`-> l`) och inga endpoint-definitioner, router-registreringar eller körbar `app`-definition finns med.
- Ingen förklarande mening om endpointen levererades.
- Resultatet är icke-körbar kod, vilket gav låg bedömningspoäng (20.5 / 100).

## Which Rules Were Broken
- **Output Format**: Kravet ”Kodblock med tydlig fil och funktion. Förklara endpointen med en mening.” uppfylldes inte (ofullständig kod, ingen förklaring).
- Underförstått förväntades en fullständig, fungerande API-implementation, vilket uteblev.

## Proposed Fixes
Lägg till följande exakta rader i `persona.md`:

- **Ny beteenderegel** under `Behavior Rules` (ny punkt 7):  
  `7. Ditt slutgiltiga svar måste innehålla ett kodblock som är syntaktiskt korrekt och fullständigt. Inga funktioner eller klasser får vara avbrutna, och alla nödvändiga delar (import, app-definition, minst en komplett endpoint, `if __name__ == "__main__":`) ska finnas med. Om du inte får plats med allt i ett enda svar, prioritera att leverera endpoint-logiken och förklara tydligt vad som saknas.`

- **Förtydligande** under `Output Format`, efter befintlig rad:  
  `Kodblocket ska vara komplett och körbart. Förklara endpointen med en mening.`

Dessa tillägg adresserar direkt problemet med ofullständiga kodblock och säkerställer att agenten prioriterar en körbar lösning.

## Version Bump
- Bump `dashboard-api` persona från `1.0.2` → `1.0.3` (patch).