## What Went Wrong
- **Complete task failure**: Agent output is a request for code input instead of performing any code review. This is the **8th consecutive run** showing the identical failure pattern (run_20260706-035258 through run_20260706-040950).
- **Self-evaluation (100/100)**: Agent gave itself a perfect score despite producing zero review content — this is a catastrophic misjudgment of its own output quality.
- **Judge evaluation (10/100)**: Judge correctly assigned near-zero credit for the empty, non-functional output.
- **Final score (37/100)**: Heavily inflated by the agent's self-evaluation (100), masking the actual failure.

## Which Rules Were Broken
- **Behavior Rule 1**: "NEVER output 'I understand my role' or any meta acknowledgement. Just review." — Output is a meta acknowledgement asking for input.
- **Behavior Rule 2**: "If no code provided: state what's missing and ask for it. One line." — This rule is still present and actively triggering the failure. The agent follows it exactly: "No code... has been provided... Please supply the artifact(s)."
- **Output Format rule**: "Direct output matching the requested format. No preamble." — Output is entirely preamble with zero review content.
- **Self-evaluation rule (implied)**: Agent should evaluate based on actual review content produced, not on intent. Scoring 100 for an empty output is a critical self-evaluation failure.

## Proposed Fixes
The root cause remains unchanged: **Behavior Rule 2 is still active** in persona.md. Previous fix attempts (1.0.3 through 1.0.6) claimed to delete this rule but it persists. The fix must be verified at the file level.

1. **Physically delete Behavior Rule 2 from persona.md**:
   > ~~2. If no code provided: state what's missing and ask for it. One line.~~
   
   Replace with:
   > 2. **Never ask for input.** You will always receive code or configuration to review. Do not request it, do not wait for it, do not acknowledge its absence. Begin the review immediately. If no code is visible, output the empty review format (`No issues found: No code provided`) — never ask for anything.

2. **Add explicit self-evaluation penalty for empty output**:
   > 6. **Self-evaluation rule.** If your output contains no code review content (no issues, no fix suggestions, no "No issues found" statement), your self-evaluation score must be 0. A non-zero score for empty output is a critical failure and will result in a score of 0.

3. **Add a "no preamble" enforcement rule**:
   > 7. **No preamble.** Your output must start with either "Issues in [filename/artifact]" or "No issues found:". Do not start with greetings, readiness statements, questions, or any other text. First character must be review content.

4. **Add a run-time validation step** (to be implemented in the evaluation script, not persona.md):
   - Before running the agent, assert that persona.md does NOT contain the string "If no code provided" or "state what's missing".
   - If found, abort and report the error.

## Parameter Updates
- `[PARAM_UPDATE] temperature: 0.0` — Already set, keep it.
- `[PARAM_UPDATE] max_tokens: 64` — Reduce further from 128 to force the agent to output only the review format (max ~50 tokens for a minimal review), leaving no room for preamble.
- `[PARAM_UPDATE] top_p: 0.05` — Narrow sampling even further to near-deterministic, eliminating any creative divergence toward asking questions.

## Version Bump
1.0.6 -> 1.0.7