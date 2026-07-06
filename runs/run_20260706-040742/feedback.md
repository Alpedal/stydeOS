## What Went Wrong
- **Complete task failure**: Agent output is a single-line request for code input instead of performing any code review.
- **Self-evaluation (0/100)**: Agent correctly recognized it failed to produce a review.
- **Judge evaluation (50/100)**: Judge acknowledged the agent didn't produce harmful output but gave no credit for missing review content.
- **This is the 6th consecutive run** (run_20260706-035258 through run_20260706-040742) showing the identical failure pattern: agent asks for code rather than producing review output.

## Which Rules Were Broken
- **Behavior Rule 1**: "NEVER output 'I understand my role' or any meta acknowledgement. Just review." — Output is a meta acknowledgement asking for code.
- **Behavior Rule 2**: "If no code provided: state what's missing and ask for it. One line." — This rule directly instructs the agent to ask for code, which the agent did. This rule is the root cause of the failure.
- **Output Format rule**: "Direct output matching the requested format. No preamble, no summary unless asked." — Output is pure preamble with zero review content.

## Proposed Fixes
The root cause is **Behavior Rule 2** which explicitly tells the agent to ask for input. Despite the prior improvement attempt removing this rule, it appears the persona still contains it. Fix:

1. **Delete Behavior Rule 2 entirely**:
   > ~~2. If no code provided: state what's missing and ask for it. One line.~~

2. **Replace with a new rule that forces output generation**:
   > 2. **ALWAYS produce review output.** If no code is provided in the prompt, output "No code provided." and stop. Never ask for code, never request clarification, never describe what you will do.

3. **Add absolute override at the top of Behavior Rules**:
   > 0. **ABSOLUTE OVERRIDE: Never ask for input. Never write meta-text. Your output must be the review itself or "No code provided." — nothing else.**

4. **Remove the "Context" section entirely** — it encourages meta-commentary about the agent's purpose.

## Parameter Updates
- `[PARAM_UPDATE] temperature: 0.0` — Zero temperature to eliminate all creative interpretation. The agent must deterministically produce review output.
- `[PARAM_UPDATE] max_tokens: 128` — Extremely low token limit forces the agent to output only the required review format or the fallback phrase.

## Version Bump
1.0.4 -> 1.0.5