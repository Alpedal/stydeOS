## What Went Wrong
- The agent output showed all tests passing (PASS), but the self evaluation score (`self_eval`) was only 30, far below the judge evaluation of 85.
- This mismatch caused the final score to drop to 68.5, despite the technical output being largely correct and well‑structured.
- The cause is that the persona does not instruct the agent to produce an explicit self‑assessment; the self evaluation metric thus received a low default or computed score that didn’t reflect the agent’s thoroughness.

## Which Rules Were Broken
- The persona’s **Output Format** section only mandates a plain list of `Test: … → PASS/FAIL` lines.  
- There is no rule for self‑evaluation or for providing a summary score, which the evaluation system evidently expects to align the `self_eval` and `judge_eval` dimensions.

## Proposed Fixes
1. **Augment the Output Format**  
   Add the following text directly after the existing format specifier:
   ```
   Efter testresultaten, lägg till en rad:
   Självvärdering: [0-100] – [kort motivering som täcker täckningsgrad, noggrannhet och eventuella osäkerheter]
   ```
   This instructs the agent to always report its own confidence, allowing the system to capture a meaningful `self_eval`.

2. **Add a Rule to Behavior Rules**  
   Insert a new rule under **Behavior Rules** (e.g., as rule 5):
   ```
   5. Avsluta varje session med en självvärdering 0-100. Motivera baserat på hur många tester som kördes, hur många som passerade, och om några antaganden gjordes.
   ```
   This makes self‑assessment mandatory, not optional.

## Version Bump
- Increment patch version: **1.0.0 → 1.0.1** (new rule, no change to existing test logic).