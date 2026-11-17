# VeraAfrika UX Design and Quality Standards

Version 1.0 · Approved by the project owner 17 Nov 2026 · Applies to every application, website, dashboard and feature in the VeraAfrika project. That includes the customer platform, the analyst console, internal tools and any prototype shown to prospects.

The base standard is the project owner's **Universal UX Design and Quality Standards**: 20 UX principles, supplemented by Nielsen's usability heuristics and WCAG 2.2 AA. This document applies that standard to VeraAfrika and adds project-specific rules for brand, data provenance and access control. Where a UX recommendation conflicts with the authorization, provenance or source-rights rules in CLAUDE.md, the architecture rule wins.

> The goal is not merely to create attractive interfaces. The goal is to build reliable products that users can understand, trust, and use effectively.

---

## 1. Users and primary journeys

| Audience | Main objective | What the interface must make obvious |
|---|---|---|
| Supplier (SME) | Find a relevant tender, check the issuer and changes, start a bid before the deadline | Deadline, time remaining, latest amendment, source link, what their plan allows |
| Buyer / institution | Find capable companies and understand the evidence behind a match | Evidence, confidence, freshness, gaps and limitations |
| Analyst | Review an ingested notice, correct fields, publish, trace an amendment | Raw source beside extracted fields, what changed, who changed it, queue age |
| Auditor / admin | Reconstruct a decision | Actor, time, object, before and after values, source record |

