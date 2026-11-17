# VeraAfrika — Claude Code project instructions

VeraAfrika helps African businesses find procurement opportunities they can act on, and helps buyers and institutions find capable, evidence-backed companies. The first milestone is one source-backed opportunity workflow in one pilot market (Senegal). Source of truth for scope and architecture:

- `handoff/README.md`, `handoff/Engineering.md`, `handoff/Access-and-decisions.md`
- High-Level Architecture v1.4 and Shared Foundation LLD v1.4 (`handoff/Originals/Project/current 0001/`)

The handoff snapshot under `handoff/` is a checksummed archive. Do not edit, add or delete files inside it. Put new work alongside it and record new revisions separately (see `handoff/Recovery.md`).

## Architecture guardrails

- Modular monolith with PostgreSQL as the system of record (HLA §4, §7.1). Do not add microservices, event streaming or a separate search engine without measured justification.
- The server builds the authorized response. Never send restricted fields to the browser and hide them with CSS, blur or disabled controls (LLD §4).
- Never accept organization, role or plan from an unsigned browser claim.
- Source values are assertions with provenance. Corrections supersede; they never overwrite raw records.
- Side-effecting POST routes require `Idempotency-Key` (LLD §6.2).
- Demo and sample data stays labeled as illustrative. Real customer data, identity documents and credentials never go into static demos.

## Brand

- Approved palette: Navy `#17324D`, Gold `#C9932F`. Use `handoff/Brand/VeraAfrika-lockup.png` and `handoff/Brand/VeraAfrika-V-mark.png` unchanged; keep exact V-mark geometry.
- Country maps are for geographic data visualization only, never as brand marks.
- Accessible usage of the palette is defined in `docs/UX_DESIGN_STANDARDS.md` §4 and takes precedence over older prototype styling.

## UX and Design Quality Policy

For every UI feature, redesign, or interface modification:

1. Read `docs/UX_DESIGN_STANDARDS.md`.
2. Apply relevant UX principles.
3. Preserve approved branding and design patterns.
4. Verify functionality, responsiveness, and accessibility.
5. Run applicable automated tests.
6. Produce a weighted UX quality score.
7. Report defects and outstanding risks.

A score of 90/100 is the release target.
Critical defects block release regardless of score.

Do not claim a test passed unless it was executed.
Do not deploy or publish without explicit approval.

Use `/ux-review` (`.claude/skills/ux-review/SKILL.md`) for a full audit. An audit reports findings and does not modify application code.

## Reporting UI work

For every completed feature, provide the deliverables in §12 of the standards:

1. Summary of what was built or changed
2. UX principles applied and why
3. Screens and workflows tested
4. Accessibility and responsiveness findings
5. Weighted UX score (1–5 per category, weighted to 100, §9)
6. Outstanding defects and severity
7. Recommended improvements
8. Release recommendation

Include the exact command and result for every test run, and list anything not tested.
