"""
DOL Office of Foreign Labor Certification (OFLC) LCA disclosure data.

Every certified Labor Condition Application filed by an employer to sponsor
H-1B, H-1B1 (Singapore/Chile), or E-3 workers is published quarterly.

Source page (URLs rotate per quarter — check for latest release):
    https://www.dol.gov/agencies/eta/foreign-labor/performance

The file is ~200-400MB Excel per quarter, ~700K rows. We read it in chunks
and keep only NY-worksite rows to stay under GitHub Actions memory limits.

IMPORTANT: You must update DOL_XLSX_URL each time OFLC releases a new quarter
(roughly Feb/May/Aug/Nov). The link pattern is discoverable from the
performance page above.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

log = logging.getLogger(__name__)

# TODO(you): Replace with the current quarter's file URL from
# https://www.dol.gov/agencies/eta/foreign-labor/performance
# As of FY2026 Q1, files look like:
#   https://www.dol.gov/sites/dolgov/files/ETA/oflc/pdfs/LCA_Disclosure_Data_FY2026_Q1.xlsx
DOL_XLSX_URL: Optional[str] = os.environ.get("DOL_XLSX_URL")

# Fields we want. DOL's schema evolves — verify against the record layout PDF
# on the OFLC performance page when a new quarter drops.
WANTED_COLUMNS = [
    "CASE_NUMBER",
    "CASE_STATUS",
    "VISA_CLASS",  # 'H-1B' | 'H-1B1 Singapore' | 'H-1B1 Chile' | 'E-3 Australian'
    "JOB_TITLE",
    "SOC_TITLE",
    "FULL_TIME_POSITION",
    "BEGIN_DATE",
    "DECISION_DATE",
    "EMPLOYER_NAME",
    "EMPLOYER_CITY",
    "EMPLOYER_STATE",
    "WORKSITE_CITY",
    "WORKSITE_STATE",
    "WAGE_RATE_OF_PAY_FROM",
    "WAGE_UNIT_OF_PAY",
]


def download_if_needed(cache_dir: Path) -> Optional[Path]:
    """Download the DOL file to cache_dir if not already present."""
    if not DOL_XLSX_URL:
        log.warning(
            "DOL_XLSX_URL not set — skipping DOL ingestion. "
            "See pipeline/sources/dol.py for how to configure."
        )
        return None

    cache_dir.mkdir(parents=True, exist_ok=True)
    filename = DOL_XLSX_URL.rsplit("/", 1)[-1]
    dest = cache_dir / filename

    if dest.exists():
        log.info("Using cached DOL file at %s (%.1f MB)", dest, dest.stat().st_size / 1e6)
        return dest

    log.info("Downloading DOL disclosure file (large, ~200-400MB) from %s", DOL_XLSX_URL)
    with requests.get(DOL_XLSX_URL, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):  # 1MB chunks
                f.write(chunk)
    log.info("Saved to %s (%.1f MB)", dest, dest.stat().st_size / 1e6)
    return dest


def load_ny_lcas(xlsx_path: Path) -> pd.DataFrame:
    """
    Load only NY-worksite LCA rows from the disclosure file.

    Uses openpyxl streaming under the hood via pandas. On a big file this
    still takes a minute or two on a modest machine but stays memory-safe.
    """
    log.info("Reading LCA file %s (may take 1-3 min for a large file)", xlsx_path)
    df = pd.read_excel(
        xlsx_path,
        usecols=lambda c: c in WANTED_COLUMNS,
        dtype=str,
        engine="openpyxl",
    )
    log.info("Read %d total LCA rows", len(df))

    # Filter to NY worksite and certified only (denied/withdrawn don't count)
    df = df[
        (df["WORKSITE_STATE"] == "NY")
        & (df["CASE_STATUS"].str.upper() == "CERTIFIED")
    ].copy()
    log.info("After NY + certified filter: %d rows", len(df))
    return df


def summarize_by_employer(ny_df: pd.DataFrame) -> pd.DataFrame:
    """
    Group NY LCAs by employer and compute a summary row per employer.

    Returns columns: employer_name, total_lcas, h1b_count, h1b1_sg_count,
    h1b1_cl_count, e3_count, most_recent_date, median_wage_usd, top_titles.
    """
    if ny_df.empty:
        return pd.DataFrame()

    # Normalize wage to annual USD. DOL reports hourly/weekly/monthly/annual.
    def to_annual(row) -> float | None:
        try:
            rate = float(row["WAGE_RATE_OF_PAY_FROM"])
        except (ValueError, TypeError):
            return None
        unit = (row["WAGE_UNIT_OF_PAY"] or "").upper()
        return {
            "YEAR": rate,
            "HOUR": rate * 2080,
            "WEEK": rate * 52,
            "BI-WEEKLY": rate * 26,
            "MONTH": rate * 12,
        }.get(unit)

    ny_df = ny_df.copy()
    ny_df["_annual_wage"] = ny_df.apply(to_annual, axis=1)
    ny_df["_visa"] = ny_df["VISA_CLASS"].fillna("").str.upper()

    rows = []
    for name, group in ny_df.groupby("EMPLOYER_NAME"):
        titles = group["JOB_TITLE"].value_counts().head(3).index.tolist()
        rows.append({
            "employer_name": name,
            "total_lcas": len(group),
            "h1b_count": int((group["_visa"] == "H-1B").sum()),
            "h1b1_sg_count": int(group["_visa"].str.contains("H-1B1 SINGAPORE").sum()),
            "h1b1_cl_count": int(group["_visa"].str.contains("H-1B1 CHILE").sum()),
            "e3_count": int(group["_visa"].str.contains("E-3").sum()),
            "most_recent_date": group["DECISION_DATE"].max(),
            "median_wage_usd": (
                float(group["_annual_wage"].median())
                if group["_annual_wage"].notna().any() else None
            ),
            "top_titles": titles,
        })
    result = pd.DataFrame(rows)
    log.info("Summarized to %d distinct NY employers with certified LCAs", len(result))
    return result
