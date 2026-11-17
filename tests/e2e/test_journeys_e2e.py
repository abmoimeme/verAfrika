"""Browser journeys J1–J8 with axe-core WCAG 2.2 AA scans and screenshots.

Run against a live dev server:
  VERAFRIKA_E2E_URL=http://localhost:8077 AXE_PATH=/path/to/axe.min.js pytest tests/e2e -q
Resets the database the server uses (VERAFRIKA_DATABASE_URL, default: dev database).
"""
import json
import os
import re
from pathlib import Path

import pytest

URL = os.environ.get("VERAFRIKA_E2E_URL")
AXE = os.environ.get("AXE_PATH")
OUT = Path(__file__).resolve().parents[2] / "reports" / "ux" / "e2e"
pytestmark = pytest.mark.skipif(not (URL and AXE), reason="set VERAFRIKA_E2E_URL and AXE_PATH to run browser journeys")

AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
FINDINGS: dict = {}


@pytest.fixture(scope="module")
def browser():
    os.environ["VERAFRIKA_DATABASE_URL"] = os.environ.get("E2E_DATABASE_URL", "postgresql://postgres@/verafrika?host=/tmp/pg&port=5433")
    from app.db import connect
    from app.seed import reset
    with connect() as c:
        reset(c)
    from playwright.sync_api import sync_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        yield b
        b.close()
    (OUT / "axe-results.json").write_text(json.dumps(FINDINGS, indent=2, ensure_ascii=False))


def scan(page, name):
    page.add_script_tag(path=AXE)
    res = page.evaluate("async (tags) => await axe.run(document, {runOnly: {type: 'tag', values: tags}})", AXE_TAGS)
    FINDINGS[name] = [{"id": v["id"], "impact": v["impact"], "help": v["help"], "nodes": len(v["nodes"]),
                       "targets": [n["target"] for n in v["nodes"]][:5]} for v in res["violations"]]
    return FINDINGS[name]


def shot(page, name):
    for w, h in [(375, 812), (1280, 900)]:
        page.set_viewport_size({"width": w, "height": h})
        page.screenshot(path=str(OUT / f"{name}-{w}.png"), full_page=True)
        # Reflow: no horizontal scrolling of the page at 375 px (WCAG 1.4.10 uses 320; checked separately below).
        if w == 375:
            sw = page.evaluate("document.documentElement.scrollWidth")
            assert sw <= 376, f"{name}: page scrolls horizontally at 375px ({sw}px)"
    page.set_viewport_size({"width": 1280, "height": 900})


def sign_in(page, user):
    page.goto(f"{URL}/#/signin")
    page.locator(f"[data-user='{user}']").click()
    page.wait_for_function("location.hash !== '#/signin' && location.hash !== '#/'")
    page.wait_for_selector("main h1")


