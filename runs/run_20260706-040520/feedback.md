## What Went Wrong
- The agent output is a single sentence asking for code to be provided, instead of performing any actual code review.
- The self-evaluation (85/100) is wildly inflated compared to the judge evaluation (0/100), indicating the agent completely failed to recognize its output was non-functional.
- This is a complete task failure — zero review output was produced. The agent did not analyze, critique, or fix any code.

## Which Rules Were Broken
- **Behavior Rule 1**: "NEVER output 'I understand my role' or any meta acknowledgement. Just review." — Output is a meta acknowledgement/request, not a review.
- **Behavior Rule 2**: "If no code provided: state what's missing and ask for it. One line." — Wait, this rule actually says to ask for code. But the agent is being evaluated on producing a review, and the evaluation context shows code was presumably provided. The rule as written is contradictory — it tells the agent to ask for code, which is exactly what the agent did, and that caused the failure.
- **Output Format rule**: "Direct output matching the requested format. No preamble, no summary unless asked." — Output contains preamble and no review content.

## Proposed Fixes
1. **Remove the contradictory rule** that tells the agent to ask for code. Delete Behavior Rule 2 entirely from `persona.md`:
   > ~~2. If no code provided: state what's missing and ask for it. One line.~~

2. **Strengthen the "no preamble" rule** by adding an explicit prohibition against asking for input:
   > 5. **Never ask for input.** You will always receive code or configuration to review. Do not request it. Do not wait for it. Begin the review immediately with the first issue or with "No issues found: [areas checked]".

3. **Add a self-evaluation calibration rule** to prevent inflated self-scores:
   > 6. **Self-evaluation accuracy.** If your output contains no code review, no issues identified, and no fix suggestions, your self-evaluation score must be 0. A non-zero score for empty output is a critical failure.

## Parameter Updates
- `[PARAM_UPDATE] temperature: 0.1` — Lower temperature to reduce creative/divergent behavior that leads to asking questions instead of executing.
- `[PARAM_UPDATE] max_tokens: 2048` — Ensure sufficient token budget for substantive review output.

## Version Bump
1.0.2 -> 1.0.3