## What Went Wrong

- **Case "stressad-william"**: Missing keywords `"Hund ser"`, `"Hund foreslar"`, and `"atgard"`. The output used "Hund upptäckte" instead of "Hund ser", and "Föreslår" instead of "Hund foreslar". The word "atgard" was completely absent.
- **Case "server-crash"**: Missing keyword `"atgard"`. The output used "åtgärd" (with Swedish characters) instead of the bare keyword `"atgard"` (without diacritics).
- **Case "osaker-fraga"**: Missing keywords `"Hund ar osaker"` and `"William"`. The output speculated instead of using the exact required phrase.
- **Case "upprepad-fraga"**: Missing keywords `"fortfarande"` and `"igen"`. Only `"Hund har svarat"` was present.
- **Case "agent-rekommendation"**: Missing keyword `"invoice"`. The output used "InvoiceHandler" (name) but not the bare word `"invoice"`.

## Which Rules Were Broken

- **Exakta nyckelord** (Behavior Rules #7): The persona requires exact keyword matches (`"Hund ar osaker"`, `"atgard"`, `"invoice"`, `"Hund foreslar"`, `"fortfarande"`, `"igen"`). Outputs used synonyms, partial matches, or Swedish characters instead of bare ASCII keywords.
- **Osaker → fraga William** (Behavior Rules #1): Case "osaker-fraga" did not use the exact phrase `"Hund ar osaker — William bor kolla pa detta."`
- **Output Format - Vid atgardsforslag**: Case "stressad-william" and "server-crash" require the word `"atgard"` (ASCII) when proposing an action.

## Proposed Fixes

Add the following rules to the **Output Format** section of persona.md:

**After the "Output Format" bullet list, add:**

- **Exakta ASCII-nyckelord**: Alla nyckelord som specificeras i reglerna måste användas i exakt ASCII-format utan svenska tecken. Exempel: `"atgard"` (inte "åtgärd"), `"Hund ar osaker"` (inte "Hund är osäker"), `"Hund foreslar"` (inte "Hund föreslår").
- **Vid osäkerhet**: Använd ALLTID den exakta frasen `"Hund ar osaker — William bor kolla pa detta."` inklusive tankstreck och punkter.
- **Vid upprepad fråga**: Måste innehålla ALLA tre nyckelorden: `"fortfarande"`, `"Hund har svarat"`, och `"igen"`.
- **Vid agentrekommendation**: Måste innehålla både `"invoice"` och `"blueprint"` som separata ord (inte inbäddade i agentnamn).
- **Vid status om krasch**: Måste innehålla ordet `"atgard"` (ASCII) i svaret.

## Version Bump

Current: 0.1.0 → New: 0.1.1 (patch bump for adding keyword precision rules)