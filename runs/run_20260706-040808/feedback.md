## What Went Wrong
- **Complete task failure**: Agent output is a single-line request for code input instead of performing any code review.
- **Self-evaluation (15/100)**: Agent partially recognized failure but still gave 15 points for an empty, non-functional output.
- **Judge evaluation (50/100)**: Judge gave half credit despite zero review content — this is inflated and enables the behavior.
- **This is the 7th consecutive run** (run_20260706-035258 through run_20260706-040808) showing the identical failure pattern: agent asks for code rather than producing review output. The previous fix attempts (1.0.3, 1.0.4, 1.0.5) have all failed to resolve this.

## Which Rules Were Broken
- **Behavior Rule 1**: "NEVER output 'I understand my role' or any meta acknowledgement. Just review." — Output is a meta acknowledgement disguised as readiness statement.
- **Behavior Rule 2**: "If no code provided: state what's missing and ask for it. One line." — This rule is still triggering despite prior fix attempts claiming to delete it. The agent follows this rule exactly: "Please provide the code..." is precisely what Rule 2 tells it to do.
- **Output Format rule**: "Direct output matching the requested format. No preamble, no summary unless asked." — Output is entirely preamble with zero review content.

## Proposed Fixes
The root cause is clear: **Behavior Rule 2** is still present and active in the persona. Previous fix attempts (1.0.3, 1.0.4, 1.0.5) claimed to delete this rule but it remains. The fix must be verified at the file level, not just proposed.

1. **Verify and delete Behavior Rule 2 from persona.md** — Check the actual file content. If the line exists:
   > ~~2. If no code provided: state what's missing and ask for it. One line.~~
   
   Delete it entirely. Then add a verification step in the run script to assert this line is absent before execution.

2. **Replace Behavior Rule 2 with a hard "never ask" constraint**:
   > 2. **Never ask for input.** You will receive code or configuration to review. Do not request it, do not wait for it, do not acknowledge its absence. Begin the review immediately. If no code is visible, output the empty review format (`No issues found: No code provided`) — never ask for anything.

3. **Add automatic zero-score enforcement**:
   > 6. **Empty output penalty.** If your output contains no code review content (no issues, no fix suggestions, no "No issues found" statement), your self-evaluation must be 0. A non-zero score for empty output is a critical failure.

4. **Add explicit preamble ban**:
   > 7. **Forbidden opening phrases.** Never start your output with: "I understand", "I'm ready", "Please provide", "I'll review", "I can help", or any meta acknowledgement. Your first character must be review content — no greetings, no readiness statements.

5. **Add a "no output = no review" rule**:
   > 8. **No output = no review.** If you produce no review content, you have failed the task. Do not ask for more information. Do not explain why you can't proceed. Just output the empty review format and score 0.

## Parameter Updates
- `[PARAM_UPDATE] temperature: 0.0` — Already set, keep it.
- `[PARAM_UPDATE] max_tokens: 128` — Reduce further to force the agent to output only the review format, no room for preamble.
- `[PARAM_UPDATE] top_p: 0.1` — Narrow sampling to near-deterministic, eliminating any creative divergence toward asking questions.

## Version Bump
1.0.5 -> 1.0.6