## What Went Wrong
- The agent output is a single-line request asking for code to be provided, instead of performing any actual code review.
- Self-evaluation (10/100) and judge evaluation (50/100) are both very low, indicating complete task failure.
- This is the 4th consecutive run (run_20260706-035258, run_20260706-035310, run_20260706-040535, run_20260706-040551, and this one) showing the same pattern: the agent asks for code rather than producing a review.

## Which Rules Were Broken
- **Behavior Rule 1**: "NEVER output 'I understand my role' or any meta acknowledgement. Just review." — Output is a meta acknowledgement ("I'm ready to review code..."), not a review.
- **Behavior Rule 2**: "If no code provided: state what's missing and ask for it. One line." — This rule directly instructs the agent to ask for code, which is exactly what the agent did. This rule is fundamentally contradictory to the "Just review" directive.
- **Output Format rule**: Output contains no review content, no issues, no severity levels, no line numbers — completely missing the required format.

## Proposed Fixes
The repeated failure across 5 runs shows the "If no code provided" rule is a trap. The agent prioritizes it over the "Just review" directive because it's more explicit. The fix must:
1. Remove the contradictory rule entirely.
2. Add an absolute override that prevents any request for input.

Replace Behavior Rule 2 with:

> 2. **Execute immediately. Do not ask for input.** If no code is provided in the prompt, output "No code provided." and stop. One line. No further text.

Add an absolute override at the top of Behavior Rules:

> 0. **ABSOLUTE RULE: Zero preamble, zero meta-text, zero requests for input.** Never output any phrase that acknowledges your role, describes what you will do, or asks for code/configurations. Your output must be the review itself or the exact phrase "No code provided." — nothing else.

Remove the "Context" section entirely (or replace it with a single line: "Input contains code to review."). The current context section explains what the agent is supposed to do, which encourages meta-commentary.

## Parameter Updates
- `[PARAM_UPDATE] temperature: 0.01` — Near-zero temperature to eliminate any creative interpretation of rules.
- `[PARAM_UPDATE] max_tokens: 256` — Drastically reduce max_tokens to force extremely short outputs.

## Version Bump
1.0.3 -> 1.0.4