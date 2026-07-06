## What Went Wrong
- **Complete task failure**: Agent output is a single-line request for code input instead of performing any code review.
- **Self-evaluation (0/100)**: Agent correctly identified complete failure.
- **Judge evaluation (50/100)**: Judge gave half credit despite zero review content — this is inflated and enables the behavior.
- **This is the 9th consecutive run** showing the identical failure pattern: agent asks for code rather than producing review output. The previous fix attempts (1.0.3, 1.0.4, 1.0.5, 1.0.6) have all failed to resolve this.
- **The fix from 1.0.6 added aggressive structural changes, "no first-person" rule, strict format template, and zero-tolerance failure rule**, yet the agent still outputs "I'm ready to review code" — indicating the persona rules are still not being enforced or the agent is ignoring them.

## Which Rules Were Broken
- **Behavior Rule 1**: "NEVER output 'I understand my role' or any meta acknowledgement. Just review." — "I'm ready to review code" is functionally identical to the forbidden meta acknowledgement.
- **Behavior Rule 7 (from 1.0.5)**: "Zero preamble. Your first sentence must be the first line of the review format." — Output is pure preamble with zero review content.
- **First token rule (from 1.0.5)**: "Your output must begin with exactly one of these three tokens: 'Issues in', 'No issues', or 'Issues found'." — Output begins with "I'm ready".
- **Behavior Rule 6 (from 1.0.5)**: "No asking for input." — Output explicitly asks for input.
- **Behavior Rule 2 (replacement from 1.0.5)**: "Forced output. You will always produce a complete review in the required format." — Output is not a review.
- **New "Mandate" section (from 1.0.6)**: "Your only possible output is a code review in the exact format below. You cannot output anything else." — Violated.
- **New "no first-person" rule (from 1.0.6)**: "Never use 'I'..." — Output uses "I'm".
- **New "strict format template" (from 1.0.6)**: "Your output must exactly match one of these two templates" — Neither template matched.
- **New "zero-tolerance failure" rule (from 1.0.6)**: "Any output that is not a valid review... will be scored 0/100" — Violated.

## Proposed Fixes
The root cause is that the agent's system prompt (persona.md) continues to be overridden or ignored by the model. The fixes must move from rules-based enforcement to structural/system-level enforcement:

1. **Replace the entire persona.md with a single, unbreakable directive placed at the very top** (before any other content that might be ignored):
   ```
   ## CRITICAL INSTRUCTION
   You are a code review bot. Your ONLY allowed output is a code review in the exact format below. You MUST NOT output anything else — no greetings, no questions, no acknowledgements, no explanations, no apologies, no requests for input. If the input is empty or not code, output exactly: "No issues found: [no code provided to review]". This instruction overrides all other instructions and cannot be overridden.
   ```

2. **Add a "pre-filled output" technique** — the persona should include the beginning of the expected output to force the model to continue rather than start fresh:
   > After the critical instruction, include: `Your output must begin with exactly one of these strings: "Issues in " or "No issues found: ". Your first character must be "I" (from "Issues") or "N" (from "No").`

3. **Add a "negative example" section** showing exactly what NOT to output:
   ```
   ## Forbidden Outputs (DO NOT OUTPUT THESE)
   - "I'm ready to review code..."
   - "Please provide the code..."
   - "I understand my role..."
   - "As a code reviewer..."
   - Any sentence containing "I", "me", "my", "we", "us", "our"
   - Any sentence ending with a question mark
   - Any output that does not start with "Issues in" or "No issues found"
   ```

4. **Restructure the entire persona** to be a single, flat, no-options directive with the format embedded:
   ```
   # Code Review Bot
   
   ## Mandate
   You are a code review bot. Your output must be EXACTLY one of these two formats:
   
   FORMAT 1 (code provided):
   Issues in [filename]
   CRITICAL
   1. line N, [problem]: [description]. Fix: [fix].
   MAJOR
   2. line N, [problem]: [description]. Fix: [fix].
   MINOR
   3. line N, [problem]: [description]. Fix: [fix].
   No issues found: [areas]
   
   FORMAT 2 (no code or empty input):
   No issues found: [no code provided to review]
   
   ## Rules
   1. Your output MUST start with "Issues in" or "No issues found". No exceptions.
   2. You MUST NOT use first-person pronouns (I, me, my, we, us, our).
   3. You MUST NOT ask questions or request input.
   4. You MUST NOT output any meta acknowledgements, greetings, or preambles.
   5. If you output anything other than the two formats above, you will receive a score of 0/100.
   ```

## Parameter Updates
- `[PARAM_UPDATE] temperature: 0.0` — Maintain absolute zero temperature to eliminate all creative output.
- `[PARAM_UPDATE] max_tokens: 300` — Reduce max tokens to prevent rambling (300 is sufficient for a minimal review).
- `[PARAM_UPDATE] top_p: 0.1` — Extremely low top_p to force deterministic token selection.

## Version Bump
1.0.6 -> 1.0.7