"""
Y Combinator company directory fetcher.

Source: https://yc-oss.github.io/api — unofficial but well-maintained mirror
of YC's public Algolia index, refreshed daily via GitHub Actions.
Free, no API key, no rate limits.
"""
from __future__ import annotations

import logging
import re
from typing import Iterator

import requests

log = logging.getLogger(__name__)

ALL_COMPANIES_URL = "https://yc-oss.github.io/api/companies/all.json"

# Match NYC-area locations. YC formats locations as "New York, NY, USA" or
# "Brooklyn, NY, USA" — sometimes multiple comma-separated locations.
NYC_PATTERN = re.compile(
    r"\b(?:New York City|New York|Brooklyn|Manhattan|Queens|Bronx|"
    r"Long Island City|LIC|Astoria)\b[^;]*\bNY\b",
    re.IGNORECASE,
)


def fetch_all() -> list[dict]:
    """Fetch every YC company. ~6,200 companies, ~10MB payload."""
    log.info("Fetching YC company directory from %s", ALL_COMPANIES_URL)
    resp = requests.get(
        ALL_COMPANIES_URL,
        timeout=60,
        headers={"User-Agent": "nyc-startup-tracker/1.0"},
    )
    resp.raise_for_status()
    data = resp.json()
    log.info("Fetched %d YC companies total", len(data))
    return data


def filter_nyc(companies: list[dict]) -> Iterator[dict]:
    """Yield only companies with a NYC-area location."""
    for c in companies:
        loc = c.get("all_locations") or ""
        if NYC_PATTERN.search(loc):
            yield c


def normalize(company: dict) -> dict:
    """
    Convert YC's raw format into our internal shape.

    We deliberately keep this shallow — the pipeline's join step is what
    combines this with DOL/SEC data. Here we just extract fields we care about.
    """
    return {
        "source": "yc",
        "source_id": f"yc-{company['slug']}",
        "name": company["name"],
        "slug": company["slug"],
        "one_liner": company.get("one_liner") or "",
        "long_description": company.get("long_description") or "",
        "website": company.get("website") or "",
        "yc_url": company.get("url") or "",
        "yc_batch": company.get("batch") or "",
        "team_size": company.get("team_size"),
        "stage": company.get("stage") or "",  # "Early" | "Growth"
        "status": company.get("status") or "",  # "Active" | "Public" | "Acquired" | "Inactive"
        "industries": company.get("industries") or [],
        "tags": company.get("tags") or [],
        "locations": [company.get("all_locations", "")],
        "is_hiring": bool(company.get("isHiring")),
        "logo_url": company.get("small_logo_thumb_url") or "",
    }
