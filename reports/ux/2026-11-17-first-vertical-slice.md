# UX review — First vertical slice (pilot UI)

Date: 17 Nov 2026 · Standard: `docs/UX_DESIGN_STANDARDS.md` v1.0 · Reviewer: Claude (build + self-review; not an independent review)
Scope: `web/` (customer, analyst and auditor views) against the API in `app/`. Server: local dev, synthetic Senegal notice, sample companies.

## 1. Summary of what was built

One source-backed tender workflow, end to end:

- **Analyst:** run the approved synthetic source. Unapproved sources are blocked. Review the extracted fields beside the raw record, correct them with a reason, publish, and trace any field back to its amendment and ingestion run.
- **Customer (Compete):** search tenders in Senegal, open one, open the original source, save it, and start a bid. Bid creation is idempotent. The customer gets an alert when the issuer moves the deadline.
- **Customer (Discover):** the same tender with restricted fields absent from the API response. A plain message says which plan is required.
- **Auditor:** reads the append-only audit log.

French and English throughout. The French default follows the user's locale.

## 2. UX principles applied

| # | Principle | Status | Evidence |
|---|---|---|---|
| 1 | Hick's Law | Pass | One primary action per screen (Start a bid / Approve and publish). Filters reduced to keywords, country, sector. |
| 2 | Fitts's Law | Pass | All buttons and links in actions are ≥ 44 px tall (`.btn`, `.btn-link`, nav). The bid button sits with the deadline. |
| 3 | Jakob's Law | Pass | Standard header nav, search form, cards, tables, modal dialog. |
| 4 | Proximity | Pass | Deadline, days left, amendment note and actions share one panel. Source and observation date sit together. |
| 5 | Miller's Law | Pass | Tender detail split into Summary, Lots, Requirements, History, Fit, Source. Sector filter starts at the 13 sectors. |
| 6 | Doherty Threshold | Partial | Skeletons, `aria-busy` and live-region feedback are in place. Response times were not measured on a slow network. |
| 7 | Von Restorff | Pass | Gold is reserved for the single primary action and the amendment note. |
| 8 | Target Distance | Pass | Corrections are made inline on the field row. Confirmation sits next to the trigger. |
| 9 | Serial Position | Pass | Tenders first for customers, review queue first for analysts. |
| 10 | Peak-End | Partial | A success message on bid start states the next steps. The bid workspace itself is minimal (UX-007). |
| 11 | Zeigarnik | Partial | Review queue shows open and overdue work. Bids show days left. No progress checklist yet. |
| 12 | Prägnanz | Pass | Plain cards on a calm background; no decorative charts. |
| 13 | Similarity | Pass | One badge system, one deadline panel and one notice style across all views. |
| 14 | Uniform Connectedness | Pass | Amendment history is attached to the deadline panel. Trace chain visually links versions. |
| 15 | Tesler's Law | Pass | Entitlements, provenance and versioning are handled by the server. Users see outcomes and plain gates. |
| 16 | Postel's Law | Partial | Server validates deadline input and requires a time zone. French date input (`15/12/2026`) is rejected with guidance rather than accepted. |
| 17 | Error Prevention | Pass | Confirm before bid; reason required for corrections; idempotent retry reuses the same key. |
| 18 | Parkinson's Law | Pass | Bid starts in two clicks from the tender. Company is prefilled from the organization. |
| 19 | Occam's Razor | Pass | No features shown that don't work. Unbuilt workspace features are stated, not mocked. |
| 20 | Pareto | Pass | Build and test effort concentrated on find → verify → bid and amendment tracing. |

## 3. Screens and workflows tested (executed)

