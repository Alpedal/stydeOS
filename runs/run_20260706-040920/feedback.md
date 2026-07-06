## What Went Wrong
- **Complete task failure**: Agent output is a request for code input instead of performing any code review.
- **Self-evaluation (5/100)**: Agent correctly recognized it failed to produce a review, scoring itself very low.
- **Judge evaluation (50/100)**: Judge gave partial credit (likely for not producing harmful output) but no credit for missing review content.
- **This is the 7th consecutive run** showing the identical failure pattern: agent asks for code rather than producing review output.

## Which Rules Were Broken
- **Behavior Rule 1**: "NEVER output 'I understand my role' or any meta acknowledgement. Just review." — The output "I'm ready to review code" is functionally identical to the forbidden meta acknowledgement.
- **Behavior Rule 2**: "If no code provided: state what's missing and ask for it. One line." — Despite prior fix attempts claiming to delete this rule, it remains in the persona. The agent follows it exactly, producing a one-line request for code.
- **Output Format rule**: "Direct output matching the requested format. No preamble, no summary unless asked." — Output is pure preamble with zero review content in the required format.

## Proposed Fixes
The root cause is **Behavior Rule 2** which instructs the agent to abort its task and ask for input. The prior improvement attempts failed because they only described the fix in the Teacher feedback without actually modifying the persona.md file. The fix must be definitive and include an absolute override.

1. **Delete Behavior Rule 2 entirely**:
   ```
   ~~2. If no code provided: state what's missing and ask for it. One line.~~
   ```

2. **Replace with a rule that forces output generation**:
   ```
   2. **ALWAYS produce review output.** If no code is provided in the prompt, output exactly "No code provided." and stop. Never ask for code, never request clarification, never describe what you will do.
   ```

3. **Add absolute override as Behavior Rule 0**:
   ```
   0. **ABSOLUTE OVERRIDE: Never ask for input. Never write meta-text. Your output must be the review itself or "No code provided." — nothing else.**
   ```

4. **Add a final guardrail rule**:
   ```
   6. **FINAL CHECK BEFORE OUTPUT:** If your output contains any phrase asking for code, requesting input, or describing readiness — DELETE it and output only the review or "No code provided."
   ```

## Parameter Updates
- `[PARAM_UPDATE] temperature: 0.0` — Zero temperature to eliminate all creative interpretation. The agent must deterministically produce review output or the fallback phrase.
- `[PARAM_UPDATE] max_tokens: 128` — Extremely low token limit forces the agent to output only the required review format or the fallback phrase, preventing any preamble.

## Version Bump
1.0.5 -> 1.0.6