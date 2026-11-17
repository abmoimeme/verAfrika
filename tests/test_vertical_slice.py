"""First vertical slice acceptance tests (HLA v1.4 §12.1, LLD v1.4 §11, UX standards J1–J10)."""
from app.db import connect

PURSUIT_KEY = "pursuit-key-0000000001"


def _pursue(client, opp_id, headers, key=PURSUIT_KEY, body=None):
    return client.post(f"/v1/opportunities/{opp_id}/pursuits", json=body or {}, headers={**headers, "Idempotency-Key": key})


# --- Ingestion, rights and review -------------------------------------------------
def test_unapproved_source_cannot_be_collected(client, login):
    analyst = login("usr_fatou")
    r = client.post("/v1/admin/sources/sn-official-procurement-candidate/runs", json={}, headers=analyst)
    assert r.status_code == 403
    assert r.json()["error"]["reason"] == "source_rights_not_approved"


def test_unreviewed_notice_is_invisible_to_customers(client, login):
    analyst = login("usr_fatou")
    client.post("/v1/admin/sources/sn-synthetic-procurement/runs", json={"snapshot": "initial"}, headers=analyst)
    aminata = login("usr_aminata")
    assert client.get("/v1/opportunities?country=SN", headers=aminata).json()["results"] == []


def test_duplicate_run_creates_one_version(client, login):
    analyst = login("usr_fatou")
    a = client.post("/v1/admin/sources/sn-synthetic-procurement/runs", json={"snapshot": "initial"}, headers=analyst).json()
    b = client.post("/v1/admin/sources/sn-synthetic-procurement/runs", json={"snapshot": "initial"}, headers=analyst).json()
    assert (a["records_new"], b["records_new"], b["records_unchanged"]) == (1, 0, 1)
    with connect() as c:
        assert c.execute("SELECT count(*) n FROM opportunity_versions").fetchone()["n"] == 1
        assert c.execute("SELECT count(*) n FROM source_records").fetchone()["n"] == 1


def test_contact_fields_are_dropped_by_rights_policy(client, published, login):
    opp_id, _ = published
    body = client.get(f"/v1/opportunities/{opp_id}", headers=login("usr_awa")).text
    assert "contact_telephone" not in body and "+221 00 000" not in body


def test_analyst_correction_keeps_raw_record(client, login):
    analyst = login("usr_fatou")
    client.post("/v1/admin/sources/sn-synthetic-procurement/runs", json={"snapshot": "initial"}, headers=analyst)
    task = client.get("/v1/admin/review-tasks", headers=analyst).json()["tasks"][0]
    r = client.post(f"/v1/admin/review-tasks/{task['id']}/corrections",
                    json={"field": "title", "value": "Pompage solaire — 12 forages ruraux (Kaffrine, Kaolack)",
                          "reason": "Shorter title for search results"}, headers=analyst)
    assert r.status_code == 200, r.text
    detail = client.get(f"/v1/admin/review-tasks/{task['id']}", headers=analyst).json()
    assert detail["fields"]["title"].startswith("Pompage solaire —")
    assert detail["source_record"]["raw_json"]["objet"].startswith("Fourniture et installation")
    titles = [a for a in detail["assertions"] if a["field_path"] == "title"]
    assert {a["origin"] for a in titles} == {"source", "analyst"}
    with connect() as c:  # raw records are immutable at the database level
        try:
            c.execute("UPDATE source_records SET raw_json='{}'::jsonb")
            raise AssertionError("raw record was modified")
        except Exception as e:  # noqa: BLE001
            assert "append-only" in str(e)


