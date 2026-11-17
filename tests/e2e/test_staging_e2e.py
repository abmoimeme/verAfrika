"""Staging sign-in journey in a real browser: invitation → account → staff MFA → publish → customer bid.

  VERAFRIKA_STAGING_URL=http://localhost:8078 STAGING_DATABASE_URL=postgresql://… AXE_PATH=…/axe.min.js pytest tests/e2e/test_staging_e2e.py
Creates fresh accounts with unique emails; does not reset the database.
"""
import os
import re
import secrets
from pathlib import Path

import pytest

URL = os.environ.get("VERAFRIKA_STAGING_URL")
DB = os.environ.get("STAGING_DATABASE_URL")
AXE = os.environ.get("AXE_PATH")
OUT = Path(__file__).resolve().parents[2] / "reports" / "ux" / "staging"
pytestmark = pytest.mark.skipif(not (URL and DB and AXE), reason="set VERAFRIKA_STAGING_URL, STAGING_DATABASE_URL and AXE_PATH")
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
PASSWORD = "phrase de passe pour le pilote"


def scan(page):
    page.add_script_tag(path=AXE)
    v = page.evaluate("async (t) => (await axe.run(document, {runOnly: {type: 'tag', values: t}})).violations.map(v => [v.id, v.impact, v.nodes.length])", TAGS)
    return v


def test_staging_journey():
    os.environ["VERAFRIKA_DATABASE_URL"] = DB
    from playwright.sync_api import sync_playwright

    from app import accounts
    from app.db import connect
    run = secrets.token_hex(3)
    with connect() as c:
        org = c.execute("SELECT id FROM organizations WHERE kind='customer' ORDER BY id LIMIT 1").fetchone()["id"]
        staff_tok = accounts.create_invite(c, f"analyst+{run}@verafrika.example", "org_va_ops", "analyst", "e2e")
        cust_tok = accounts.create_invite(c, f"owner+{run}@pilote.example", org, "owner", "e2e")
    OUT.mkdir(parents=True, exist_ok=True)
    found = {}

    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        # bypass_csp only lets the test inject axe-core; the app keeps its strict CSP.
        page = b.new_page(viewport={"width": 390, "height": 844}, locale="fr-FR", bypass_csp=True)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # Unauthenticated visit lands on the sign-in form, not the dev picker
        page.goto(f"{URL}/")
        page.wait_for_selector("#login")
        assert page.locator("[data-user]").count() == 0
        found["signin"] = scan(page)
        page.screenshot(path=str(OUT / "01-signin-390.png"), full_page=True)
        page.fill("#li-email", "nobody@example.com"); page.fill("#li-pw", "wrong password 123")
        page.locator("#login button[type=submit]").click()
        page.wait_for_function("document.querySelector('[data-err]').textContent.length > 0")
        assert "incorrect" in page.locator("[data-err]").inner_text().lower()

        # Staff invitation → account → authenticator setup → analyst tools
        page.goto(f"{URL}/#/invite/{staff_tok}"); page.wait_for_selector("#inv")
        found["invite"] = scan(page)
        page.screenshot(path=str(OUT / "02-invite-390.png"), full_page=True)
        page.fill("#iv-name", "Analyste Test"); page.fill("#iv-pw", "court")
        page.locator("#inv button[type=submit]").click()
        page.wait_for_function("document.querySelector('[data-err]').textContent.length > 0")
        assert page.evaluate("document.activeElement.id") == "iv-pw"  # focus moves to the field in error
        page.fill("#iv-pw", PASSWORD); page.locator("#inv button[type=submit]").click()
        page.wait_for_selector("#mfa-key")
        found["mfa-setup"] = scan(page)
        page.screenshot(path=str(OUT / "03-mfa-setup-390.png"), full_page=True)
        secret = page.locator("#mfa-key").inner_text().replace(" ", "")
        page.fill("#mfa-code", "000000"); page.locator("#mfa button[type=submit]").click()
        page.wait_for_function("document.querySelector('[data-err]').textContent.length > 0")
        page.fill("#mfa-code", accounts.totp_now(secret)); page.locator("#mfa button[type=submit]").click()
        page.wait_for_function("location.hash === '#/review'")

        page.goto(f"{URL}/#/sources"); page.wait_for_selector("[data-snap='initial']")
        page.locator("[data-run='sn-synthetic-procurement'][data-snap='initial']").click(); page.wait_for_selector(".notice-success")
        page.goto(f"{URL}/#/review")
        page.wait_for_selector("main h1")
        if page.locator("tbody a").count():
            page.locator("tbody a").first.click(); page.wait_for_selector("#approve")
            page.locator("#approve").click(); page.wait_for_function("location.hash === '#/review'")

        # Sign out ends the session
        page.locator("#switch").click(); page.wait_for_selector("#login")
        page.goto(f"{URL}/#/review"); page.wait_for_selector("#login")

        # Pilot customer: invitation → tenders → bid
        page.goto(f"{URL}/#/invite/{cust_tok}"); page.wait_for_selector("#inv")
        page.fill("#iv-name", "Responsable Pilote"); page.fill("#iv-pw", PASSWORD)
        page.locator("#inv button[type=submit]").click()
        page.wait_for_function("location.hash.startsWith('#/opportunities')"); page.wait_for_selector(".opp-card")
        page.locator(".opp-card h2 a").first.click(); page.wait_for_selector("h1")
        if page.locator("#start-bid").count():
            page.locator("#start-bid").click(); page.locator("#d-ok").click()
            page.wait_for_function("location.hash.startsWith('#/bids/')")
        found["bid"] = scan(page)
        page.screenshot(path=str(OUT / "04-customer-bid-390.png"), full_page=True)

        # Sign back in with the password (no MFA for customers)
        page.locator("#switch").click(); page.wait_for_selector("#login")
        page.fill("#li-email", f"OWNER+{run}@pilote.example"); page.fill("#li-pw", PASSWORD)
        page.locator("#login button[type=submit]").click()
        page.wait_for_function("location.hash.startsWith('#/opportunities')")
        assert re.search(r"Responsable Pilote", page.locator("#who").inner_text())
        b.close()

    assert errors == [], errors
    assert all(v == [] for v in found.values()), found