def test_full_journey(browser):
    # bypass_csp only lets the test inject axe-core; the app keeps its strict CSP.
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="fr-FR", bypass_csp=True)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    # Sign-in screen
    page.goto(f"{URL}/#/signin")
    page.wait_for_selector("[data-user]")
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.className") == "skip-link"
    assert scan(page, "signin") == []
    shot(page, "01-signin")

    # Analyst: collect, review, correct, publish
    sign_in(page, "usr_fatou")
    page.goto(f"{URL}/#/sources"); page.wait_for_selector("[data-run][data-snap='initial']")
    page.locator("[data-run='sn-official-procurement-candidate']").click()
    page.wait_for_selector("#run-msg [role=alert]")
    assert "approved" in page.locator("#run-msg").inner_text().lower() or "approuv" in page.locator("#run-msg").inner_text().lower()
    page.locator("[data-run='sn-synthetic-procurement'][data-snap='initial']").click()
    page.wait_for_selector(".notice-success")
    assert scan(page, "sources") == []
    shot(page, "02-sources")
    page.goto(f"{URL}/#/review"); page.wait_for_selector("tbody a")
    assert scan(page, "review-queue") == []
    page.locator("tbody a").first.click(); page.wait_for_selector("#approve")
    page.locator("[data-correct='title']").click()
    page.fill("#v-title", "Pompage solaire pour 12 forages ruraux (Kaffrine, Kaolack)")
    page.locator("[data-form='title'] button[type=submit]").click()
    assert page.locator("[data-form='title'] [data-err]").inner_text().strip() != ""  # reason required
    page.fill("#r-title", "Titre plus court pour les résultats de recherche")
    page.locator("[data-form='title'] button[type=submit]").click()
    page.wait_for_selector(".notice-success")
    assert scan(page, "review-task") == []
    shot(page, "03-review-task")
    page.locator("#approve").click(); page.wait_for_function("location.hash === '#/review'")

    # Compete customer: find, open source, save, start bid (J1, J2, J3)
    sign_in(page, "usr_aminata")
    page.wait_for_selector(".opp-card")
    assert scan(page, "tenders") == []
    shot(page, "04-tenders")
    page.locator(".opp-card h2 a").first.click(); page.wait_for_selector("#start-bid")
    assert "Pompage solaire pour 12 forages" in page.locator("h1").inner_text()
    href = page.locator("a", has_text=re.compile("source d'origine|original source")).first.get_attribute("href")
    src = ctx.new_page(); src.goto(f"{URL}{href}")
    assert "Données de test synthétiques" in src.content(); src.close()
    assert scan(page, "tender-detail-compete") == []
    shot(page, "05-tender-detail-compete")
    page.locator("#save").click(); page.wait_for_selector("#save[aria-pressed='true']")
    page.locator("#start-bid").click(); page.wait_for_selector("dialog[open]")
    assert scan(page, "start-bid-dialog") == []
    page.keyboard.press("Escape")
    assert page.evaluate("document.activeElement.id") == "start-bid"  # focus returns to trigger
    page.locator("#start-bid").click(); page.locator("#d-ok").click()
    page.wait_for_function("location.hash.startsWith('#/bids/')"); page.wait_for_selector(".notice-success")
    assert scan(page, "bid-started") == []
    shot(page, "06-bid-started")

    # Issuer amends the deadline (J5)
    sign_in(page, "usr_fatou")
    page.goto(f"{URL}/#/sources"); page.wait_for_selector("[data-snap='amendment-1']")
    page.locator("[data-snap='amendment-1']").click(); page.wait_for_selector(".notice-success")

    sign_in(page, "usr_aminata")
    page.goto(f"{URL}/#/alerts"); page.wait_for_selector(".card h2")
    assert "Additif n°1" in page.locator("main").inner_text()
    assert scan(page, "alerts") == []
    shot(page, "07-alerts")
    page.locator("main a.btn").first.click(); page.wait_for_selector(".amend-note")
    body = page.locator("main").inner_text()
    assert "12 janvier 2027" in body and "15 décembre 2026" in body
    shot(page, "08-tender-amended")

    # Analyst traces the deadline back to the amendment (J7)
    sign_in(page, "usr_fatou")
    page.goto(f"{URL}/#/trace"); page.locator("main .card a").first.click(); page.wait_for_selector(".chain")
    chain = page.locator(".chain").inner_text()
    assert "Additif n°1" in chain and "12" in chain
    assert scan(page, "trace") == []
    shot(page, "09-trace")

    # Discover customer: gated, restricted fields absent from the page (J4)
    sign_in(page, "usr_moussa")
    page.wait_for_selector(".opp-card"); page.locator(".opp-card h2 a").first.click(); page.wait_for_selector(".gate")
    html = page.content()
    assert "DEMO-014" not in html and "450" not in page.locator("main").inner_text()
    assert page.locator("#start-bid").count() == 0
    assert scan(page, "tender-detail-discover") == []
    shot(page, "10-tender-detail-discover")

    # English and 320 px reflow on the detail page
    page.locator("#lang-en").click(); page.wait_for_selector("text=Submission deadline")
    page.set_viewport_size({"width": 320, "height": 700})
    assert page.evaluate("document.documentElement.scrollWidth") <= 321
    page.screenshot(path=str(OUT / "11-discover-en-320.png"), full_page=True)
    assert scan(page, "tender-detail-discover-en") == []

    # Auditor view
    sign_in(page, "usr_cheikh")
    page.wait_for_selector("table")
    assert "pursuit.created" in page.locator("main").inner_text()
    assert scan(page, "audit") == []

    assert errors == [], errors