def test_correction_requires_reason_and_valid_deadline(client, login):
    analyst = login("usr_fatou")
    client.post("/v1/admin/sources/sn-synthetic-procurement/runs", json={"snapshot": "initial"}, headers=analyst)
    tid = client.get("/v1/admin/review-tasks", headers=analyst).json()["tasks"][0]["id"]
    assert client.post(f"/v1/admin/review-tasks/{tid}/corrections", json={"field": "title", "value": "x", "reason": ""}, headers=analyst).status_code == 400
    r = client.post(f"/v1/admin/review-tasks/{tid}/corrections", json={"field": "deadline", "value": "15/12/2026", "reason": "typo fix"}, headers=analyst)
    assert r.status_code == 400 and r.json()["error"]["field"] == "value"


# --- Customer journey ------------------------------------------------------------
def test_j1_j2_compete_user_finds_notice_and_source(client, published, login):
    opp_id, _ = published
    aminata = login("usr_aminata")
    res = client.get("/v1/opportunities?country=SN&q=pompage", headers=aminata).json()
    assert [o["id"] for o in res["results"]] == [opp_id]
    o = client.get(f"/v1/opportunities/{opp_id}", headers=aminata).json()
    assert o["deadline"] == "2026-12-15T10:00:00+00:00"
    assert o["issuer"] and o["source"]["observed_at"] and o["sample_data"] is True
    assert o["source"]["url"].startswith("/fixtures/sources/sn-synthetic/notices/SN-DEMO-2026-0147")
    page = client.get(o["source"]["url"])
    assert page.status_code == 200 and "Données de test synthétiques" in page.text
    assert o["match"]["eligible"] is True and o["match"]["strengths"] and o["match"]["limitations"]


def test_discover_response_omits_restricted_fields(client, published, login):
    opp_id, _ = published
    moussa = login("usr_moussa")
    o = client.get(f"/v1/opportunities/{opp_id}", headers=moussa).json()
    for k in ("reference", "lots", "estimated_value", "qualification_requirements", "match", "amendment_history"):
        assert k not in o, k
    assert "url" not in o["source"] and "checksum" not in o["source"]
    assert o["access"]["details"] is False and o["access"]["pursuit"] is False


def test_j4_discover_cannot_start_bid(client, published, login):
    opp_id, _ = published
    r = _pursue(client, opp_id, login("usr_moussa"))
    assert r.status_code == 403
    assert r.json()["error"]["required_plan"] == "compete"
    with connect() as c:
        assert c.execute("SELECT count(*) n FROM pursuits").fetchone()["n"] == 0
        assert c.execute("SELECT count(*) n FROM audit_events WHERE action='access.denied' AND details_json->>'permission'='bid.workspace'").fetchone()["n"] == 1


def test_viewer_role_cannot_start_bid_even_on_compete(client, published, login):
    opp_id, _ = published
    r = _pursue(client, opp_id, login("usr_khady"))
    assert r.status_code == 403 and r.json()["error"]["reason"] == "role_not_permitted"


def test_j3_pursuit_is_idempotent(client, published, login):
    opp_id, _ = published
    aminata = login("usr_aminata")
    a = _pursue(client, opp_id, aminata)
    b = _pursue(client, opp_id, aminata)
    assert a.status_code == b.status_code == 201
    assert a.json() == b.json()
    assert b.headers["Idempotent-Replayed"] == "true"
    with connect() as c:
        assert c.execute("SELECT count(*) n FROM pursuits").fetchone()["n"] == 1
        assert c.execute("SELECT used_count FROM entitlement_usage WHERE organization_id='org_sahel'").fetchone()["used_count"] == 1
        assert c.execute("SELECT count(*) n FROM audit_events WHERE action='pursuit.created'").fetchone()["n"] == 1


