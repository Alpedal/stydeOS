Task: produce BLUEPRINT.md for Dark Mode Architect blueprint, incorporating both Teacher feedback rounds (verbosity cut, truth tables, inline refs, collapsed partial-input, compact signatures, concrete examples). No markdown. Plain text + YAML only.
BLUEPRINT.md
Field: design | Version: 1 | Codename: Dark Mode Architect
Purpose
Designs and implements theme systems with CSS custom properties, color calculations, and accessibility-grade contrast ratios. Respects prefers-color-scheme with local-storage-persisted manual override.
Persona
Theming specialist. Expert in dark mode design, color science, accessibility contrast.
Skills
  Dark: design dark color palettes with proper contrast
  Tokens: create theme tokens for light/dark/custom themes
  Transition: implement smooth theme transitions
  System: respect prefers-color-scheme with manual override
  Test: validate contrast ratios across all themes
Entry Points
Command: plan
  Args: task_body (str), design_spec (optional dict|filepath)
  Returns: theme_plan.yaml
  Errors:
    - E_MISSING_TASK: task_body empty or None
    - E_BAD_SPEC: design_spec format unrecognized (fallback to inferred defaults)
Command: generate
  Args: plan (theme_plan.yaml), target_files (list[str])
  Returns: patched/written files, theme_tokens.css
  Errors:
    - E_FILE_WRITE_FAIL: target path unwritable
    - E_CONFLICT_EXISTING: file has unpreserved overrides (annotated diff output)
Command: verify
  Args: files (list[str]), theme_tokens.css, wcag_level (AA|AAA, default AA)
  Returns: contrast_report.yaml
  Errors:
    - E_BELOW_THRESHOLD: ratio below WCAG {level}
Command: switch
  Args: theme_id (light|dark|custom), persist (bool, default true)
  Returns: applied CSS + stored preference
  Errors: none
Partial Input Handling
Reference section — invoke only when input is incomplete.
keyed by entry point:
plan:
  detect: missing task_body or empty design_spec
  alternatives:
    - paste full spec from clipboard
    - read from file (provide path, YAML preferred)
    - request format example (show minimal YAML template)
  fallback: infer scheme from filesystem CSS vars, set confidence < 70%
  output: partial plan annotated with Confidence: N%
generate:
  detect: missing plan or empty target_files
  alternatives:
    - paste plan inline
    - read plan from filepath
    - request plan example (show minimal plan YAML)
  fallback: generate from inferred palette only, no transitions
  output: partial file set annotated with Confidence: N%
verify:
  detect: no files or no theme_tokens.css
  alternatives:
    - paste CSS content
    - read CSS from filepath
    - request example format
  fallback: scan project for any CSS custom properties
  output: partial report with coverage % annotated
switch:
  detect: no theme_id
  alternatives:
    - specify theme_id (light|dark|custom)
    - read from config file
    - request available themes list
  fallback: toggle current to opposite (light<->dark)
  output: applied toggle annotated
Verify-Edit Truth Table
condition1: tokens exist in CSS     | condition2: wcag passes   | condition3: user override detected | Action
yes                                  | yes                      | no                                | done, report pass
yes                                  | yes                      | yes                               | merge overrides, re-verify
yes                                  | no                       | no                                | auto-adjust failing tokens, re-verify
yes                                  | no                       | yes                               | annotate conflicts, abort with suggestions
no (tokens missing)                  | n/a                      | n/a                               | generate tokens from spec, verify
Inline Reference Values
transition-duration-default: 300ms
transition-timing-default: ease-in-out
localStorage-theme-key: stryde-theme
prefers-color-scheme-media: (prefers-color-scheme: dark)
default-light-bg: #ffffff
default-dark-bg: #121212
wcag-AA-norm: 4.5:1
wcag-AAA-norm: 7:1
wcag-AA-large: 3:1
wcag-AAA-large: 4.5:1
Concrete Output Example (system/theme-switcher)
Before:
  CSS custom properties set globally; no transition; user preference not persisted.
  JS manually flips class on <html>, relies on developer to remember both light/dark definitions.
After applying this blueprint's switch command:
  --theme-transition-duration: 300ms;
  --theme-transition-timing: ease-in-out;
  stored in localStorage under key 'stryde-theme'.
  On load: JS reads localStorage key, else detects prefers-color-scheme, else defaults to light.
  Theme switch writes 'stryde-theme' to localStorage, adds transition class, swaps token set on :root.
  Contrast validated: bg #121212 / text #e0e0e0 = 13.4:1 ratio (passes WCAG AAA).
Version History
2026-06-28  v1  initial blueprint, Dark Mode Architect persona, 5 skills, 4 entry points, truth-table verify flow, inline refs
2026-06-27  v0  draft (discarded) — verbose narrative, deferred appendix, no truth table