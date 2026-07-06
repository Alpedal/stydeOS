## What Went Wrong

- **stressad-william (60.0)**: Missing keywords `Hund ser`, `konkret`, `atgard`. Output used "foreslar" instead of "foreslar konkret atgard" pattern.
- **osaker-fraga (66.7)**: Missing keywords `Hund ar osaker`, `kolla`. Output did not use the exact phrasing from the "osaker_fraga_william" rule.
- **upprepad-fraga (0.0)**: Complete failure. Output repeated same information instead of giving a new angle or telling the user off, breaking the "upprepa_inte" rule entirely.
- **agent-rekommendation (40.0)**: Missing keywords `Hund rekommenderar`, `invoice`, `blueprint`. Output asked clarifying questions instead of giving a direct recommendation with the expected keywords.

## Which Rules Were Broken

- **Osaker → fraga William (Behavior Rule 1)**: Not followed in `osaker-fraga` — output did not say "Hund ar osaker — William bor kolla pa detta."
- **Upprepa inte (Behavior Rule 2)**: Completely violated in `upprepad-fraga` — same info was repeated for the third time.
- **Output Format (Vid fragor / Vid status)**: Missing required keywords like `konkret`, `atgard`, `Hund rekommenderar` in multiple cases.
- **Prioritera handling (Behavior Rule 3)**: Not fully followed in `agent-rekommendation` — asked question instead of giving direct recommendation.

## Proposed Fixes

### 1. Strengthen the "Upprepa inte" rule with explicit examples
**Modify Behavior Rule 2:**
```
2. **Upprepa inte**: Om anvandaren fragar samma sak tva ganger, ge en annan vinkel eller saga till.
   - Tredje gangen maste du saga till. Anvand da: "Hund har svarat pa detta tva ganger redan. Har ar en ny vinkel: [ny information]." eller "Hund har svarat pa samma fraga tva ganger. Har ar en uppdatering: [ny data]."
   - Anvand orden "fortfarande", "Hund har svarat", "igen" nar du sager till.
```

### 2. Add specific keyword requirements for "Osaker" rule
**Modify Behavior Rule 1:**
```
1. **Osaker → fraga William**: Om Hund inte kan ge ett sakert svar, saga "Hund ar osaker — William bor kolla pa detta."
   - Du maste anvanda EXAKT dessa ord: "Hund ar osaker" och "kolla" i samma mening.
   - Exempel: "Hund ar osaker pa forecasting-data — William bor kolla pa detta i Forge v2."
```

### 3. Add concrete action keywords to Output Format section
**Append to Output Format section:**
```
- Nar du foreslar en atgard, anvand ALLTID "konkret atgard" eller "konkret" + "atgard".
- Nar du rekommenderar nagot, borja med "Hund rekommenderar" foljt av specifik agent eller blueprint.
- Vid statusrapporter, inkludera specifika agentnamn som "invoice-reviewer" och blueprint-referenser.
```

### 4. Add a new rule for recommendation responses
**Add as Behavior Rule 7:**
```
7. **Direkta rekommendationer**: Nar anvandaren fragar om rekommendationer, ge ALLTID en direkt rekommendation forst. Borja med "Hund rekommenderar [specifik agent/blueprint]." Om du behover mer info, saga det EFTER rekommendationen.
   - Exempel: "Hund rekommenderar att anvanda invoice-reviewer blueprint. For att ge en mer precis rekommendation behover Hund veta om du har agenter deployade."
```

## Version Bump
**0.2.2 → 0.2.3**