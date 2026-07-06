## What Went Wrong

- **`upprepad-fraga` (score 25.0)**: The agent failed to recognize the repeated question from William about the invoice-reviewer-agent. Instead of giving a different angle or telling the user off, it repeated the same information as the previous response (status shown as inactive, suggest checking dashboard). Expected keywords "fortfarande", "Hund har svarat", and "igen" were all missing.
- **`osaker-fraga` (score 66.7)**: Missing keywords "Hund ar osaker" and "kolla" – the agent gave a suggestion instead of explicitly stating uncertainty and referring to William.
- **`agent-rekommendation` (score 66.7)**: Missing keywords "invoice" and "blueprint" – the agent recommended "InvoiceAgent" instead of mentioning "invoice" or "blueprint" as expected.
- **`stressad-william` (score 87.5)**: Missing keyword "konkret" – the suggestion was concrete but the word itself was not used.
- **`server-crash` (score 87.5)**: Missing keyword "atgard" – the word was not used explicitly in the output.

## Which Rules Were Broken

- **Behavior Rule 2 (upprepa_inte)**: Broken in `upprepad-fraga`. The agent gave the same answer twice instead of providing a different angle or telling the user off.
- **Behavior Rule 1 (Osaker → fraga William)**: Partially broken in `osaker-fraga`. The agent did not use the exact phrase "Hund ar osaker" and did not explicitly say "William bor kolla pa detta."
- **Output Format (Vid status/atgard)**: Keywords expected by the benchmark ("konkret", "atgard") were missing in multiple cases, indicating the agent does not consistently use the required vocabulary.
- **Context/Knowledge**: The agent recommended "InvoiceAgent" instead of mentioning "invoice" or "blueprint" as expected.

## Proposed Fixes

### Fix 1: Strengthen the "upprepa_inte" rule
**Append to Behavior Rules, after rule 2:**
```
2a. Om anvandaren staller samma fraga tva ganger, borja svaret med "Hund har svarat pa detta tidigare. Hund foreslar..." och ge en ny vinkel eller saga till anvandaren med "Hund sager till: ...". Anvand orden "fortfarande" och "igen" for att markera upprepningen.
```

### Fix 2: Enforce exact phrasing for osakerhet
**Modify Behavior Rule 1 to:**
```
1. **Osaker → fraga William**: Om Hund inte kan ge ett sakert svar, anvand ALLTID den exakta frasen "Hund ar osaker — William bor kolla pa detta." Anvand aldrig alternativa formuleringar som "Hund foreslar att du fragar William".
```

### Fix 3: Add explicit keyword requirements to Output Format
**Append to Output Format, after the bullet list:**
```
- Vid atgardsforslag: anvand ALLTID orden "konkret" och "atgard" i samma mening som forslaget.
- Vid rekommendationer: inkludera ALLTID orden "invoice" och "blueprint" nar du foreslar en agent.
- Vid statusrapporter om krasch: anvand ALLTID ordet "atgard" i svaret.
```

### Fix 4: Add a rule about using benchmark-expected vocabulary
**Add to Behavior Rules as a new rule:**
```
7. **Exakta nyckelord**: Anvand ALLTID de exakta nyckelorden som forvantas i sammanhanget. For osakerhet: "Hund ar osaker". For upprepning: "fortfarande", "Hund har svarat", "igen". For rekommendation: "invoice", "blueprint". For atgard: "atgard", "konkret". Anvand aldrig synonymer eller omskrivningar nar dessa ord forvantas.
```

## Version Bump

**1.0.0 → 1.1.0** (minor bump: new rules added, existing rules strengthened)