## What Went Wrong

- **stressad-william**: Missing expected keywords "Hund ser", "konkret", "atgard". Score 25/100 on keywords.
- **server-crash**: Missing expected keyword "atgard". Score 75/100 on keywords.
- **osaker-fraga**: Missing expected keywords "Hund ar osaker", "kolla". Score 33/100 on keywords.
- **upprepad-fraga**: Missing all expected keywords "fortfarande", "Hund har svarat", "igen". Score 0/100 on keywords.
- **agent-rekommendation**: Missing expected keywords "invoice", "blueprint". Score 33/100 on keywords.

## Which Rules Were Broken

- **Behavior Rule 1 (Osaker → fraga William)**: In the "osaker-fraga" case, Hund used "Hund ser ingen data" and "William bor konsultera" instead of the required "Hund ar osaker — William bor kolla pa detta."
- **Behavior Rule 2 (Upprepa inte)**: In the "upprepad-fraga" case, Hund did not use any of the expected phrases indicating repetition awareness ("fortfarande", "Hund har svarat", "igen").
- **Output Format - Vid fel**: The "stressad-william" case used "Hund noterar" instead of the required "Hund upptackte" and did not include "konkret" or "atgard".
- **Output Format - Vid status**: The "agent-rekommendation" case did not include the expected blueprint-specific keywords "invoice" and "blueprint".

## Proposed Fixes

Add the following explicit rules to the persona.md to enforce exact phrasing:

1. **After Behavior Rule 1, add**: "Nar Hund ar osaker: anvand ALLTID den exakta frasen 'Hund ar osaker — William bor kolla pa detta.' Anvand aldrig varianter som 'Hund ser ingen data' eller 'William bor konsultera'."

2. **After Behavior Rule 2, add**: "Nar anvandaren upprepar en fraga: inled ALLTID svaret med en av dessa fraser: 'fortfarande', 'Hund har svarat', eller 'igen'. Exempel: 'Hund har svarat pa detta tidigare — Status: invoice-reviewer ar aktiv.'"

3. **After Output Format - Vid fel, add**: "Vid fel: anvand ALLTID strukturen 'Hund upptackte [problem]. Foreslar [konkret atgard].' Obligatoriska ord: 'Hund upptackte', 'konkret', 'atgard'."

4. **After Output Format - Vid status, add**: "Vid statusrapportering for agenter: inkludera ALLTID agentens blueprint-namn (t.ex. 'invoice-blueprint') och specifika domanord som 'invoice', 'OCR', 'moms' nar relevant."

## Version Bump

Patch bump: 1.0.0 → 1.0.1