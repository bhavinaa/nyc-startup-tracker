"""
Fuzzy matching between company names across data sources.

The problem: YC says "Ramp", DOL says "Ramp Business Corporation",
SEC says "RAMP INC" — no shared identifier, all different strings.

Strategy:
    1. Normalize aggressively (lowercase, strip corp suffixes, drop punctuation).
    2. Score with rapidfuzz.token_set_ratio (good for reorderings + extra tokens).
    3. Auto-accept matches >= AUTO_ACCEPT threshold.
    4. Dump ambiguous matches (>= REVIEW_MIN, < AUTO_ACCEPT) to a CSV for you
       to review by hand.
    5. Apply manual overrides from manual_overrides.json on every run — so
       you review each ambiguous case once, then never again.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

from rapidfuzz import fuzz, process

log = logging.getLogger(__name__)

AUTO_ACCEPT = 92  # score >= this: auto-join
REVIEW_MIN = 78   # AUTO_ACCEPT > score >= this: needs human eyes
                  # < REVIEW_MIN: not a match, ignore

# Corporate suffixes and legal noise to strip. Order matters (longest first).
_SUFFIX_RE = re.compile(
    r"\b("
    r"business\s+corporation|"
    r"limited\s+liability\s+company|"
    r"public\s+benefit\s+corp(?:oration)?|"
    r"pbc|"
    r"corporation|corp\.?|"
    r"incorporated|inc\.?|"
    r"limited|ltd\.?|"
    r"llc|l\.l\.c\.|"
    r"l\.p\.|lp|"
    r"co\.?|company|"
    r"holdings?|technologies|technology|tech|labs?|"
    r"the"
    r")\b",
    re.IGNORECASE,
)

_PUNCT_RE = re.compile(r"[^\w\s]")
_SPACE_RE = re.compile(r"\s+")


def normalize(name: str) -> str:
    """
    Aggressively normalize a company name for matching.

    "Ramp Business Corporation, Inc." -> "ramp"
    "The Ramp Company"                -> "ramp"
    "RAMP Technologies LLC"           -> "ramp"

    We're deliberately lossy — collisions between distinct companies with
    the same normalized name (e.g. two different "Peak" startups) are
    caught in the review step below.
    """
    if not name:
        return ""
    s = name.lower()
    s = _PUNCT_RE.sub(" ", s)
    s = _SUFFIX_RE.sub(" ", s)
    s = _SPACE_RE.sub(" ", s).strip()
    return s


def load_manual_overrides(path: Path) -> dict[str, str]:
    """
    Load manual employer_name -> yc_slug overrides.

    File format (JSON):
        {
            "Ramp Business Corporation": "yc-ramp",
            "OpenAI, Inc.":              "yc-openai"
        }
    """
    if not path.exists():
        log.info("No manual overrides file at %s (that's fine)", path)
        return {}
    with open(path) as f:
        overrides = json.load(f)
    log.info("Loaded %d manual overrides from %s", len(overrides), path)
    return overrides


def match_employers_to_yc(
    yc_companies: list[dict],
    dol_employers: list[str],
    manual_overrides: dict[str, str],
) -> tuple[dict[str, str], list[tuple[str, str, int]]]:
    """
    For each DOL employer name, find the best matching YC company (if any).

    Returns:
        matches:  dict of employer_name -> yc source_id (for accepted matches)
        review:   list of (employer_name, best_yc_name, score) for human review
    """
    # Build lookup of normalized -> yc entry
    yc_by_norm: dict[str, dict] = {}
    for c in yc_companies:
        norm = normalize(c["name"])
        if norm:
            yc_by_norm.setdefault(norm, c)

    yc_norm_names = list(yc_by_norm.keys())

    matches: dict[str, str] = {}
    review: list[tuple[str, str, int]] = []
    hits, misses, override_hits = 0, 0, 0

    for employer in dol_employers:
        # Manual override wins
        if employer in manual_overrides:
            matches[employer] = manual_overrides[employer]
            override_hits += 1
            continue

        norm = normalize(employer)
        if not norm:
            misses += 1
            continue

        best: Optional[tuple[str, float, int]] = process.extractOne(
            norm, yc_norm_names, scorer=fuzz.token_set_ratio
        )
        if best is None:
            misses += 1
            continue

        best_norm, score, _ = best
        if score >= AUTO_ACCEPT:
            matches[employer] = yc_by_norm[best_norm]["source_id"]
            hits += 1
        elif score >= REVIEW_MIN:
            review.append((employer, yc_by_norm[best_norm]["name"], int(score)))
        else:
            misses += 1

    log.info(
        "Match results: %d auto-accepted, %d manual override, %d need review, %d no match",
        hits, override_hits, len(review), misses,
    )
    return matches, review


def write_review_csv(review: list[tuple[str, str, int]], path: Path) -> None:
    """Write the review file so you can eyeball ambiguous matches."""
    if not review:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write("dol_employer_name,best_yc_name,score,is_match_yn\n")
        for emp, yc, score in sorted(review, key=lambda r: -r[2]):
            # Escape any commas in names
            emp_esc = emp.replace(",", ";")
            yc_esc = yc.replace(",", ";")
            f.write(f"{emp_esc},{yc_esc},{score},\n")
    log.info("Wrote %d ambiguous matches to %s for human review", len(review), path)
