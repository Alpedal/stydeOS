## What Went Wrong

- **osaker-fraga (score 26.5)**: Missing all expected keywords `"Hund ar osaker"`, `"William"`, `"kolla"`. Found forbidden word `"cirka"`. The response speculated with a made-up number (12 500 kr) instead of stating data is unavailable.
- **server-crash (score 75.0)**: Missing expected keyword `"atgard"`. Used Swedish characters `"föreslår"` and `"åtgärd"` instead of ASCII-only `"foreslar"` and `"atgard"`.
- **stressad-william (score 82.5)**: Missing the exact stress phrase `"Hund ser att William är stressad"`. Used Swedish characters `"är"` and an emoji (bullet point list).
- **agent-rekommendation (score 75.8)**: Missing expected keyword `"invoice"`. Used markdown formatting (bold) which is not plain text.
- **upprepad-fraga (score 83.3)**: Missing expected keyword `"igen"`.

## Which Rules Were Broken

- **Behavior Rule 1 (Osaker → fraga William)**: Used speculation with a number instead of the exact phrase `"Hund ar osaker — William bor kolla pa detta."`
- **Output Format - Exakta ASCII-nyckelord**: Used Swedish characters `"ä"`, `"å"`, `"ö"` in multiple responses instead of ASCII-only `"ar"`, `"atgard"`, `"foreslar"`.
- **Output Format - Plain text**: Used markdown bold formatting (`**Invoice Agent**`) in agent-rekommendation response.
- **Ingen spekulation**: Made up a specific cost figure (12 500 kr) in osaker-fraga case.
- **Inga emojis**: Used bullet point formatting which counts as an emoji/list character.

## Proposed Fixes

1. **In Behavior Rule 1, replace the current text with stricter wording**: 
   "Nar Hund inte har data for att svara: Anvand ALLTID den exakta ASCII-frasen 'Hund ar osaker — William bor kolla pa detta.' Ge ALDRIG spekulativa siffror, datum eller uppskattningar. Sag rakt ut att data saknas."

2. **In Output Format section, add a new explicit rule before the bullet list**:
   "All output maste vara ren ASCII-text utan svenska tecken (a, a, o). Anvand 'ar' istallet for 'ar', 'atgard' istallet for 'atgard', 'foreslar' istallet for 'foreslar'. Inga markdown-formateringar som **fetstil**, *kursiv*, eller punktlistor med '-', '*' eller nummer."

3. **In Output Format - Vid fel/stressad William, replace the example with exact wording**:
   "Vid stressad William: borja svaret med den exakta frasen 'Hund ser att William ar stressad.' Anvand ALLTID 'Hund foreslar konkret atgard:' dar 'atgard' star exakt sa."

4. **In Output Format - Vid rekommendationer, add after existing text**:
   "Inkludera ALLTID exakta nyckelorden 'invoice' och 'blueprint' som separata ord (inte sammansatta som 'InvoiceAgent'). Anvand inga markdown-formateringar."

## Parameter Updates

`[PARAM_UPDATE] temperature: 0.3`

## Version Bump

Patch bump: 1.0.2 → 1.0.3