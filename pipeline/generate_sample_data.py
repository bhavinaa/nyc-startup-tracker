"""
Generates a realistic sample data.json so the frontend works out of the box
without you having to download the 400MB DOL disclosure file first.

Data is *representative shape* — the companies are real NYC YC companies,
the sponsorship numbers are plausible but illustrative. Replace with real
DOL data by running `python -m pipeline.main` with DOL_XLSX_URL set.

    python3 pipeline/generate_sample_data.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "public" / "data.json"

# Real NYC YC companies with plausible-but-illustrative sponsorship data.
# Do NOT cite this as real sponsorship info — the shape is real but the
# numbers are stand-ins until you run the actual DOL pipeline.
SAMPLE = [
    {
        "name": "Ramp", "slug": "ramp", "yc_batch": "Winter 2020",
        "one_liner": "Corporate cards and expense management software.",
        "website": "https://ramp.com", "team_size": 800, "stage": "Growth",
        "industries": ["Fintech"], "tags": ["Fintech", "SaaS", "B2B"],
        "is_hiring": True, "sponsorship_totals": (89, 71, 8, 0, 10),
        "median_wage": 175000, "recent": "2025-11-14",
        "titles": ["Software Engineer", "Senior Software Engineer", "Product Designer"],
    },
    {
        "name": "Cedar", "slug": "cedar", "yc_batch": "Summer 2016",
        "one_liner": "Consumer-friendly medical billing platform.",
        "website": "https://cedar.com", "team_size": 300, "stage": "Growth",
        "industries": ["Healthcare", "Healthcare IT"], "tags": ["Healthcare", "SaaS"],
        "is_hiring": True, "sponsorship_totals": (34, 30, 2, 0, 2),
        "median_wage": 158000, "recent": "2025-09-22",
        "titles": ["Software Engineer", "Data Scientist", "Product Manager"],
    },
    {
        "name": "Latch", "slug": "latch", "yc_batch": "Winter 2015",
        "one_liner": "Full-building enterprise access and IoT platform.",
        "website": "https://latch.com", "team_size": 200, "stage": "Growth",
        "industries": ["Real Estate and Construction", "Proptech"],
        "tags": ["Hardware", "IoT", "SaaS"], "is_hiring": False,
        "sponsorship_totals": (12, 11, 1, 0, 0),
        "median_wage": 142000, "recent": "2024-06-30",
        "titles": ["Firmware Engineer", "Software Engineer"],
    },
    {
        "name": "Flatiron Health", "slug": "flatiron-health", "yc_batch": "Summer 2013",
        "one_liner": "Software for oncology research and clinical care.",
        "website": "https://flatiron.com", "team_size": 900, "stage": "Growth",
        "industries": ["Healthcare"], "tags": ["Healthcare", "Data Science"],
        "is_hiring": True, "sponsorship_totals": (67, 55, 4, 1, 7),
        "median_wage": 168000, "recent": "2025-10-08",
        "titles": ["Software Engineer", "Data Scientist", "Machine Learning Engineer"],
    },
    {
        "name": "Zocdoc-adjacent Startup", "slug": "sample-b2b", "yc_batch": "Winter 2022",
        "one_liner": "B2B SaaS for medical practice management (sample entry).",
        "website": "https://example.com", "team_size": 45, "stage": "Early",
        "industries": ["B2B", "Healthcare IT"], "tags": ["SaaS", "B2B"],
        "is_hiring": True, "sponsorship_totals": None,  # No sponsorship history
        "median_wage": None, "recent": None, "titles": [],
    },
    {
        "name": "Newer AI Startup", "slug": "sample-ai", "yc_batch": "Winter 2024",
        "one_liner": "AI infrastructure for developers (sample entry).",
        "website": "https://example.com", "team_size": 12, "stage": "Early",
        "industries": ["B2B", "Infrastructure"], "tags": ["AI", "Developer Tools"],
        "is_hiring": True, "sponsorship_totals": None,
        "median_wage": None, "recent": None, "titles": [],
    },
    {
        "name": "Bigger NYC Fintech", "slug": "sample-fintech-2", "yc_batch": "Summer 2018",
        "one_liner": "Payments infrastructure for B2B (sample entry).",
        "website": "https://example.com", "team_size": 250, "stage": "Growth",
        "industries": ["Fintech", "Payments"], "tags": ["Fintech", "B2B", "SaaS"],
        "is_hiring": True, "sponsorship_totals": (22, 18, 3, 0, 1),
        "median_wage": 162000, "recent": "2025-08-15",
        "titles": ["Software Engineer", "Backend Engineer"],
    },
    {
        "name": "Brooklyn Hardware Startup", "slug": "sample-hw", "yc_batch": "Winter 2019",
        "one_liner": "Consumer hardware manufacturing (sample entry).",
        "website": "https://example.com", "team_size": 80, "stage": "Growth",
        "industries": ["Consumer", "Consumer Electronics"], "tags": ["Hardware"],
        "is_hiring": False, "sponsorship_totals": (4, 4, 0, 0, 0),
        "median_wage": 135000, "recent": "2023-11-02",
        "titles": ["Mechanical Engineer"],
    },
]


def build_company(sample: dict) -> dict:
    totals = sample["sponsorship_totals"]
    sponsorship = None
    if totals is not None:
        total, h1b, h1b1_sg, h1b1_cl, e3 = totals
        sponsorship = {
            "employer_name": sample["name"].upper() + " INC",
            "total_lcas": total,
            "h1b_count": h1b,
            "h1b1_sg_count": h1b1_sg,
            "h1b1_cl_count": h1b1_cl,
            "e3_count": e3,
            "most_recent_date": sample["recent"],
            "median_wage_usd": sample["median_wage"],
            "top_titles": sample["titles"],
        }
    return {
        "id": f"yc-{sample['slug']}",
        "name": sample["name"],
        "slug": sample["slug"],
        "one_liner": sample["one_liner"],
        "long_description": "",
        "website": sample["website"],
        "yc_url": f"https://www.ycombinator.com/companies/{sample['slug']}",
        "yc_batch": sample["yc_batch"],
        "team_size": sample["team_size"],
        "stage": sample["stage"],
        "status": "Active",
        "industries": sample["industries"],
        "tags": sample["tags"],
        "locations": ["New York, NY, USA"],
        "is_hiring": sample["is_hiring"],
        "logo_url": "",
        "sponsorship": sponsorship,
    }


def main() -> None:
    companies = [build_company(s) for s in SAMPLE]
    # Sort: sponsored first, then by total sponsorship count desc
    companies.sort(key=lambda c: (
        c["sponsorship"] is None,
        -(c["sponsorship"]["total_lcas"] if c["sponsorship"] else 0),
        not c["is_hiring"],
        c["name"],
    ))
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "company_count": len(companies),
        "companies": companies,
        "_note": "This is SAMPLE data. Run `python -m pipeline.main` with DOL_XLSX_URL set to generate real data.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {len(companies)} sample companies to {OUT}")


if __name__ == "__main__":
    main()
