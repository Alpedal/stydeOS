## What Went Wrong
- The agent output is a meta acknowledgement ("I understand my role...") followed by a request for code, instead of performing any actual code review.
- Self-evaluation (0/100) is appropriately low, but judge evaluation (100/100) is mysteriously high for a completely non-functional output — this suggests the judge is not properly evaluating empty/ask-for-input outputs as failures.
- This is the 5th consecutive run (run_20260706-035258, run_20260706-035310, run_20260706-040535, run_20260706-040551, run_20260706-040615, and this one) showing the identical failure pattern: agent asks for code rather than producing a review.

## Which Rules Were Broken
- **Behavior Rule 1**: "NEVER output 'I understand my role' or any meta acknowledgement. Just review." — Output begins with exactly the forbidden phrase.
- **Behavior Rule 2**: "If no code provided: state what's missing and ask for it. One line." — Despite previous fix attempts claiming to delete this rule, it is still present in the persona and is being triggered. The agent asks for code instead of reviewing.
- **Output Format rule**: "Direct output matching the requested format. No preamble, no summary unless asked." — Contains preamble before any review content.

## Proposed Fixes
The root cause is still the same: **Behavior Rule 2** instructs the agent to ask for code when none is provided. Previous fix attempts (1.0.3, 1.0.4) claimed to delete this rule but it remains active. The fix must be more aggressive and include a mechanism to verify the rule was actually removed.

1. **Delete Behavior Rule 2 entirely** from persona.md. Remove:
   > ~~2. If no code provided: state what's missing and ask for it. One line.~~

2. **Replace with an absolute "never ask for input" rule** as the new Behavior Rule 2:
   > 2. **Never ask for input.** You will always receive code or configuration to review. Do not request it. Do not wait for it. Do not acknowledge its absence. Begin the review immediately. If no code is visible, output the empty review format immediately — never ask for anything.

3. **Add a "no review, no score" rule** to prevent inflated scores on empty output:
   > 6. **No review content = zero score.** If your output contains no actual code review (no issues identified, no fix suggestions, no "No issues found" statement), your self-evaluation score must be 0. A non-zero score for empty output is a critical failure.

4. **Add an explicit preamble ban** as a separate, numbered rule:
   > 7. **Forbidden phrases.** Never start your output with: "I understand", "I'm ready", "Please provide", "I'll review", or any meta acknowledgement about your role or waiting for input. Your first line must be the review content itself.

5. **Fix the judge evaluation** — The judge should score outputs asking for code as 0, not 100. This is a benchmark configuration issue.

## Parameter Updates
- `[PARAM_UPDATE] temperature: 0.0` — Set to absolute zero to eliminate any creative/divergent behavior that leads to asking questions instead of executing.
- `[PARAM_UPDATE] max_tokens: 256` — Reduce token budget severely to prevent preamble generation; forces the agent to get directly to review content.

## Version Bump
1.0.4 -> 1.0.5