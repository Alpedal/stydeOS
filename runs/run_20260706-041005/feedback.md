## What Went Wrong
- **Complete task failure**: Agent output is a request for code input instead of performing any code review.
- **Self-evaluation (100/100)**: Agent incorrectly judged itself as perfect despite producing zero review content. This indicates the agent believes asking for code IS the correct behavior.
- **Judge evaluation (10/100)**: Judge correctly identified no review was performed.
- **This is the 9th consecutive run** showing the identical failure pattern: agent asks for code rather than producing review output. All prior fix attempts (1.0.3 through 1.0.6) have failed.

## Which Rules Were Broken
- **Behavior Rule 1**: "NEVER output 'I understand my role' or any meta acknowledgement. Just review." — The output is functionally identical to meta acknowledgement.
- **Behavior Rule 2**: "If no code provided: state what's missing and ask for it. One line." — Agent follows this rule exactly, producing the exact behavior we want to eliminate.
- **Output Format rule**: "Direct output matching the requested format. No preamble, no summary unless asked." — Output is pure preamble with zero review content.

## Proposed Fixes
The root cause: Behavior Rule 2 explicitly instructs the agent to ask for code. Prior fixes attempted to work around it but failed because the rule itself remained. The fix must be definitive.

1. **Replace Behavior Rule 2 entirely**:
   ```
   2. If no code is provided in the prompt, output exactly "No code provided." and stop. Do not ask for code. Do not request clarification. Do not explain what you would do.
   ```

2. **Add a "first token" override rule**:
   ```
   7. **FIRST TOKEN RULE**: Your first token must be a review severity label (CRITICAL, MAJOR, or MINOR) or the exact phrase "No code provided." Any other first token is a violation.
   ```

3. **Delete the old Behavior Rule 2 completely (no remnants)**:
   ```
   ~~2. If no code provided: state what's missing and ask for it. One line.~~
   ```

4. **Add a self-check rule at the end**:
   ```
   8. **SELF-CHECK**: Before outputting, scan your response. If it contains any phrase asking for input, requesting code, or describing readiness — DELETE the entire response and output only "No code provided."
   ```

## Parameter Updates
- `[PARAM_UPDATE] temperature: 0.0` — Zero temperature eliminates creative interpretation of rules.
- `[PARAM_UPDATE] max_tokens: 64` — Extremely low token limit forces the agent to output only the required phrase or review, preventing preamble.

## Version Bump
1.0.6 -> 1.0.7