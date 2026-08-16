"""
SEC EDGAR Form D data — filings by private companies raising priced rounds.

Form D is filed within 15 days of a Regulation D exempt offering (which
includes almost all US VC rounds). It's a strong signal a company is:
  (a) private (public companies file 10-K/10-Q, not Form D)
  (b) actually raising money (not just incorporated)
  (c) roughly what stage (from offering size)

EDGAR full-text search JSON endpoint:
    https://efts.sec.gov/LATEST/search-index?q=&forms=D&dateRange=custom&...

For MVP simplicity we use a stub here — SEC EDGAR's rate limits and pagination
make it a project of its own. See TODO below for the upgrade path.
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def fetch_recent_ny_form_d() -> list[dict]:
    """
    TODO: Implement full SEC EDGAR ingestion.

    Approach when you get to it:
      1. Query EDGAR full-text search for Form D filings, state=NY, last 4 years:
         https://efts.sec.gov/LATEST/search-index?forms=D&locationCode=NY
      2. For each hit, fetch the filing's primary XML (structured Form D data).
      3. Extract: entity_name, offering_amount_total, industry, filing_date.
      4. Return as list of dicts matching the shape below.
    Rate limit: SEC caps you at 10 req/sec. Send a real User-Agent with your
    email address (they enforce this and will block anonymous scrapers).

    For MVP: we return [] and rely on YC's `stage` field for funding-stage
    filtering. This gives you Series A/B/C signal via YC's classification
    ('Early' / 'Growth') which is coarse but honest.
    """
    log.info("SEC Form D fetcher is stubbed — returning empty. See sources/sec.py for the upgrade path.")
    return []