| Check | Command | Result |
|---|---|---|
| API acceptance tests (HLA §12.1, LLD §11, J3–J8) | `pytest -q` | **26 passed**, 1 skipped (browser suite, run separately) |
| Browser journey J1–J8 + sign-in, sources, review, trace, audit | `VERAFRIKA_E2E_URL=http://localhost:8077 AXE_PATH=…/axe.min.js pytest tests/e2e -q` | **1 passed** (single scripted journey covering 13 screens/states) |
| axe-core 4.x, tags wcag2a/aa, wcag21a/aa, wcag22aa | inside the browser journey | **0 violations on 13 screens/states** (`reports/ux/e2e/axe-results.json`) |
| Reflow | browser journey | No horizontal page scroll at 375 px on 10 screens; at 320 px on the Discover detail page (EN) |
| Keyboard | browser journey | First Tab reaches the skip link; dialog opens with focus on the confirm button; Escape returns focus to the trigger |
| Token contrast | `pytest tests/test_design_tokens.py` | All text pairs ≥ 4.5:1; input borders, focus rings ≥ 3:1; brand values unchanged; no text below 12 px |
| Visual inspection | screenshots at 375 and 1280 px in `reports/ux/e2e/` | Reviewed; issues logged below |

## 4. Accessibility and responsiveness findings

Defects found and **fixed during this build** (each re-verified by the commands above):

| Finding | WCAG | Fix |
|---|---|---|
| Initial page load moved focus to the heading, skipping the skip link | 2.4.1, 2.4.3 | Focus moves only on in-app navigation |
| Review screen scrolled horizontally at 375 px | 1.4.10 | Grid columns use `minmax(0, 1fr)` |
| Screen-reader-only labels escaped table scroll containers | 1.4.10 | `.table-wrap` positioned |
| Scrolling tables not reachable by keyboard (axe, serious) | 2.1.1 | Scrolling table regions become focusable, labeled regions |
| Sticky header ~190 px tall on phones could hide focused content | 2.4.11 | Header is static below 860 px |
| Gold text on white in prototypes (2.73:1) | 1.4.3 | Not used. Approved `--gold-text #8E6821` for light surfaces |

Other UX defects fixed: logo wordmark illegible (display-cropped the approved PNG, file unchanged); deadline and bid button buried at the bottom on mobile (now first); match explanations in English inside the French UI (now translated codes).

## 5. Weighted UX score

| Category | Weight | Score (1–5) | Points | Basis |
|---|---|---|---|---|
| Usability and navigation | 20 | 4 | 16.0 | Primary journeys complete quickly; minor gaps UX-002, UX-004 |
| Visual hierarchy and consistency | 15 | 4 | 12.0 | Brand and tokens consistent; UX-003, UX-005 |
| Functional completeness | 20 | 4 | 16.0 | All journeys real and working; workspace minimal (UX-007); J10 not exercised |
| Accessibility and responsiveness | 15 | 4 | 12.0 | **Incomplete**: no screen-reader pass, no 200% zoom test, only Chromium |
| Performance and feedback | 10 | 4 | 8.0 | **Incomplete**: no slow-network measurement |
| Error prevention and recovery | 10 | 4 | 8.0 | **Incomplete**: J9 network failure not executed in a browser (idempotent replay verified at the API) |
| Localization and content clarity | 10 | 3 | 6.0 | UX-001 (taxonomy labels English only), UX-006; French not reviewed by a fluent speaker |
| **Total** | 100 | | **78.0** | **Provisional** |

Band: **75–89, requires refinement.** The score is provisional because three categories are Incomplete.

## 6. Outstanding defects

| ID | Severity | Location | Issue | Fix | Effort |
|---|---|---|---|---|---|
| UX-001 | Major | Tender detail, sector filter | VA taxonomy has English labels only, so the French UI shows English sector names | Add French labels to the taxonomy as v1.1 (taxonomy owner), resolve labels by locale | M |
| UX-002 | Minor | Plan gates | Gates state the required plan but give no way to learn more or request an upgrade | Add a plan comparison page or contact path once pricing is approved | S |
| UX-003 | Minor | Header, mobile | Signed-in line and three buttons take ~190 px on phones | Move profile and language into a compact menu on small screens | S |
| UX-004 | Minor | Review task | One textarea serves as both approval note and rejection reason | Separate fields; show the reject reason only when rejecting | S |
| UX-005 | Minor | Review task, 375 px | Field table scrolls sideways (permitted) and is cramped | Stack rows as cards below 640 px | S |
| UX-006 | Minor | Source and sample names | Source name, attribution and "(sample)" org names are English-only data | Add localized display names to source and organization records | S |
| UX-007 | Minor | Bid workspace | Workspace shows status and deadline only (honestly disclosed) | Requirements checklist and document tasks (next slice) | L |
| UX-008 | Cosmetic | Fit panel | Score 85/100 has no explanation of the scale | Add a one-line "how this is calculated" disclosure | S |

