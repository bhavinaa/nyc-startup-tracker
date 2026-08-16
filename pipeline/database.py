"""
SQLite-backed intermediate storage for the pipeline.

Why SQLite when we ultimately export JSON?
    - Joining three heterogeneous sources (YC / DOL / SEC) is *much* nicer in
      SQL than in Python dict-wrangling.
    - Gives us a queryable artifact for ad-hoc analysis later ("show me all
      NYC fintech YC companies that sponsored H-1B1 in the last 12 months").
    - The .db file is small enough (~5-10MB) that it can also be committed
      to the repo as a bonus artifact if you want.

If you later want browser-side SQL, swap `sql.js` into the frontend and
serve companies.db directly. For now, we export JSON for zero-friction reads.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id              TEXT PRIMARY KEY,     -- e.g. 'yc-ramp'
    name            TEXT NOT NULL,
    slug            TEXT,
    one_liner       TEXT,
    long_description TEXT,
    website         TEXT,
    yc_url          TEXT,
    yc_batch        TEXT,
    team_size       INTEGER,
    stage           TEXT,
    status          TEXT,
    industries      TEXT,                 -- JSON array
    tags            TEXT,                 -- JSON array
    locations       TEXT,                 -- JSON array
    is_hiring       INTEGER,              -- 0/1
    logo_url        TEXT
);

CREATE TABLE IF NOT EXISTS sponsorship (
    company_id      TEXT PRIMARY KEY REFERENCES companies(id),
    employer_name   TEXT,                 -- the DOL-side name we matched from
    total_lcas      INTEGER,
    h1b_count       INTEGER,
    h1b1_sg_count   INTEGER,
    h1b1_cl_count   INTEGER,
    e3_count        INTEGER,
    most_recent_date TEXT,
    median_wage_usd REAL,
    top_titles      TEXT                  -- JSON array
);

CREATE INDEX IF NOT EXISTS ix_companies_stage ON companies(stage);
CREATE INDEX IF NOT EXISTS ix_companies_is_hiring ON companies(is_hiring);
CREATE INDEX IF NOT EXISTS ix_sponsorship_h1b1_sg ON sponsorship(h1b1_sg_count);
"""


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_companies(conn: sqlite3.Connection, companies: list[dict]) -> None:
    rows = [
        (
            c["source_id"], c["name"], c["slug"], c["one_liner"], c["long_description"],
            c["website"], c["yc_url"], c["yc_batch"], c["team_size"], c["stage"],
            c["status"], json.dumps(c["industries"]), json.dumps(c["tags"]),
            json.dumps(c["locations"]), int(c["is_hiring"]), c["logo_url"],
        )
        for c in companies
    ]
    conn.executemany(
        """
        INSERT OR REPLACE INTO companies
            (id, name, slug, one_liner, long_description, website, yc_url,
             yc_batch, team_size, stage, status, industries, tags, locations,
             is_hiring, logo_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    log.info("Upserted %d companies", len(rows))


def upsert_sponsorship(
    conn: sqlite3.Connection,
    employer_to_company_id: dict[str, str],
    summary_df,
) -> None:
    """Attach sponsorship summary rows to their matched company_id."""
    if summary_df is None or summary_df.empty:
        log.info("No sponsorship data to load")
        return

    rows = []
    for _, r in summary_df.iterrows():
        emp = r["employer_name"]
        cid = employer_to_company_id.get(emp)
        if not cid:
            continue
        rows.append((
            cid, emp,
            int(r["total_lcas"]),
            int(r["h1b_count"]),
            int(r["h1b1_sg_count"]),
            int(r["h1b1_cl_count"]),
            int(r["e3_count"]),
            str(r["most_recent_date"]) if r["most_recent_date"] is not None else None,
            float(r["median_wage_usd"]) if r["median_wage_usd"] is not None else None,
            json.dumps(list(r["top_titles"])),
        ))

    conn.executemany(
        """
        INSERT OR REPLACE INTO sponsorship
            (company_id, employer_name, total_lcas, h1b_count, h1b1_sg_count,
             h1b1_cl_count, e3_count, most_recent_date, median_wage_usd, top_titles)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    log.info("Attached sponsorship data to %d companies", len(rows))


def export_to_json(conn: sqlite3.Connection, out_path: Path) -> None:
    """
    Join companies + sponsorship into one JSON file consumed by the frontend.

    Shape:
        {
          "generated_at": "...",
          "companies": [ { ...company fields..., "sponsorship": {...} | null }, ... ]
        }
    """
    from datetime import datetime, timezone

    cursor = conn.execute("""
        SELECT c.*, s.total_lcas, s.h1b_count, s.h1b1_sg_count, s.h1b1_cl_count,
               s.e3_count, s.most_recent_date, s.median_wage_usd, s.top_titles,
               s.employer_name AS dol_employer_name
        FROM companies c
        LEFT JOIN sponsorship s ON c.id = s.company_id
        ORDER BY
            (s.total_lcas IS NULL) ASC,           -- sponsored companies first
            COALESCE(s.total_lcas, 0) DESC,       -- most-sponsoring first
            c.is_hiring DESC,                     -- then hiring flag
            c.name ASC
    """)

    companies = []
    for row in cursor:
        c = dict(row)
        # Unpack JSON columns
        for jsonf in ("industries", "tags", "locations"):
            c[jsonf] = json.loads(c[jsonf] or "[]")
        # Nest sponsorship
        if c["total_lcas"] is not None:
            c["sponsorship"] = {
                "employer_name": c.pop("dol_employer_name"),
                "total_lcas": c.pop("total_lcas"),
                "h1b_count": c.pop("h1b_count"),
                "h1b1_sg_count": c.pop("h1b1_sg_count"),
                "h1b1_cl_count": c.pop("h1b1_cl_count"),
                "e3_count": c.pop("e3_count"),
                "most_recent_date": c.pop("most_recent_date"),
                "median_wage_usd": c.pop("median_wage_usd"),
                "top_titles": json.loads(c.pop("top_titles") or "[]"),
            }
        else:
            c["sponsorship"] = None
            for k in ("total_lcas", "h1b_count", "h1b1_sg_count", "h1b1_cl_count",
                      "e3_count", "most_recent_date", "median_wage_usd", "top_titles",
                      "dol_employer_name"):
                c.pop(k, None)
        c["is_hiring"] = bool(c["is_hiring"])
        companies.append(c)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "company_count": len(companies),
        "companies": companies,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    log.info("Exported %d companies to %s (%.1f KB)",
             len(companies), out_path, out_path.stat().st_size / 1024)
