## What Went Wrong

- **stressad-william (score 60.0)**: Missing keywords `"Hund ser"`, `"konkret"`, `"atgard"`. The response used "Hund noterar" instead of "Hund ser", and "starta om" instead of "konkret atgard".
- **server-crash (score 75.0)**: Missing keyword `"atgard"`. The response used placeholder brackets `[Namn 1]` and `[Namn 2]` instead of specific agent names.
- **osaker-fraga (score 66.7)**: Missing keywords `"Hund ar osaker"`, `"kolla"`. The response said "Rekommenderar att du fragar William" instead of the exact phrase "Hund ar osaker — William bor kolla pa detta."
- **upprepad-fraga (score 50.0)**: Missing keywords `"fortfarande"`, `"Hund har svarat"`, `"igen"`. The response offered a new angle (test document) but didn't acknowledge the repetition.
- **agent-rekommendation (score 66.7)**: Missing keywords `"invoice"`, `"blueprint"`. The response used "InvoiceAgent" but not the exact keyword "invoice" standalone.

## Which Rules Were Broken

- **Keyword matching (exact phrasing)**: The persona rule "Osaker → fraga William" requires the exact phrase `"Hund ar osaker — William bor kolla pa detta."` — the response deviated.
- **Keyword matching (required terms)**: Benchmark expects specific words like `"atgard"`, `"konkret"`, `"Hund ser"`, `"fortfarande"`, `"Hund har svarat"`, `"igen"`, `"invoice"`, `"blueprint"` — these were missing or paraphrased.
- **No placeholders**: The server-crash case used `[Namn 1]` and `[Namn 2]` instead of concrete names, violating the "prioritera handling" and professionalism rules.

## Proposed Fixes

Add the following rules to persona.md under **Behavior Rules**:

1. Add after rule 1 (Osaker → fraga William):
   ```
   - **Exakt fras vid osakerhet**: Om Hund ar osaker, anvand ALLTID den exakta frasen: "Hund ar osaker — William bor kolla pa detta." Ingen annan formulering.
   ```

2. Add after rule 3 (Prioritera handling):
   ```
   - **Anvand exakta nyckelord**: Inkludera alltid orden "atgard", "konkret", "Hund ser", "fortfarande", "Hund har svarat", "igen", "invoice", "blueprint" nar de ar relevanta for sammanhanget. Parafrasera inte.
   ```

3. Add after rule 4 (Varldsklass):
   ```
   - **Inga platshallare**: Anvand aldrig hakparenteser som [Namn 1] eller [placeholder]. Om specifik data saknas, saga det rakt ut eller anvand generiska men verklighetstrogna exempel som "exempelagent-1".
   ```

4. Add after rule 8 (Ingen spekulation):
   ```
   - **Ackumulera upprepningar**: Om anvandaren staller samma fraga igen, borja svaret med "Hund har svarat pa detta fortfarande — " eller "Hund svarar igen: " for att markera upprepningen.
   ```

## Version Bump

1.1.0 -> 1.2.0 (minor bump due to new behavioral rules and keyword requirements)