def test_idempotency_key_rules(client, published, login):
    opp_id, _ = published
    aminata = login("usr_aminata")
    r = client.post(f"/v1/opportunities/{opp_id}/pursuits", json={}, headers=aminata)
    assert r.status_code == 400 and r.json()["error"]["field"] == "Idempotency-Key"
    assert _pursue(client, opp_id, aminata, body={"note": "a"}).status_code == 201
    r = _pursue(client, opp_id, aminata, body={"note": "b"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "idempotency_conflict"
    r = _pursue(client, opp_id, aminata, key="another-key-00000000001")
    assert r.status_code == 409 and r.json()["error"]["code"] == "pursuit_exists"


def test_j8_cross_tenant_pursuit_is_not_visible(client, published, login):
    opp_id, _ = published
    pid = _pursue(client, opp_id, login("usr_aminata")).json()["id"]
    r = client.get(f"/v1/pursuits/{pid}", headers=login("usr_awa"))
    assert r.status_code == 404 and r.json()["error"]["code"] == "resource_not_visible"
    with connect() as c:
        assert c.execute("SELECT count(*) n FROM audit_events WHERE action='access.denied' AND object_id=%s", (pid,)).fetchone()["n"] == 1


def test_customers_cannot_reach_analyst_routes(client, login):
    r = client.get("/v1/admin/review-tasks", headers=login("usr_awa"))
    assert r.status_code == 404


# --- Amendments ------------------------------------------------------------------
def test_j5_j7_deadline_amendment_reaches_customer_and_is_traceable(client, published, login):
    opp_id, analyst = published
    aminata = login("usr_aminata")
    assert client.put(f"/v1/opportunities/{opp_id}/saved", headers=aminata).status_code == 200

    run = client.post("/v1/admin/sources/sn-synthetic-procurement/runs", json={"snapshot": "amendment-1"}, headers=analyst).json()
    assert run["records_amended"] == 1

    o = client.get(f"/v1/opportunities/{opp_id}", headers=aminata).json()
    assert o["deadline"] == "2027-01-12T10:00:00+00:00"
    assert o["version"] == 2 and o["amended"] is True
    assert o["verification"] == "issuer_amendment_pending_confirmation"
    assert o["last_amendment"]["issuer_reference"] == "Additif n°1"
    assert o["amendment_history"][0]["changes"] == [
        {"field": "deadline", "old": "2026-12-15T10:00:00+00:00", "new": "2027-01-12T10:00:00+00:00"}]

    al = client.get("/v1/alerts", headers=aminata).json()["alerts"]
    assert any(a["kind"] == "deadline_changed" and a["issuer_reference"] == "Additif n°1" for a in al)
    # An organization that never saved or pursued it gets no alert.
    assert not client.get("/v1/alerts", headers=login("usr_awa")).json()["alerts"]

    t = client.get(f"/v1/admin/opportunities/{opp_id}/trace?field=deadline", headers=analyst).json()
    v1, v2 = t["versions"]
    assert v1["assertions"][0]["value_json"] == "2026-12-15T10:00:00+00:00"
    assert v2["assertions"][0]["value_json"] == "2027-01-12T10:00:00+00:00"
    assert v2["source_record"]["id"] == t["amendments"][0]["source_record_id"]
    assert v2["source_record"]["ingestion_run_id"] == t["amendments"][0]["ingestion_run_id"]
    assert v1["source_record"]["checksum"] != v2["source_record"]["checksum"]

    # The analyst confirms it; the customer sees it as reviewed.
    task = [x for x in client.get("/v1/admin/review-tasks", headers=analyst).json()["tasks"] if x["kind"] == "amendment"][0]
    assert task["priority"] == "high"
    assert client.post(f"/v1/admin/review-tasks/{task['id']}/approve", json={}, headers=analyst).status_code == 200
    o = client.get(f"/v1/opportunities/{opp_id}", headers=aminata).json()
    assert o["verification"] == "analyst_reviewed" and o["deadline"] == "2027-01-12T10:00:00+00:00"
    # No duplicate alert on confirmation.
    assert sum(a["kind"] == "deadline_changed" for a in client.get("/v1/alerts", headers=aminata).json()["alerts"]) == 1


def test_analyst_correction_carries_forward_to_amended_version(client, login):
    analyst = login("usr_fatou")
    client.post("/v1/admin/sources/sn-synthetic-procurement/runs", json={"snapshot": "initial"}, headers=analyst)
    tid = client.get("/v1/admin/review-tasks", headers=analyst).json()["tasks"][0]["id"]
    client.post(f"/v1/admin/review-tasks/{tid}/corrections", json={"field": "title", "value": "Titre corrigé", "reason": "Analyst wording"}, headers=analyst)
    opp_id = client.post(f"/v1/admin/review-tasks/{tid}/approve", json={}, headers=analyst).json()["opportunity_id"]
    client.post("/v1/admin/sources/sn-synthetic-procurement/runs", json={"snapshot": "amendment-1"}, headers=analyst)
    o = client.get(f"/v1/opportunities/{opp_id}", headers=login("usr_aminata")).json()
    assert o["title"] == "Titre corrigé" and o["version"] == 2


# --- Coverage, audit and failure ----------------------------------------------------
def test_country_without_coverage_is_disclosed(client, published, login):
    r = client.get("/v1/opportunities?country=RW", headers=login("usr_aminata")).json()
    assert r["coverage"]["state"] == "not_researched" and r["complete"] is False


def test_suspended_membership_loses_access(client, published, login):
    h = login("usr_aminata")
    with connect() as c:
        c.execute("UPDATE memberships SET status='suspended' WHERE user_id='usr_aminata'")
    r = client.get("/v1/opportunities?country=SN", headers=h)
    assert r.status_code == 403 and r.json()["error"]["reason"] == "membership_inactive"


def test_audit_log_is_append_only_and_auditor_can_reconstruct(client, published, login):
    opp_id, _ = published
    _pursue(client, opp_id, login("usr_aminata"))
    ev = client.get(f"/v1/audit/events?object_id={opp_id}", headers=login("usr_cheikh")).json()["events"]
    actions = {e["action"] for e in ev}
    assert {"opportunity.ingested", "opportunity.review_approved", "pursuit.created"} <= actions
    with connect() as c:
        try:
            c.execute("DELETE FROM audit_events")
            raise AssertionError("audit row deleted")
        except Exception as e:  # noqa: BLE001
            assert "append-only" in str(e)


def test_failed_run_is_visible_and_retry_is_safe(client, login, monkeypatch):
    from app import ingestion
    analyst = login("usr_fatou")
    real = ingestion.normalize
    monkeypatch.setattr(ingestion, "normalize", lambda raw, allowed: (_ for _ in ()).throw(ValueError("schema drift")))
    r = client.post("/v1/admin/sources/sn-synthetic-procurement/runs", json={"snapshot": "initial"}, headers=analyst)
    assert r.status_code == 502
    runs = client.get("/v1/admin/ingestion-runs", headers=analyst).json()["runs"]
    assert runs[0]["status"] == "failed" and "schema drift" in runs[0]["error"]
    with connect() as c:
        assert c.execute("SELECT count(*) n FROM source_records").fetchone()["n"] == 0
    monkeypatch.setattr(ingestion, "normalize", real)
    r = client.post("/v1/admin/sources/sn-synthetic-procurement/runs", json={"snapshot": "initial"}, headers=analyst)
    assert r.status_code == 200 and r.json()["records_new"] == 1


def test_taxonomy_hierarchy_is_complete(client, login):
    with connect() as c:
        counts = {r["level"]: r["n"] for r in c.execute("SELECT level, count(*) n FROM sector_nodes GROUP BY level")}
    assert counts == {"sector": 13, "cluster": 39, "industry": 78, "activity": 156}
    r = client.get("/v1/reference/sector-taxonomy?parent_code=VA02", headers=login("usr_aminata")).json()
    assert [n["level"] for n in r["nodes"]] == ["cluster"] * 3


def test_shipped_taxonomy_matches_handoff_checksum():
    import hashlib
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    shipped = hashlib.sha256((root / "reference" / "VERAFRIKA_sector_taxonomy_v1.csv").read_bytes()).hexdigest()
    assert shipped == "80c76012010042a7fd267c6397bd5e556194438fc7b33b0c165a933539c31986"  # handoff/Inventory.csv