**Context to design for:** French and English (French is primary in Senegal and Côte d'Ivoire), mid-range Android phones, slow or intermittent connections, shared office devices, and users new to digital procurement.

---

## 2. The 20 UX principles

Treat these as design heuristics, not rigid rules. Resolve conflicts using user research, accessibility and task requirements.

| # | Principle | Rule | VeraAfrika application |
|---|---|---|---|
| 1 | Hick's Law | Reduce unnecessary decisions. | One primary action per screen (for example "Start bid"). Filters default to the user's country and sectors. |
| 2 | Fitts's Law | Make important controls easy to reach and activate. | Primary actions are large and placed within thumb reach on mobile. Targets ≥ 24 × 24 px, 44 × 44 px on touch screens. |
| 3 | Jakob's Law | Use familiar interface conventions. | Standard tables, filters, tabs, search and forms. No novel navigation patterns. |
| 4 | Proximity | Group related information. | Deadline, time remaining and amendment marker sit together. Source and observation date sit next to the fact they support. |
| 5 | Miller's Law | Organize information into understandable chunks. | Tender detail in short sections (Summary, Eligibility, Documents, History). Taxonomy drills Sector → Cluster → Industry, never a flat 156-item list. |
| 6 | Doherty Threshold | Optimize responsiveness and give immediate feedback. | Visual acknowledgement within 100 ms, results within 400 ms where possible, otherwise skeletons or progress. |
| 7 | Von Restorff Effect | Highlight important actions. | Gold accent reserved for the single most important action or alert (deadline changed, closing soon). Never used decoratively next to it. |
| 8 | Target Distance | Minimize pointer and touch movement. | Row actions on the row; confirmation next to the trigger; analysts correct a field where it is displayed. |
| 9 | Serial Position | Prioritize important navigation items. | Opportunities and bids first, help and settings last. Analyst queue first in the console. |
| 10 | Peak-End Rule | Design positive completion experiences. | A bid start ends with a clear confirmation, the deadline and the next step, not a bare toast. |
| 11 | Zeigarnik Effect | Communicate unfinished progress. | Bid workspaces show progress and outstanding requirements. Analyst queue shows items still to review. |
| 12 | Prägnanz | Prefer simple, understandable visual structures. | Plain cards and tables on a calm background. Charts only where they add meaning. |
| 13 | Similarity | Maintain component consistency. | One component per concept across the customer and analyst apps (same deadline badge, same status chips). |
| 14 | Uniform Connectedness | Clearly associate related elements. | Amendment history is visually attached to the field it changed. Source citation is enclosed with its value. |
| 15 | Tesler's Law | Manage unavoidable complexity. | The system absorbs complexity (entitlements, provenance, version history). Users see simple outcomes with details one step away. |
| 16 | Postel's Law | Handle reasonable input variations safely. | Accept French and English input, accents, `DD/MM/YYYY`, `1 234,56`, phone numbers with or without `+221`. Validate on the server. |
| 17 | Error Prevention | Prevent mistakes and support recovery. | Confirm destructive or billable actions, warn before deadlines lapse, keep drafts, retry safely (idempotency). |
| 18 | Parkinson's Law | Eliminate unnecessary workflow steps. | Start a bid in one step from the tender. Prefill known company data. No redundant entry (WCAG 3.3.7). |
| 19 | Occam's Razor | Avoid unnecessary interface complexity. | Remove fields, badges and widgets that don't serve the current task. |
| 20 | Pareto Principle | Prioritize high-value user workflows. | The find → verify → bid journey gets the most design and testing effort. |

---

## 3. Nielsen's 10 usability heuristics (supplementary)

| # | Heuristic | What reviewers check |
|---|---|---|
| H1 | Visibility of system status | Loading, saving, ingestion and review states; source freshness; "last updated" times |
| H2 | Match with the real world | Procurement vocabulary users know; FR/EN labels; local date and money formats |
| H3 | User control and freedom | Cancel, undo, back; discard draft; leave a flow without penalty |
| H4 | Consistency and standards | Shared components and tokens; platform conventions |
| H5 | Error prevention | Validation before submit; confirmations; deadline warnings |
| H6 | Recognition rather than recall | Visible options, breadcrumbs, recent and saved items |
| H7 | Flexibility and efficiency | Shortcuts, filters, saved searches, bulk analyst actions |
| H8 | Aesthetic and minimalist design | No decorative clutter; signal over noise in dashboards |
| H9 | Recognize, diagnose and recover from errors | Plain-language errors mapped from API codes (§8.3) |
| H10 | Help and documentation | Contextual help in a consistent location (also WCAG 3.2.6) |

---

## 4. Mandatory implementation requirements

Every interface must:

- Be responsive across mobile, tablet and desktop (320 px to wide desktop).
- Follow the approved design system and branding (§5).
- Use consistent typography, spacing, colors and components.
- Provide clear navigation and primary calls to action.
- Include functional buttons, forms, menus, filters and search.
- Support loading, empty, success and error states. For VeraAfrika also: restricted (tier), stale (source freshness) and amended states.
- Prevent destructive actions without appropriate safeguards.
- Support keyboard navigation and visible focus indicators.
- Target WCAG 2.2 AA accessibility (§6).
- Support required languages and localization: French and English, locale-correct dates, numbers and XOF/FCFA amounts, layouts that tolerate French strings about 30% longer.
- Avoid fake functionality, dead links and misleading placeholder data. Any sample or illustrative data must be labeled as such.
- Provide meaningful feedback for user interactions.

**VeraAfrika-specific requirements**

- Every fact shown to a customer carries its source, observation date and freshness.
- Restricted data is absent from the server response. Never blur, hide or disable it client-side.
- Locked features state the required plan plainly. No dark patterns.
- Amendments are visible on the affected field, with history one step away.

---

## 5. Brand and visual system

### 5.1 Approved assets and colors

- Lockup `handoff/Brand/VeraAfrika-lockup.png` and V-mark `handoff/Brand/VeraAfrika-V-mark.png`. Use unchanged. Do not redraw them as SVG polygons in production.
- Navy `#17324D` is the primary color. Gold `#C9932F` is the accent.
- Country maps are data visualization only, never brand marks.

### 5.2 Accessible use of the palette (measured 17 Nov 2026)

| Pairing | Contrast | Allowed use |
|---|---|---|
| Navy `#17324D` on white | 13.13:1 | Body text, headings, icons |
| Gold `#C9932F` on Navy | 4.81:1 | Text, icons and focus rings on navy surfaces |
| Navy on Gold | 4.81:1 | Text on gold buttons and badges |
| Gold on white | **2.73:1 — fails** | Decorative fills only. Never text, icons, input borders or focus indicators on light surfaces |
| White on Gold | **2.73:1 — fails** | Not allowed for text |
| Gold on `#F5F7F8` | **2.54:1 — fails** | Not for UI components that convey state |
| Muted `#6C7783` on `#F5F7F8` | 4.24:1 — fails for small text | Use on white (4.56:1) or darken |

**Approved token (project owner, 17 Nov 2026):** `--gold-text: #8E6821` (5.06:1 on white, 4.58:1 on `#FAF3E5`) for gold-colored text and icons on light backgrounds. The approved Gold is unchanged for fills and navy surfaces.

### 5.3 Tokens, type and spacing

- Use CSS custom properties; no hard-coded colors in components. Minimum token set: `--navy`, `--navy-deep`, `--gold`, `--gold-text`, `--gold-soft`, `--bg`, `--card`, `--text`, `--muted`, `--line`, `--danger`, `--success`, `--warning`, `--info`, `--focus`.
- Status color is never the only signal; pair it with text or an icon.
- Font: Inter with system fallbacks. Minimum text size 12 px; body 14–16 px; line height ≥ 1.4.
- 4 px spacing grid.

---

## 6. Accessibility: WCAG 2.2 AA

All UI meets WCAG 2.2 Level AA. These checks are mandatory; the full standard still applies.

**Perceivable**
- 1.1.1 Text alternatives for images, charts and icons; decorative images use `alt=""` or `aria-hidden="true"`; charts have a text or table equivalent.
- 1.3.1 Semantic structure: landmarks, heading order, real tables with `<th scope>`, a `<label>` for every input.
- 1.3.5 `autocomplete` on personal fields.
- 1.4.1 Color is not the only signal.
- 1.4.3 Text contrast ≥ 4.5:1 (≥ 3:1 for large text).
- 1.4.4 / 1.4.10 Works at 200% zoom and reflows at 320 px without horizontal scrolling (data tables may scroll inside their container).
- 1.4.11 Non-text contrast ≥ 3:1 for input borders, focus indicators and meaningful icons and chart marks.
- 1.4.12 Text spacing overrides don't break layout.
- 1.4.13 Hover and focus content is dismissible, hoverable and persistent.

**Operable**
- 2.1.1 / 2.1.2 Fully keyboard operable with no traps. Use `<button>` or `<a href>`, never clickable `div`s.
- 2.2.1 Session timeouts warn and allow extension.
- 2.3.3 Honor `prefers-reduced-motion`.
- 2.4.1 Skip link to main content.
- 2.4.3 Logical focus order; modals trap focus and return it on close.
- 2.4.6 Descriptive headings and labels.
- 2.4.7 Visible focus. Never `outline: none` without a replacement of ≥ 2 px and ≥ 3:1 contrast.
- **2.4.11 Focus Not Obscured (new in 2.2):** sticky headers, toasts and banners never fully hide the focused element.
- **2.5.7 Dragging Movements (new):** a single-pointer alternative exists for every drag.
- **2.5.8 Target Size (new):** pointer targets ≥ 24 × 24 CSS px.

**Understandable**
- 3.1.1 / 3.1.2 `lang` on `<html>` and on passages in another language.
- 3.2.1 / 3.2.2 No unexpected context changes on focus or input.
- **3.2.6 Consistent Help (new):** help appears in the same place on every page.
- 3.3.1 / 3.3.3 Errors identified in text, with suggestions.
- 3.3.4 Review or confirm legal, financial and bid-submission actions.
- **3.3.7 Redundant Entry (new):** don't ask for the same information twice in a process.
- **3.3.8 Accessible Authentication (new):** no cognitive tests to sign in; allow paste and password managers.

**Robust**
- 4.1.2 Custom controls expose name, role and state.
- 4.1.3 Status messages (saved, deadline changed, quota reached) use `role="status"` or `aria-live`.

### 6.1 Current baseline (handoff inspection, 17 Nov 2026)

| Finding | Where | WCAG |
|---|---|---|
| Gold text on white at 2.73:1 | Both prototypes | 1.4.3 |
| No `:focus` styles; `outline:none` present | Internal console v7 | 2.4.7 |
| About 50 font-size rules at 8–11 px | Internal console v7 | 1.4.4 risk, readability |
| Clickable `div` elements | Internal console v7 | 2.1.1, 4.1.2 |
| Only 2 `aria-` attributes | Customer prototype | 4.1.2 |
| No `prefers-reduced-motion` handling | Customer prototype (timed walkthroughs) | 2.3.3, 2.2.2 |

These are prototypes. New production UI must not inherit these defects.

---

## 7. Design and development workflow

**Before implementation**
1. Identify target users and their main objectives (§1).
2. Map primary user journeys.
3. Identify relevant UX principles (§2).
4. Review existing components and patterns.
5. Define acceptance criteria.

**During implementation**
1. Build reusable components.
2. Apply responsive layouts.
3. Implement real functionality.
4. Test edge cases and error states.
5. Validate accessibility and usability.

**After implementation**
1. Perform functional testing (§8).
2. Review all applicable UX principles.
3. Test desktop and mobile layouts.
4. Evaluate accessibility.
5. Complete the weighted UX scorecard (§9).
6. Document defects and recommendations (§10).

---

## 8. Functional testing requirements

### 8.1 Every UI change
- Unit tests for new logic (formatters, validators, state handling).
- Component or integration tests for new interactive components, including keyboard operation.
- An end-to-end test for any change that touches a primary journey.
- An automated accessibility scan (axe-core) on every changed page and state, including modals and error states.
- Layout checks at 320, 375, 768, 1280 and 1440 px.

### 8.2 Primary journey suite (must stay green)

| ID | Scenario | Expected |
|---|---|---|
| J1 | Supplier on Compete finds the pilot notice and opens it | Deadline, issuer, source link and observation date visible |
| J2 | Same user opens the original source | Link goes to the cited source record; attribution shown |
| J3 | User starts a bid, then retries the same request | One bid is created; the retry returns the same result |
| J4 | Discover user tries to start a bid | Clear "Requires Compete" message; no restricted fields in the page or network response |
| J5 | Issuer amends the deadline | User sees the new deadline, an amendment marker and an alert; old value in history |
| J6 | Analyst corrects an extracted field and publishes | Raw record unchanged; correction attributed; customer sees corrected value |
| J7 | Analyst traces a deadline to its amendment | Field → assertion → source record → ingestion run chain is visible |
| J8 | User from Org B opens Org A's bid URL | Not-found page; no data leak |
| J9 | Network fails mid-action | Error with retry; no duplicate side effect; input preserved |
| J10 | Usage limit reached | Plain message with limit, reset date and upgrade path |

### 8.3 API error to UI message mapping

| API code | UI behavior |
|---|---|
| 401 `authentication_required` | Return to sign-in, preserving the destination |
| 403 `permission_denied` | State the required plan or role. Never show the restricted value |
| 404 `resource_not_visible` | Generic not-found page; never confirm the object exists |
| 409 `idempotency_conflict` | "This request changed while it was being sent. Review and try again." |
| 422 `review_required` | Explain that analyst review is pending and the expected timing |
| 429 `usage_limit_reached` | Show limit, period end and upgrade path |
| 503 `source_temporarily_unavailable` | Show cached data with its last-success timestamp |

### 8.4 Tooling
To be added when the first production UI lands: Playwright (end-to-end and layout screenshots), `@axe-core/playwright` (accessibility), pytest (API contracts behind the UI), and a token contrast check script. Until then, reviews list each missing tool as "not available" and report no result for checks that weren't run.

---

## 9. Weighted quality scorecard

Score each category from **1 to 5**. Weighted total out of 100 = Σ (score ÷ 5 × weight).

| Category | Weight | What it covers at VeraAfrika |
|---|---|---|
| Usability and navigation | 20% | Primary journeys are easy to find and complete; navigation order; principles 1, 3, 8, 9, 20; heuristics H3, H6, H7 |
| Visual hierarchy and consistency | 15% | Brand compliance (§5), tokens, type scale, component consistency; principles 4, 5, 7, 12, 13, 14; H4, H8 |
| Functional completeness | 20% | Real, working functionality; no fake features or dead links; correct server-authorized behavior per plan and organization; provenance shown; amendments visible |
| Accessibility and responsiveness | 15% | WCAG 2.2 AA (§6); 320–1440 px layouts; touch targets; principle 2 |
| Performance and feedback | 10% | Doherty threshold; loading, success and stale states; status messages; principles 6, 10, 11; H1 |
| Error prevention and recovery | 10% | Validation, confirmations, safe retries, recoverable errors (§8.3); principles 16, 17; H5, H9 |
| Localization and content clarity | 10% | Complete FR/EN, locale formats, plain wording, labeled sample data; principles 15, 18, 19; H2, H10 |

### 9.1 Score definitions

| Score | Meaning |
|---|---|
| 5 | Excellent. Fully meets the standard; at most cosmetic issues; all relevant checks executed. |
| 4 | Good. Minor issues only, none affecting task completion. |
| 3 | Acceptable. At least one major issue with a workaround, or several minor ones. |
| 2 | Poor. Multiple major issues, or a primary task is seriously impaired. |
| 1 | Failing. The category is largely broken or contains a critical defect. |

A category with checks that weren't performed is marked **Incomplete**, scored only on what was verified, and the total is labeled **provisional**. A provisional score can't support a release decision.

### 9.2 Release targets

| Total | Meaning |
|---|---|
| 90+ | Eligible for release, subject to mandatory checks (§11) |
| 75–89 | Requires refinement |
| Below 75 | Requires significant improvement |

Critical functional, security or accessibility defects automatically block release, regardless of score.

---

## 10. Defect severity

| Severity | Definition |
|---|---|
| Critical | Blocks release. See §11.2. |
| Major | Blocks or seriously slows a primary task for some users; WCAG AA failure off the primary journeys |
| Minor | Friction, inconsistency or polish issue with a workaround |
| Cosmetic | Visual nit with no task impact |

**Prioritizing improvements:** critical → major on a primary journey → accessibility majors → other majors → high-reach minors → cosmetic. Within each tier, rank by user impact, usability evidence, implementation effort and business value. Tag each item with effort (S/M/L).

---

## 11. Release criteria

### 11.1 Release checklist
- [ ] Weighted score ≥ 90 and not provisional
- [ ] Zero critical defects
- [ ] Majors fixed, or accepted in writing by the product owner with a target date
- [ ] Primary journey suite J1–J10 executed and passing, with command output shown
- [ ] axe-core: zero serious or critical violations on changed pages
- [ ] Manual keyboard pass and one screen-reader pass (NVDA or VoiceOver) on the primary journey
- [ ] FR and EN reviewed by a fluent speaker
- [ ] Explicit approval from the project owner to deploy or publish

### 11.2 Critical defects (automatic release block)
1. A primary journey can't be completed.
2. Restricted or cross-tenant data appears in the page, network response, cache or logs.
3. A deadline, amendment or source citation is wrong, missing, or stale without disclosure.
4. Fake functionality, or sample data presented as real.
5. A WCAG 2.2 A or AA failure on a primary journey screen (for example a keyboard trap, unlabeled form control, text contrast below 4.5:1 or a missing focus indicator).
6. Data loss, or a duplicate side effect (two bids, two introductions, double usage count).
7. Brand assets altered or replaced with unapproved artwork.
8. Security-sensitive behavior relying on client-side hiding.

---

## 12. Required deliverables for every completed feature

1. Summary of what was built or changed.
2. UX principles applied and why.
3. Screens and workflows tested.
4. Accessibility and responsiveness findings.
5. Weighted UX score (category table with evidence).
6. Outstanding defects and severity.
7. Recommended improvements.
8. Release recommendation.

Never claim a test passed unless it was actually performed. Clearly identify anything not tested.

---

## 13. Continuous improvement and governance

- Review existing interfaces against these standards before adding new complexity.
- Preserve approved branding and functional workflows. Propose improvements based on user impact, usability evidence, implementation effort and business value.
- The project owner owns these standards; the brand owner approves palette and asset changes.
- Review quarterly, after WCAG updates, or after pilot user research. Record changes below.

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-11-17 | Initial standards from the project owner's Universal UX Design and Quality Standards. Approved, including the `--gold-text` token. |
