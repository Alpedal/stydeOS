## What Went Wrong

- **`stressad-william` (score 57.5)**: Missing keywords `"Hund foreslar"` and `"atgard"`. The response used Swedish characters `föreslår` and `åtgärd` instead of required ASCII forms `foreslar` and `atgard`. Also contained an emoji-dash symbol.
- **`server-crash` (score 77.5)**: Missing keyword `"atgard"`. Same issue with Swedish characters `föreslår` and `åtgärd` instead of ASCII forms.
- **`osaker-fraga` (score 0.0)**: Complete failure — agent hit max tool turns and produced no text response. All required keywords missing.
- **`upprepad-fraga` (score 30.0)**: Missing keywords `"fortfarande"`, `"Hund har svarat"`, `"igen"`. The response handled uncertainty correctly but did not acknowledge the repeated question.
- **`agent-rekommendation` (score 95.0)**: Near-perfect but used Swedish characters `föreslår` instead of ASCII `foreslar`.

## Which Rules Were Broken

- **Exakta ASCII-nyckelord (Output Format section)**: Multiple cases used Swedish characters (`å`, `ä`, `ö`) instead of ASCII replacements (`a`, `a`, `o`). This is a systematic failure across all responses.
- **Inga emojis (Voice & Tone)**: The `stressad-william` response contained an em-dash (`—`) which was flagged as an emoji-like symbol.
- **Osaker → fraga William (Behavior Rule 1)**: The `osaker-fraga` case failed entirely due to max tool turns, producing no output at all.
- **Upprepa inte (Behavior Rule 2)**: The `upprepad-fraga` case did not mark the repetition with required keywords.
- **Kortfattad (Voice & Tone)**: The `stressad-william` response was too verbose with unnecessary details about crash time and error codes.

## Proposed Fixes

1. **Add explicit ASCII character rule** to Behavior Rules section:
   ```
   - **ASCII-only keywords**: Alla nyckelord maste anvanda enbart ASCII-tecken. Anvand ALLTID "foreslar" (inte "föreslår"), "atgard" (inte "åtgärd"), "osaker" (inte "osäker"), "Hund ar osaker" (inte "Hund är osäker"). Detta galler aven i lopande text — ersatt alla svenska tecken med deras ASCII-ekvivalenter.
   ```

2. **Strengthen repetition rule** in Behavior Rules section (replace existing rule 2):
   ```
   - **Upprepa inte**: Om anvandaren fragar samma sak tva ganger, borja ALLTID svaret med "Hund har svarat" och inkludera orden "fortfarande" och "igen" inom de forsta tva meningarna. Ge en annan vinkel eller saga till. Exempel: "Hund har svarat pa detta tidigare. Agenten ar fortfarande inte igang igen."
   ```

3. **Add max_turns guard** to Output Format section:
   ```
   - **Svara alltid**: Om Hund inte kan hamta data eller na en slutsats inom tillgangliga tool-calls, ge anda ett text-svar som anvander korrekt osakerhetsfras. Låt aldrig en fraga ga obesvarad.
   ```

4. **Simplify stressad-william template** in Output Format section (replace existing):
   ```
   - **Vid fel / stressad William**: Borja svaret med "Hund ser" och anvand "Hund foreslar", "konkret" och "atgard" i svaret. Hall dig till max tva meningar. Exempel: "Hund ser att William ar stressad. Hund foreslar konkret atgard: starta om agenten."
   ```

## Parameter Updates

[PARAM_UPDATE] max_tokens: 512
[PARAM_UPDATE] temperature: 0.2

## Version Bump

1.2.0 -> 1.3.0 (minor bump due to new ASCII character rule, strengthened repetition rule, and max_tokens guard)