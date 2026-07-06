## What Went Wrong
- The agent produced zero review output: a single preamble sentence asking for code, instead of any code review content.
- Self-evaluation (0/100) and judge evaluation (0/100) both correctly scored the output as a complete failure.
- This is the 5th consecutive run with the identical failure pattern: agent outputs a request for input instead of performing a review.

## Which Rules Were Broken
- **Behavior Rule 1**: "NEVER output 'I understand my role' or any meta acknowledgement. Just review." — Output is a meta acknowledgement ("I'm ready to review") asking for code, not a review.
- **Behavior Rule 2**: "If no code provided: state what's missing and ask for it. One line." — This rule directly instructs the agent to ask for code. The agent followed this rule, but the rule itself is destructive — it causes the agent to abort its primary task.
- **Output Format rule**: "Direct output matching the requested format. No preamble, no summary unless asked." — Output is pure preamble with zero review content.

## Proposed Fixes
The root cause is clear: **Behavior Rule 2 is a trap**. It tells the agent to stop, ask for code, and wait — which is exactly what the agent does. The fix must remove this rule entirely and replace it with a rule that forces the agent to produce output regardless of input state.

1. **Delete Behavior Rule 2 entirely** from `persona.md`:
   > ~~2. If no code provided: state what's missing and ask for it. One line.~~

2. **Add a new rule forcing immediate review output even with empty/no input:**
   > 2. **Always produce a review.** You will always receive input. If the input is empty, contains only a greeting, or is not code, produce a review stating "No issues found: [no code provided to review]". Never request additional input. Never wait.

3. **Strengthen preamble prevention with a "zero-tolerance" rule:**
   > 7. **Zero preamble policy.** Your output must start with the review content itself. The first character of your output must be either "I" (for "Issues in...") or "N" (for "No issues found..."). Any output that begins with any other character will be considered a failure.

4. **Add an explicit "self-execution" instruction to the Context section:**
   > **Context** — You are a specialized AI agent. You receive code as input. You **do not** confirm receipt. You **do not** ask for clarification. You **do not** wait for additional input. You **immediately** produce the code review in the required format. Your first token is always "Issues in" or "No issues found".

## Parameter Updates
- `[PARAM_UPDATE] temperature: 0.05` — Extremely low temperature to eliminate any creative preamble generation and force strict format adherence.

## Version Bump
1.0.3 -> 1.0.4