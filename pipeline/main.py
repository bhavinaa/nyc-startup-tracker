"""
Pipeline entrypoint. Run this to refresh the data:

    python3 -m pipeline.main

Steps:
    1. Fetch YC companies, filter to NYC.
    2. Download DOL LCA disclosure file (if DOL_XLSX_URL env var set).
    3. Filter LCAs to NY, group by employer.
    4. Fuzzy-match DOL employers to YC companies.
    5. Write everything to SQLite (companies.db) + export JSON for frontend.

Idempotent: safe to re-run. Ambiguous matches are written to a review CSV
so you can eyeball them and add to manual_overrides.json.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add project root to path so `python pipeline/main.py` works from the top
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import database, matching
from pipeline.sources import dol, sec, yc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pipeline")

# Paths
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
DB_PATH = DATA_DIR / "companies.db"
JSON_OUT = ROOT / "web" / "public" / "data.json"
REVIEW_CSV = DATA_DIR / "matches_to_review.csv"
OVERRIDES_JSON = ROOT / "pipeline" / "manual_overrides.json"


def run() -> None:
    log.info("=== NYC startup tracker pipeline starting ===")

    # --- YC ---
    all_yc = yc.fetch_all()
    nyc_raw = list(yc.filter_nyc(all_yc))
    nyc_companies = [yc.normalize(c) for c in nyc_raw]
    log.info("NYC YC companies: %d", len(nyc_companies))

    # --- DOL ---
    xlsx = dol.download_if_needed(CACHE_DIR)
    if xlsx is not None:
        ny_lcas = dol.load_ny_lcas(xlsx)
        summary_df = dol.summarize_by_employer(ny_lcas)
    else:
        summary_df = None

    # --- SEC (stub for now) ---
    _ = sec.fetch_recent_ny_form_d()

    # --- Match employers -> YC companies ---
    if summary_df is not None and not summary_df.empty:
        overrides = matching.load_manual_overrides(OVERRIDES_JSON)
        matches, review = matching.match_employers_to_yc(
            nyc_companies,
            dol_employers=summary_df["employer_name"].tolist(),
            manual_overrides=overrides,
        )
        matching.write_review_csv(review, REVIEW_CSV)
    else:
        matches = {}

    # --- Persist ---
    conn = database.open_db(DB_PATH)
    try:
        database.upsert_companies(conn, nyc_companies)
        database.upsert_sponsorship(conn, matches, summary_df)
        database.export_to_json(conn, JSON_OUT)
    finally:
        conn.close()

    log.info("=== Pipeline done ===")
    log.info("SQLite DB: %s", DB_PATH)
    log.info("Frontend JSON: %s", JSON_OUT)
    if REVIEW_CSV.exists():
        log.info("Ambiguous matches to review: %s", REVIEW_CSV)


if __name__ == "__main__":
    run()