**Critical defects: none found in the tested scope.**

## 7. Recommended improvements (prioritized)

**Before pilot users see it**
1. UX-001: French taxonomy labels (raises Localization to 4, +2 points).
2. Run the missing checks: NVDA or VoiceOver pass, 200% zoom, Safari and Firefox, Android Chrome on a real device, a throttled-network run, and J9 and J10 in the browser. This clears the "Incomplete" marks.
3. A fluent French speaker reviews all strings, including the analyst views.

**Next iteration:** UX-003, UX-004, UX-005, UX-002, UX-006.

**Backlog:** UX-007 bid workspace content; UX-008 score explanation.

## 8. Release recommendation

**Not ready for release.** It's fine to demo internally on synthetic data. Blocking reasons:

- The score is provisional (78) and below 90.
- Mandatory checks in standards §11.1 weren't performed: screen reader, fluent-speaker review, cross-browser.
- The data and security decisions in `handoff/Access-and-decisions.md` are still open: source rights, OIDC provider, hosting region.

## 9. Risks and assumptions

- This review was done by the same agent that built the UI. Standards §11 and CLAUDE.md favor an independent `/ux-review` before any release decision.
- **Deadline amendments go live before analyst confirmation.** They are shown with an "issuer amendment — confirmation in progress" label. This is a deliberate default because deadline freshness is material (HLA risk table). It needs product sign-off.
- **Compete allows one active bid workspace at a time.** This reads the LLD's Grow-only `bid.multiple` permission as a limit. Product hasn't approved it yet.

---

## Addendum: staging sign-in for pilot customers (17 Nov 2026, later the same day)

**Built:**
- Invite-only accounts: email + password, with French/English sign-in, invitation and password-reset screens.
- Staff must use an authenticator app (TOTP). Codes can't be replayed.
- Lockout after 5 failures; limit per IP address.
- Sign-out ends the session on the server.
- Server hardening: strict CSP, HSTS, frame and nosniff headers; the cross-site write check; API docs and the development profile picker disabled outside development.

**Tests run (executed):**

| Check | Command | Result |
|---|---|---|
| API suite, including 10 new sign-in tests | `pytest -q` | **37 passed**, 2 skipped (browser suites run separately) |
| Staging browser journey: invitation → password rules → authenticator setup (wrong then correct code) → publish → sign out → customer signs up and starts a bid → password sign-in | `VERAFRIKA_STAGING_URL=… pytest tests/e2e/test_staging_e2e.py` | **Passed** at 390 px |
| axe-core on sign-in, invitation, authenticator setup and the customer bid page | inside that journey | **0 violations** |
| Development journey re-run after the changes | `pytest tests/e2e/test_journeys_e2e.py` | **Passed**; 13 screens, 0 axe violations (one earlier run failed because the server was still restarting; re-run passed) |
| Clean-copy staging run on an empty database | uvicorn from only the files the Dockerfile copies | Migrations 001–004 applied on start; `/docs`, `/openapi.json`, dev personas and dev sessions return 404 |
| Docker image build | `docker build` | **Not run.** Docker Hub is blocked from the build workspace. The first build happens on the host |

**Defects found and fixed during this work:**
1. Every 401 error said "session expired, choose a profile again", including a mistyped password.
2. The password field was unstyled and tiny.
3. The staging footer said all data was sample data, although accounts are real.
4. There was no real password-reset path. Added `reset-access`, with an optional authenticator reset.

**New open items:**

| ID | Severity | Issue | Fix |
|---|---|---|---|
| UX-009 | Minor | Authenticator setup on desktop shows a key to type, with no QR code | Render a QR code server-side as SVG |
| UX-010 | Minor | No self-service password reset; the pilot lead issues links | Add once email delivery is chosen |

**Score:** unchanged at **78, provisional**. The sign-in work fixed the errors it introduced and passed its own checks. The open items limiting the score (French taxonomy labels, screen reader, cross-browser, fluent-French review) haven't changed.

**Release recommendation for pilot customers: not ready under §11**, unless the project owner accepts the risk in writing. Deploying staging and inviting VeraAfrika staff first is within the standards.
