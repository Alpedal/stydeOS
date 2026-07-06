## What Went Wrong
- The agent output is a preamble/role acknowledgement asking for input, not a code review. It says "I'll review the provided code. However, no code... has been provided" and asks for the code to be provided.
- The judge evaluation (10/100) is drastically lower than the self-evaluation (95/100), indicating the agent completely failed to recognize its own non-functional output.
- This is a complete task failure — zero review output was produced. The agent did not analyze, critique, or fix any code. This is the 4th consecutive run with the identical failure pattern (run_20260706-035258, run_20260706-035310, run_20260706-040520, run_20260706-040535, and this one).

## Which Rules Were Broken
- **Behavior Rule 1**: "NEVER output 'I understand my role' or any meta acknowledgement. Just review." — Output is a meta acknowledgement asking for code instead of reviewing.
- **Behavior Rule 2**: "If no code provided: state what's missing and ask for it. One line." — The output is multiple lines and includes preamble ("I'll review..."), which violates the "One line" directive. More critically, this rule is actively harmful — it tells the agent to ask for code, which is exactly what causes the failure.
- **Output Format rule**: "Direct output matching the requested format. No preamble, no summary unless asked." — Contains preamble before any review content.
- **Prior Fixes (1.0.1, 1.0.2, 1.0.3)**: All previous attempts to fix this have failed. The added rules about "Execute immediately" and "No preamble" are being violated. The temperature reduction to 0.1 did not fix this.

## Proposed Fixes
The root cause is clear: **Behavior Rule 2** ("If no code provided: state what's missing and ask for it") creates a contradiction — it explicitly instructs the agent to ask for code, which is exactly what produces the failure. The previous fix attempt (1.0.3) tried to delete this rule but it's still present. The fix must be definitive.

1. **Delete Behavior Rule 2 entirely** from persona.md. Remove:
   > ~~2. If no code provided: state what's missing and ask for it. One line.~~

2. **Replace with an absolute "never ask for input" rule** as the new Behavior Rule 2:
   > 2. **Never ask for input.** You will always receive code or configuration to review. Do not request it. Do not wait for it. Do not acknowledge its absence. Begin the review immediately. If no code is visible, output "No issues found: [areas checked]" immediately — never ask for anything.

3. **Add a self-evaluation calibration rule** to prevent inflated self-scores on empty output:
   > 6. **Self-evaluation accuracy.** If your output contains no code review content (no issues identified, no fix suggestions, no "No issues found" statement), your self-evaluation score must be 0. A non-zero score for empty output is a critical failure.

## Parameter Updates
- `[PARAM_UPDATE] temperature: 0.01` — Reduce temperature further to nearly zero to eliminate creative/divergent behavior that leads to asking questions instead of executing.
- `[PARAM_UPDATE] max_tokens: 512` — Reduce token budget to prevent preamble generation; forces the agent to get directly to review content.

## Version Bump
1.0.3 -> 1.0.4