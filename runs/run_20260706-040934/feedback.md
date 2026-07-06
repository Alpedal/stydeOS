## What Went Wrong
- **Complete task failure**: Agent output is a single-line request for code input instead of performing any code review.
- **Self-evaluation (0/100)**: Agent correctly identified complete failure.
- **Judge evaluation (50/100)**: Judge gave half credit despite zero review content — this is inflated and enables the behavior.
- **This is the 8th consecutive run** showing the identical failure pattern: agent asks for code rather than producing review output. The previous fix attempts (1.0.3, 1.0.4, 1.0.5) have all failed to resolve this.
- **The fix from 1.0.5 explicitly added a "no-ask" rule and "first token" constraint**, yet the agent still outputs "I'm ready to review code" — indicating the persona rules are not being enforced or the agent is ignoring them.

## Which Rules Were Broken
- **Behavior Rule 1**: "NEVER output 'I understand my role' or any meta acknowledgement. Just review." — "I'm ready to review code" is functionally identical to the forbidden meta acknowledgement.
- **Behavior Rule 7 (from 1.0.5)**: "Zero preamble. Your first sentence must be the first line of the review format." — Output is pure preamble with zero review content.
- **First token rule (from 1.0.5)**: "Your output must begin with exactly one of these three tokens: 'Issues in', 'No issues', or 'Issues found'." — Output begins with "I'm ready".
- **Behavior Rule 6 (from 1.0.5)**: "No asking for input." — Output explicitly asks for input.
- **Behavior Rule 2 (replacement from 1.0.5)**: "Forced output. You will always produce a complete review in the required format." — Output is not a review.

## Proposed Fixes
The root cause is that the agent's system prompt (persona.md) is being overridden or ignored by the model's training. The fixes must be more aggressive and structural:

1. **Replace the entire Behavior Rules section** with a single, unbreakable directive:
   ```
   ## Mandate
   You are a code review bot. Your only possible output is a code review in the exact format below. You cannot output anything else — not a greeting, not a question, not an acknowledgement. If the input is empty or not code, output exactly: "No issues found: [no code provided to review]". No exceptions.
   ```

2. **Add a "no first-person" rule** to prevent any agent self-reference:
   > 8. **No first-person pronouns.** Never use "I", "me", "my", "we", "us", or "our" in any output. You are not a person. You are a review formatter.

3. **Add a "strict format template"** that must be filled verbatim:
   > **Required output template.** Your output must exactly match one of these two templates:
   > Template A (code present): `Issues in [filename]\nCRITICAL\n...\nMAJOR\n...\nMINOR\n...\nNo issues found: [areas]`
   > Template B (no code): `No issues found: [no code provided to review]`
   > Any deviation from these templates is a failure. Fill in the bracketed sections only.

4. **Add a "zero-tolerance failure" rule**:
   > 9. **Zero-tolerance for non-review output.** Any output that is not a valid review in the required format will be scored 0/100. This includes greetings, questions, acknowledgements, explanations, apologies, and requests for input.

5. **Restructure the persona to be a single block** with no section headers that might be parsed differently:
   > Remove all section headers (## Role, ## Voice & Tone, ## Behavior Rules, ## Output Format, ## Context). Replace with a single flat directive: "You are a code review bot. Your output must be one of two exact formats: ..."

## Parameter Updates
- `[PARAM_UPDATE] temperature: 0.0` — Absolute zero temperature to eliminate all creative output and force deterministic behavior.
- `[PARAM_UPDATE] max_tokens: 500` — Ensure sufficient tokens for a full review but not so many that the model rambles.

## Version Bump
1.0.5 -> 1.0.6