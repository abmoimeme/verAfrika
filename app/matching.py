"""Explainable company-to-opportunity matching (HLA v1.4 §7.2, §7.4).

Deterministic eligibility gate, then weighted relevance. Every match stores its rule
version, strengths, gaps and limitations so a dispute can be reconstructed.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .db import Jsonb, new_id

RULE_VERSION = "match-rules-0.2"
UEMOA = {"SN", "BJ", "BF", "CI", "GW", "ML", "NE", "TG"}

# Explanations are codes with parameters so every client can render them in the user's language.
def _m(code: str, **params) -> dict:
    return {"code": code, "params": params}


STANDARD_LIMITATIONS = [_m("decision_support_only"), _m("experience_not_verified")]


def evaluate(company: dict, profile: dict, registration: dict | None, fields: dict, now: datetime) -> dict:
    strengths, gaps, limitations = [], [], list(STANDARD_LIMITATIONS)
    eligible, score = True, 0

    deadline = datetime.fromisoformat(fields["deadline"]) if fields.get("deadline") else None
    if deadline and deadline <= now:
        eligible = False
        gaps.append(_m("deadline_passed"))

    countries = set(fields.get("eligible_countries") or [])
    if company["country_code"] in countries:
        score += 15
        strengths.append(_m("country_eligible", country=company["country_code"]))
    else:
        eligible = False
        gaps.append(_m("country_not_eligible", country=company["country_code"]))

    if registration and registration["status"] == "active":
        score += 15
        strengths.append(_m("registration_active", authority=registration["authority"]))
        if registration["observed_at"] < now - timedelta(days=90):
            limitations.append(_m("registration_stale", days=90))
    else:
        gaps.append(_m("registration_missing"))

    code = fields.get("industry_code")
    sectors = profile.get("sector_codes") or []
    exact = bool(code and code in sectors)
    if exact:
        score += 40
        strengths.append(_m("industry_exact"))
    elif code and any(s.rsplit(".", 1)[0] == code.rsplit(".", 1)[0] for s in sectors):
        score += 20
        strengths.append(_m("industry_related"))
        gaps.append(_m("industry_not_identical"))
    else:
        gaps.append(_m("industry_mismatch"))

    needed = set(fields.get("capability_tags") or [])
    have = set(profile.get("capabilities") or [])
    if needed:
        covered = needed & have
        score += round(30 * len(covered) / len(needed))
        if covered:
            strengths.append(_m("capabilities_covered", capabilities=sorted(covered)))
        missing = needed - have
        if missing:
            gaps.append(_m("capabilities_missing", capabilities=sorted(missing)))
        limitations.append(_m("capabilities_self_declared"))

    if company.get("is_sample"):
        limitations.append(_m("sample_company"))

    if not registration:
        confidence = "low"
    elif exact and registration["observed_at"] >= now - timedelta(days=90):
        confidence = "high"
    else:
        confidence = "medium"
    return {"eligible": eligible, "score": min(score, 100) if eligible else min(score, 40),
            "confidence": confidence, "strengths": strengths, "gaps": gaps, "limitations": limitations}


def compute_for_version(conn, opp_id: str, version_no: int, fields: dict) -> int:
    now = datetime.now(timezone.utc)
    companies = conn.execute(
        "SELECT c.*, p.sector_codes, p.capabilities FROM companies c JOIN company_profiles p ON p.company_id=c.id "
        "WHERE c.id IN (SELECT company_id FROM organizations WHERE kind='customer' AND company_id IS NOT NULL)"
    ).fetchall()
    n = 0
    for c in companies:
        reg = conn.execute("SELECT * FROM registrations WHERE company_id=%s ORDER BY observed_at DESC LIMIT 1", (c["id"],)).fetchone()
        r = evaluate(c, c, reg, fields, now)
        conn.execute(
            "INSERT INTO matches(id,opportunity_id,version_no,company_id,eligible,score,confidence,strengths,gaps,limitations,rule_version) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (opportunity_id,version_no,company_id) DO UPDATE SET "
            "eligible=EXCLUDED.eligible, score=EXCLUDED.score, confidence=EXCLUDED.confidence, strengths=EXCLUDED.strengths, "
            "gaps=EXCLUDED.gaps, limitations=EXCLUDED.limitations, rule_version=EXCLUDED.rule_version, created_at=now()",
            (new_id("mch"), opp_id, version_no, c["id"], r["eligible"], r["score"], r["confidence"],
             Jsonb(r["strengths"]), Jsonb(r["gaps"]), Jsonb(r["limitations"]), RULE_VERSION))
        n += 1
    return n
