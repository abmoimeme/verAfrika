"""Source ingestion (LLD v1.4 §7, HLA v1.4 §6.1).

connector → raw record preserved → fields normalized into assertions → version created →
amendment detected → review task / alert. A run either commits every record or none
(no partial publication); failed runs stay visible and are safe to retry because
records are de-duplicated by (source, external key, checksum).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import audit
from .db import Jsonb, connect, new_id
from .errors import ApiError

FIXTURES = Path(__file__).resolve().parent.parent / "connectors" / "fixtures"

# Fields compared to detect an amendment. issuer_amendment is metadata about the change itself.
TRACKED_FIELDS = ["title", "reference", "issuer", "procedure", "published_on", "deadline", "place",
                  "lots", "qualification_requirements", "eligible_countries", "industry_code",
                  "capability_tags", "estimated_value", "language"]

# Versioned mapping from source-native activity labels to VA industry codes (LLD §5.4 "Source mapping").
ACTIVITY_MAPPING_VERSION = "sn-synthetic-activity-map-0.1"
ACTIVITY_MAPPING = {
    "hydraulique rurale / énergie solaire": "VA02.03.01",   # Water & Sanitation
    "énergie solaire": "VA02.01.01",                        # Renewable Power
}
CAPABILITY_KEYWORDS = {
    "pompage solaire": "solar_pumping",
    "forage": "borehole_works",
    "hydraulique": "water_supply",
}


@dataclass
class RawNotice:
    external_key: str
    source_url: str
    raw: dict
    retrieved_at: datetime


class FixtureConnector:
    """Reads a synthetic feed snapshot. A real connector implements the same fetch() contract."""

    def __init__(self, folder: str, base_url: str):
        self.folder = FIXTURES / folder
        self.base_url = base_url

    def fetch(self, snapshot: str) -> list[RawNotice]:
        feed = json.loads((self.folder / "feed.json").read_text())
        if snapshot not in feed:
            raise ApiError(400, "invalid_request", f"Unknown snapshot '{snapshot}'.", available=sorted(feed))
        now = datetime.now(timezone.utc)
        out = []
        for name in feed[snapshot]:
            raw = json.loads((self.folder / name).read_text())
            rev = name.split(".rev")[1].split(".")[0] if ".rev" in name else "1"
            out.append(RawNotice(raw.get("avis_id"), f"{self.base_url}/{raw.get('avis_id')}?rev={rev}", raw, now))
        return out


CONNECTORS = {
    "fixture:sn_synthetic": lambda: FixtureConnector("sn_synthetic", "/fixtures/sources/sn-synthetic/notices"),
}


def checksum(raw: dict) -> str:
    return hashlib.sha256(json.dumps(raw, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _date(s: str) -> str:
    return datetime.strptime(s.strip(), "%d/%m/%Y").date().isoformat()


def _datetime_gmt(s: str) -> str:
    # Senegal uses GMT year-round. Stored as ISO 8601 UTC.
    return datetime.strptime(s.strip(), "%d/%m/%Y %H:%M").replace(tzinfo=timezone.utc).isoformat()


def normalize(raw: dict, allowed_fields: list[str]) -> dict:
    """Map source-native fields to canonical ones. Raises ValueError on malformed input."""
    if not raw.get("avis_id") or not raw.get("objet"):
        raise ValueError("notice is missing avis_id or objet")
    activity = (raw.get("activite_source") or "").strip().lower()
    text = " ".join([raw.get("objet", ""), *raw.get("criteres_qualification", [])]).lower()
    fields = {
        "title": raw["objet"].strip(),
        "reference": raw.get("reference"),
        "issuer": raw.get("autorite_contractante"),
        "procedure": raw.get("type_procedure"),
        "published_on": _date(raw["date_publication"]),
        "deadline": _datetime_gmt(raw["date_limite_depot"]),
        "place": raw.get("lieu_execution"),
        "lots": [{"number": l["numero"], "title": l["intitule"],
                  "bid_security": {"amount": l.get("garantie_soumission_xof"), "currency": "XOF"}}
                 for l in raw.get("lots", [])],
        "qualification_requirements": raw.get("criteres_qualification", []),
        "eligible_countries": raw.get("pays_eligibles", []),
        "industry_code": ACTIVITY_MAPPING.get(activity),
        "capability_tags": sorted({tag for kw, tag in CAPABILITY_KEYWORDS.items() if kw in text}),
        "estimated_value": {"amount": raw.get("montant_estime_xof"), "currency": "XOF"} if raw.get("montant_estime_xof") else None,
        "language": raw.get("langue", "fr"),
        "issuer_amendment": raw.get("additif"),
    }
    # Rights policy: only fields the source permits are kept (contacts are never in allowed_fields).
    return {k: v for k, v in fields.items() if k in allowed_fields}


def _current_values(conn, version_id: str, origin: str | None = None) -> dict:
    q = "SELECT field_path, value_json, origin, id, reason FROM opportunity_assertions WHERE version_id=%s AND superseded_by_id IS NULL"
    rows = conn.execute(q, (version_id,)).fetchall()
    if origin:
        rows = [r for r in rows if r["origin"] == origin]
    return {r["field_path"]: r for r in rows}


def _source_values(conn, version_id: str) -> dict:
    """Values as the source stated them, ignoring analyst corrections."""
    rows = conn.execute(
        "SELECT field_path, value_json FROM opportunity_assertions WHERE version_id=%s AND origin='source'", (version_id,)
    ).fetchall()
    return {r["field_path"]: r["value_json"] for r in rows}


def _insert_version(conn, opp_id, version_no, record_id, fields, review_state) -> str:
    vid = new_id("ver")
    conn.execute(
        "INSERT INTO opportunity_versions(id,opportunity_id,version_no,source_record_id,review_state,published_at) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (vid, opp_id, version_no, record_id, review_state,
         datetime.now(timezone.utc) if review_state == "published_pending_confirmation" else None),
    )
    for k, v in fields.items():
        conn.execute(
            "INSERT INTO opportunity_assertions(id,version_id,field_path,value_json,origin,source_record_id) VALUES (%s,%s,%s,%s,'source',%s)",
            (new_id("asr"), vid, k, Jsonb(v), record_id),
        )
    return vid


def _carry_forward_corrections(conn, prev_version_id, new_version_id, changed: set[str]):
    """Analyst corrections on fields the source did not change still apply to the new version."""
    for field, a in _current_values(conn, prev_version_id, origin="analyst").items():
        if field in changed:
            continue  # the issuer changed this field; the analyst must look at it again
        _supersede(conn, new_version_id, field, a["value_json"], a.get("reason"), carried_from=a["id"])


def _supersede(conn, version_id, field, value, reason, actor_id=None, carried_from=None) -> str:
    cur = conn.execute(
        "SELECT id, actor_id FROM opportunity_assertions WHERE version_id=%s AND field_path=%s AND superseded_by_id IS NULL",
        (version_id, field)).fetchone()
    nid = new_id("asr")
    if cur:
        # Release the one-current constraint, insert the new assertion, then link.
        conn.execute("UPDATE opportunity_assertions SET superseded_by_id=%s WHERE id=%s", (nid, cur["id"]))
    if carried_from:
        conn.execute(
            "INSERT INTO opportunity_assertions(id,version_id,field_path,value_json,origin,actor_id,reason,supersedes_id) "
            "SELECT %s,%s,%s,value_json,'analyst',actor_id,%s,%s FROM opportunity_assertions WHERE id=%s",
            (nid, version_id, field, f"Carried forward from previous version: {reason}", cur["id"] if cur else None, carried_from),
        )
    else:
        conn.execute(
            "INSERT INTO opportunity_assertions(id,version_id,field_path,value_json,origin,actor_id,reason,supersedes_id) "
            "VALUES (%s,%s,%s,%s,'analyst',%s,%s,%s)",
            (nid, version_id, field, Jsonb(value), actor_id, reason, cur["id"] if cur else None),
        )
    return nid


def _due(hours: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def _alert_interested_orgs(conn, opp_id, amendment_id, changed) -> int:
    orgs = conn.execute(
        "SELECT organization_id FROM saved_opportunities WHERE opportunity_id=%s "
        "UNION SELECT organization_id FROM pursuits WHERE opportunity_id=%s AND status='active'",
        (opp_id, opp_id)).fetchall()
    n = 0
    for o in orgs:
        conn.execute(
            "INSERT INTO alerts(id,organization_id,opportunity_id,kind,payload,amendment_id) VALUES (%s,%s,%s,'deadline_changed',%s,%s) "
            "ON CONFLICT DO NOTHING",
            (new_id("alr"), o["organization_id"], opp_id, Jsonb({"changes": changed}), amendment_id),
        )
        audit.record(conn, "alert.created", actor_id=None, organization_id=o["organization_id"],
                     object_type="opportunity", object_id=opp_id, kind="deadline_changed", amendment_id=amendment_id)
        n += 1
    return n


def run(source_key: str, snapshot: str, actor_id: str) -> dict:
    with connect() as conn:
        src = conn.execute("SELECT * FROM sources WHERE key=%s", (source_key,)).fetchone()
        if not src:
            raise ApiError(404, "resource_not_visible", "Not found.")
        if src["rights_status"] != "approved":
            audit.record(conn, "ingestion.blocked", actor_id=actor_id, organization_id=None, object_type="source",
                         object_id=src["id"], reason="source_rights_not_approved", rights_status=src["rights_status"])
            conn.commit()
            raise ApiError(403, "permission_denied", "This source has not been approved for collection.",
                           reason="source_rights_not_approved", rights_status=src["rights_status"])
        run_id = new_id("run")
        conn.execute(
            "INSERT INTO ingestion_runs(id,source_id,rights_policy_version,status,triggered_by) VALUES (%s,%s,%s,'running',%s)",
            (run_id, src["id"], src["rights_policy_version"], actor_id))
        conn.commit()  # the run is visible even if processing fails

        stats = {"records_seen": 0, "records_new": 0, "records_amended": 0, "records_unchanged": 0}
        try:
            connector = CONNECTORS[src["access_method"]]()
            notices = connector.fetch(snapshot)
            with conn.transaction():
                for n in notices:
                    stats["records_seen"] += 1
                    _process(conn, src, run_id, n, stats, actor_id)
                conn.execute(
                    "UPDATE ingestion_runs SET status='succeeded', finished_at=now(), records_seen=%s, records_new=%s, "
                    "records_amended=%s, records_unchanged=%s WHERE id=%s",
                    (stats["records_seen"], stats["records_new"], stats["records_amended"], stats["records_unchanged"], run_id))
                conn.execute(
                    "UPDATE country_source_coverage SET last_success_at=now(), next_run_at=now() + interval '4 hours' WHERE source_id=%s",
                    (src["id"],))
                audit.record(conn, "ingestion.run_succeeded", actor_id=actor_id, organization_id=None,
                             object_type="ingestion_run", object_id=run_id, snapshot=snapshot, **stats)
        except Exception as e:  # noqa: BLE001 — every failure must be visible on the run
            conn.rollback()
            conn.execute("UPDATE ingestion_runs SET status='failed', finished_at=now(), error=%s WHERE id=%s",
                         (f"{type(e).__name__}: {e}"[:500], run_id))
            audit.record(conn, "ingestion.run_failed", actor_id=actor_id, organization_id=None,
                         object_type="ingestion_run", object_id=run_id, error=str(e)[:200])
            conn.commit()
            if isinstance(e, ApiError):
                raise
            raise ApiError(502, "ingestion_failed", "The ingestion run failed and was rolled back. It is safe to retry.",
                           run_id=run_id) from e
        return {"run_id": run_id, "status": "succeeded", **stats}


def _process(conn, src, run_id, n: RawNotice, stats, actor_id):
    digest = checksum(n.raw)
    opp = conn.execute("SELECT * FROM opportunities WHERE source_id=%s AND external_key=%s",
                       (src["id"], n.external_key)).fetchone()
    dup = conn.execute("SELECT id FROM source_records WHERE source_id=%s AND external_key=%s AND checksum=%s",
                       (src["id"], n.external_key, digest)).fetchone()
    if dup:
        stats["records_unchanged"] += 1
        if opp:
            conn.execute("UPDATE opportunities SET last_seen_at=%s WHERE id=%s", (n.retrieved_at, opp["id"]))
        return

    fields = normalize(n.raw, src["allowed_fields"])
    record_id = new_id("srec")
    conn.execute(
        "INSERT INTO source_records(id,source_id,ingestion_run_id,external_key,source_url,retrieved_at,checksum,raw_json) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (record_id, src["id"], run_id, n.external_key, n.source_url, n.retrieved_at, digest, Jsonb(n.raw)))

    if not opp:
        opp_id = new_id("opp")
        conn.execute(
            "INSERT INTO opportunities(id,source_id,external_key,country_code,status,latest_version,last_seen_at) "
            "VALUES (%s,%s,%s,%s,'pending_review',1,%s)", (opp_id, src["id"], n.external_key, src["country_code"], n.retrieved_at))
        vid = _insert_version(conn, opp_id, 1, record_id, fields, "pending_review")
        conn.execute("INSERT INTO review_tasks(id,opportunity_id,version_id,kind,priority,due_at) VALUES (%s,%s,%s,'new_notice','normal',%s)",
                     (new_id("rvw"), opp_id, vid, _due(24)))
        audit.record(conn, "opportunity.ingested", actor_id=actor_id, organization_id=None, object_type="opportunity",
                     object_id=opp_id, source_record_id=record_id, run_id=run_id)
        stats["records_new"] += 1
        return

    prev = conn.execute("SELECT id, version_no FROM opportunity_versions WHERE opportunity_id=%s AND version_no=%s",
                        (opp["id"], opp["latest_version"])).fetchone()
    old_src = _source_values(conn, prev["id"])
    changed = [{"field": f, "old": old_src.get(f), "new": fields.get(f)}
               for f in TRACKED_FIELDS if old_src.get(f) != fields.get(f)]
    new_no = opp["latest_version"] + 1
    changed_names = {c["field"] for c in changed}
    deadline_only = changed_names == {"deadline"}
    auto_publish = deadline_only and src["auto_publish_deadline_amendments"] and opp["status"] == "published"
    state = "published_pending_confirmation" if auto_publish else "pending_review"
    vid = _insert_version(conn, opp["id"], new_no, record_id, fields, state)
    _carry_forward_corrections(conn, prev["id"], vid, changed_names)

    amend_id = new_id("amd")
    issuer_ref = (fields.get("issuer_amendment") or {}).get("numero") if isinstance(fields.get("issuer_amendment"), dict) else None
    conn.execute(
        "INSERT INTO amendments(id,opportunity_id,from_version,to_version,issuer_reference,changed_fields,source_record_id,ingestion_run_id) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (amend_id, opp["id"], prev["version_no"], new_no, issuer_ref, Jsonb(changed), record_id, run_id))
    conn.execute("UPDATE opportunities SET latest_version=%s, last_seen_at=%s" + (", published_version=%s" if auto_publish else "") + " WHERE id=%s",
                 (new_no, n.retrieved_at, *( [new_no] if auto_publish else [] ), opp["id"]))
    conn.execute("INSERT INTO review_tasks(id,opportunity_id,version_id,kind,priority,due_at) VALUES (%s,%s,%s,'amendment',%s,%s)",
                 (new_id("rvw"), opp["id"], vid, "high" if "deadline" in changed_names else "normal",
                  _due(4 if "deadline" in changed_names else 24)))
    audit.record(conn, "opportunity.amendment_detected", actor_id=actor_id, organization_id=None, object_type="opportunity",
                 object_id=opp["id"], amendment_id=amend_id, issuer_reference=issuer_ref, changed=sorted(changed_names),
                 auto_published=auto_publish, source_record_id=record_id, run_id=run_id)
    if auto_publish:
        _alert_interested_orgs(conn, opp["id"], amend_id, changed)
    stats["records_amended"] += 1
