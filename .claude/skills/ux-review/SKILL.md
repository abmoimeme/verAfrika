---
name: ux-review
description: Audit a VeraAfrika UI against the 20 UX principles, Nielsen heuristics and WCAG 2.2 AA, run available tests, compute the weighted 100-point score, and return defects plus a prioritized improvement plan. Read-only; never modifies application code.
argument-hint: "[page, route, component or folder to review — defaults to UI changed since last commit]"
disable-model-invocation: true
---

# /ux-review — VeraAfrika UX audit

You are running a **read-only audit**. Report findings; do not fix them.

## Hard rules

- Do **not** edit, create or delete application code, styles, tests, fixtures or configuration. The only file you may write is the report at `reports/ux/YYYY-MM-DD-<scope-slug>.md`.
- Do **not** install packages, deploy, publish or push. If a tool is missing, record it as "not available" and continue.
- Do **not** report a test or check as passed unless you executed it in this session. Include the exact command and a summary of its output for every executed check.
- If something can't be verified, mark it **Not verified**. The affected scorecard category is then **Incomplete**.
- Follow CLAUDE.md. Where the standards conflict with authorization, provenance or source-rights rules, the architecture rule wins.

## Inputs

- `$ARGUMENTS`: the scope (route, page, component or folder). If empty, use UI files changed since the last commit (`git diff --name-only HEAD`). If there is no git history, ask the user which screen to review.
- `docs/UX_DESIGN_STANDARDS.md` is the rubric. Read it fully before starting.

## Procedure

### 1. Establish scope
- List the screens, states (default, loading, empty, error, restricted, amended) and journeys (J1–J10 in standards §8.2) that the scope touches.
- Note the build, commit and the server you reviewed against.

### 2. Inspect the UI
- Read the relevant HTML, templates, components, CSS and tokens.
- If the app can run locally, start it (read-only use of existing scripts only) and open each in-scope screen with the available browser tooling.
- Capture screenshots at 320, 375, 768, 1280 and 1440 px if a browser tool exists.

### 3. Run available checks
Detect what exists, run it, and record the results. Do not install anything.

| Check | How to detect | Run |
|---|---|---|
| Unit and integration tests | `package.json` scripts, `pytest.ini`, `pyproject.toml` | `npm test` / `pytest -q` (scoped where possible) |
| End-to-end tests | `playwright.config.*` | `npx playwright test <scope>` |
| Accessibility scan | `@axe-core/playwright` or `axe-core` in dependencies | axe on each in-scope page and state |
| Contrast | Token values in CSS | Compute WCAG contrast ratios for every text/background and UI/background pair in scope |
| Static a11y grep | Always available | `outline:none` without replacement, clickable `div`/`span`, `<img>` without `alt`, inputs without `<label>`, missing `lang`, font sizes < 12 px, missing `prefers-reduced-motion` |
| Keyboard | Browser tool available | Tab through each screen: order, visible focus, no traps, modal focus return, 2.4.11 not obscured |
| Restricted data | API tests or network inspection | Confirm restricted fields are absent from responses and DOM for lower tiers and other organizations |

### 4. Assess
- **20 UX principles** (standards §2: Hick's Law through Pareto Principle): Pass / Partial / Fail / N/A for each, with evidence (file:line, screenshot or observed behavior). Treat them as heuristics; where two conflict, note how accessibility and task requirements resolve it.
- **Mandatory implementation requirements** (standards §4): check each one, including the VeraAfrika-specific rules.
- **Nielsen H1–H10:** findings rated cosmetic, minor, major or critical.
- **WCAG 2.2 AA:** cite the success criterion number for each finding. Always check the 2.2 additions (2.4.11, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8).
- **VeraAfrika specifics:** source, observation date and freshness on facts; amendments visible; sample data labeled; honest tier gating; brand assets unchanged; gold-on-light used only as allowed in standards §4.2.

### 5. Score
- Score each of the seven categories from 1 to 5 using the definitions in standards §9.1, citing the defect IDs and evidence behind each score.
- Show the arithmetic: Σ (score ÷ 5 × weight) = total out of 100.
- Mark categories with unverified items as **Incomplete**. If any category is Incomplete, the total is provisional and cannot support a release decision.
- Apply the release bands (90+ / 75–89 / below 75) and check the critical-defect list (standards §11.2). Any critical defect blocks release regardless of score.

### 6. Defects
Number them `UX-001`, `UX-002`, and so on. Each entry: severity, location, evidence, violated principle / heuristic / WCAG criterion, user impact, recommended fix, effort (S/M/L).

### 7. Improvement plan
Order items using standards §10: critical → primary-journey majors → accessibility majors → other majors → high-reach minors → cosmetic. Within a tier, rank by user impact, usability evidence, effort and business value. Give each item its effort (S/M/L) and the category score it would raise. Group the plan into "Before release", "Next iteration" and "Backlog".

### 8. Report
Write the report to `reports/ux/YYYY-MM-DD-<scope-slug>.md` with: scope; the eight deliverables in standards §12 (adapted for an audit: what was reviewed instead of what was built); the 20-principle table; heuristic and WCAG findings; tests run with commands and results; tests not run and why; the improvement plan; risks and assumptions. Then reply with:
- Score (and whether it is provisional)
- Release recommendation: **Ready** or **Not ready**, with the blocking reasons
- Count of defects by severity
- Top 5 improvements
- The checks that were not run and why

End by asking whether the user wants any fixes implemented. Implementation happens only after they say so, in a separate step.
