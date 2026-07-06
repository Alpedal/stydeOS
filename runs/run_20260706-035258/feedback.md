## What Went Wrong
- The agent output consists only of a preamble/acknowledgment message ("I understand my role... Please provide the code...") rather than performing any actual code review or producing working output.
- This is a complete failure to execute the core task: reviewing code. The output contains no code critique, no analysis, no review content.
- The self-evaluation score of 30/100 confirms the agent recognized it did not deliver on the task.

## Which Rules Were Broken
- **Behavior Rule 1**: "Deliver working output, not descriptions." — The agent delivered a description of its role and a prompt for input, not working output.
- **Behavior Rule 2**: "One task at a time. Complete it before moving on." — The agent never started the review task.
- **Behavior Rule 4**: "Prioritize correctness over cleverness." — The agent failed to produce any correct output at all.

## Proposed Fixes
Add the following rule to the Behavior Rules section of `persona.md` (after rule 4):

> 5. **No preamble or waiting for input.** When given a code snippet, immediately produce the review. Do not acknowledge the role, ask for the code, or describe what you will do. Start directly with the review output.

Additionally, modify the Context section to include a situational trigger:

> **Context** — You are a specialized AI agent operating within the Forge v2 (Crucible) framework. You will receive code as input. Your ONLY output is the code review itself. Do not output anything else — no greetings, no confirmations, no questions.

## Parameter Updates
No hyperparameter changes needed. The failure is behavioral (output format/rule compliance), not due to temperature, token limits, or sampling.

## Version Bump
1.0.0 -> 1.0.1