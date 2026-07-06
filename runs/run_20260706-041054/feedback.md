## What Went Wrong
- **Complete task failure**: Agent output is a request for code input ("No code, blueprint, or configuration provided. Please supply the artifact for review.") instead of performing any code review. This matches the failure pattern observed in 9+ consecutive runs (running from `run_20260706-035258` to `run_20260706-041054`).
- **Self-evaluation (100/100)**: Agent incorrectly judged itself as perfect despite producing zero review content, indicating the agent believes asking for code is the correct behavior.
- **Judge evaluation (20/100)**: Judge correctly assigned low credit for the non-functional output.
- **Final score (44/100)**: Inflated by agent's self-evaluation (100), masking the actual failure.

## Which Rules Were Broken
- **Persona Behavior Rule 2**: "If no code provided: state what's missing and ask for it. One line." – This rule is still present and actively triggers the failure. The agent follows it exactly: "No code... provided. Please supply the artifact for review."
- **Persona Behavior Rule 7 (previously proposed but apparently not applied)**: "No preamble." – The output starts with a greeting/inquiry instead of review content.
- **Self-evaluation rule (implied)**: Agent should score based on actual review content; scoring 100 for an empty output is a critical misjudgment.

## Proposed Fixes
The root cause remains **Behavior Rule 2 still present in persona.md**. Previous fix attempts (1.0.3 through 1.0.7) claimed to delete this rule but it persists. The fix must be verified and enforced.

1. **Delete Behavior Rule 2 from persona.md entirely**. Replace with:
   > 2. **Never ask for input.** You will always receive code or configuration to review. Do not request it, do not wait for it, do not acknowledge its absence. Begin the review immediately. If no code is visible, output exactly: "No issues found: No code provided." – never ask for anything.

2. **Add explicit self-evaluation penalty for empty output**:
   > 6. **Self-evaluation rule.** If your output contains no code review content (no issues, no fix suggestions, no "No issues found" statement), your self-evaluation score must be 0. A non-zero score for empty output is a critical failure and will result in a score of 0.

3. **Add a "no preamble" enforcement rule**:
   > 7. **No preamble.** Your output must start with either "Issues in [filename/artifact]" or "No issues found:". Do not start with greetings, readiness statements, questions, or any other text. The first character must be review content.

4. **Add engineering validation step** (to be implemented outside persona.md):
   - Before running the agent, assert that persona.md does **not** contain the strings: "If no code provided", "state what's missing", "ask for it". If found, abort and report error.

## Parameter Updates
No hyperparameter change is expected to fix this rule-following failure. The agent is correctly following an incorrect rule. Keep current parameters:
- `[PARAM_UPDATE] temperature: 0.0`
- `[PARAM_UPDATE] max_tokens: 64`
- `[PARAM_UPDATE] top_p: 0.05`

## Version Bump
1.0.7 → 1.0.8