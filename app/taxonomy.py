"""VA sector taxonomy import (LLD v1.4 §5.4).

Import into an inactive version, validate counts, uniqueness and parent integrity,
record the checksum and rights state, then activate in one transaction.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

EXPECTED = {"sector": 13, "cluster": 39, "industry": 78, "activity": 156}


class TaxonomyError(Exception):
    pass


def load_nodes(path: Path) -> tuple[list[dict], str]:
    raw = path.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    nodes: dict[str, dict] = {}

    def add(code, level, parent, label, fit=None):
        code = str(code).strip()
        existing = nodes.get(code)
        if existing:
            if existing["level"] != level or existing["parent_code"] != parent or existing["label"] != label:
                raise TaxonomyError(f"code {code} has conflicting definitions")
            return
        nodes[code] = {"code": code, "level": level, "parent_code": parent, "label": label,
                       "market_fit": fit, "sort_order": len(nodes)}

    for r in rows:
        add(r["sector_code"], "sector", None, r["sector_name"])
        add(r["cluster_code"], "cluster", r["sector_code"], r["cluster_name"])
        add(r["industry_code"], "industry", r["cluster_code"], r["industry_name"])
        add(r["activity_code"], "activity", r["industry_code"], r["activity_name"], r.get("market_fit"))
    return list(nodes.values()), checksum


def validate(nodes: list[dict]) -> dict:
    counts = {lvl: sum(1 for n in nodes if n["level"] == lvl) for lvl in EXPECTED}
    if counts != EXPECTED:
        raise TaxonomyError(f"unexpected counts {counts}, expected {EXPECTED}")
    codes = {n["code"] for n in nodes}
    orphans = [n["code"] for n in nodes if n["parent_code"] and n["parent_code"] not in codes]
    if orphans:
        raise TaxonomyError(f"orphan nodes: {orphans[:5]}")
    return counts


def import_and_activate(conn, path: Path, key: str = "va", version: str = "1.0") -> dict:
    nodes, checksum = load_nodes(path)
    counts = validate(nodes)
    tax_id = f"tax_{key}_{version}"
    existing = conn.execute("SELECT checksum, activated_at FROM sector_taxonomies WHERE id=%s", (tax_id,)).fetchone()
    if existing:
        if existing["checksum"] != checksum:
            raise TaxonomyError("same version with a different checksum; issue a new version")
        return {"taxonomy_id": tax_id, "checksum": checksum, "counts": counts, "already_active": bool(existing["activated_at"])}
    with conn.transaction():
        conn.execute(
            "INSERT INTO sector_taxonomies(id,key,version,source_file,checksum,rights_status) VALUES (%s,%s,%s,%s,%s,'verafrika_owned')",
            (tax_id, key, version, path.name, checksum),
        )
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO sector_nodes(taxonomy_id,code,level,parent_code,label,sort_order,market_fit) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                [(tax_id, n["code"], n["level"], n["parent_code"], n["label"], n["sort_order"], n["market_fit"]) for n in nodes],
            )
        conn.execute("UPDATE sector_taxonomies SET retired_at=now() WHERE key=%s AND activated_at IS NOT NULL AND retired_at IS NULL", (key,))
        conn.execute("UPDATE sector_taxonomies SET activated_at=now() WHERE id=%s", (tax_id,))
    return {"taxonomy_id": tax_id, "checksum": checksum, "counts": counts, "already_active": False}


def label_path(conn, code: str | None) -> list[dict]:
    """Breadcrumb from the active taxonomy, e.g. Sector > Cluster > Industry."""
    out = []
    while code:
        n = conn.execute(
            "SELECT n.code, n.label, n.level, n.parent_code FROM sector_nodes n JOIN sector_taxonomies t ON t.id=n.taxonomy_id "
            "WHERE t.activated_at IS NOT NULL AND t.retired_at IS NULL AND n.code=%s", (code,)
        ).fetchone()
        if not n:
            break
        out.insert(0, {"code": n["code"], "label": n["label"], "level": n["level"]})
        code = n["parent_code"]
    return out
