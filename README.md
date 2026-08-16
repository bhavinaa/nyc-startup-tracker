# NYC Startup Visa Tracker

A public site listing NYC YC-backed startups joined with their U.S. Department
of Labor H-1B and H-1B1 sponsorship history. Built to help international
students (particularly Singapore/Chile citizens, who qualify for the
lottery-free H-1B1) find NYC startups with a real sponsorship track record.

**Live data sources**, all free and public:
- Y Combinator company directory via `yc-oss.github.io/api`
- DOL OFLC Labor Condition Application disclosure files
- SEC EDGAR Form D filings (stub — see roadmap)

## Architecture

```
    ┌─────────────────────────────────────────────────────────────┐
    │  GitHub Actions (weekly cron)                                │
    │                                                              │
    │   YC API ──┐                                                 │
    │            ├──► Python pipeline ──► SQLite ──► data.json ──┐ │
    │   DOL XLSX ┘         (fuzzy join)                          │ │
    │                                                            │ │
    │                                          git commit ◄──────┘ │
    └─────────────────────────────────────────────────────────────┘
                                    │
                                    │ push to main
                                    ▼
                          ┌──────────────────┐
                          │  Vercel          │
                          │  (auto-deploys   │
                          │   React app)     │
                          └──────────────────┘
```

**Key design decisions:**
- **No backend server.** Everything is precomputed by the pipeline into a static
  `data.json` file. React reads it client-side. This means $0 hosting, no
  scaling worries, and no auth complexity.
- **SQLite as the pipeline's storage, JSON as the frontend's input.** SQL is
  the right tool for fuzzy-joining three heterogeneous data sources; JSON is
  the right shape for a browser to filter <10k rows client-side. Right tool
  for each job.
- **The refresh loop is a `git commit`.** GitHub Actions runs the pipeline,
  commits the new `data.json`, and that push triggers Vercel to redeploy.
  Elegant, cheap, and reliable.
- **Fuzzy company-name matching is the interesting engineering.** Three
  sources, no shared IDs, three different name conventions — a manual review
  loop with saved overrides handles the ambiguous cases.

## Directory layout

```
.
├── pipeline/               # Python data pipeline
│   ├── main.py             # Orchestrator entrypoint
│   ├── sources/
│   │   ├── yc.py           # YC directory fetcher
│   │   ├── dol.py          # DOL LCA disclosure fetcher
│   │   └── sec.py          # SEC Form D (stub)
│   ├── matching.py         # Fuzzy company-name matching
│   ├── database.py         # SQLite schema + JSON export
│   ├── generate_sample_data.py   # Ships sample data.json for local dev
│   ├── manual_overrides.json     # Employer -> YC company overrides
│   └── requirements.txt
│
├── web/                    # React frontend (Vite + TS + Tailwind)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── hooks/
│   │   └── types.ts
│   ├── public/
│   │   └── data.json       # Consumed by the frontend, committed to repo
│   ├── package.json
│   └── vite.config.ts
│
├── data/                   # Pipeline outputs (gitignored except sample data.json)
├── .github/workflows/
│   └── refresh-data.yml    # Weekly cron
├── vercel.json             # Deploy config
└── README.md
```

## Quick start

### 1. Frontend only (fastest path to something running)

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`. You'll see the site with ~8 sample companies.
This works because `web/public/data.json` is committed to the repo.

### 2. Regenerate the sample data

```bash
python3 -m pip install -r pipeline/requirements.txt
python3 pipeline/generate_sample_data.py
```

### 3. Run the real pipeline (with actual DOL data)

The DOL disclosure file is 200–400 MB and its URL changes each quarter. Get
the current URL from the OFLC performance page:

> https://www.dol.gov/agencies/eta/foreign-labor/performance

Look under "Disclosure Data" for the most recent LCA disclosure file
(H-1B, H-1B1, E-3). Copy the .xlsx URL, then:

```bash
export DOL_XLSX_URL="https://www.dol.gov/sites/dolgov/files/ETA/oflc/pdfs/LCA_Disclosure_Data_FY2026_Q2.xlsx"
python3 -m pipeline.main
```

The pipeline will:
1. Fetch all YC companies and filter to NYC (~1 sec)
2. Download the DOL XLSX (~1 min on decent internet)
3. Parse it, filter to NY-worksite certified LCAs (~1–3 min)
4. Fuzzy-match employers to YC companies
5. Write `data/companies.db` (SQLite) and `web/public/data.json` (frontend)
6. Write `data/matches_to_review.csv` — open this and see the ambiguous
   matches. For each real match, add an entry to
   `pipeline/manual_overrides.json` and re-run. Those decisions are permanent.

### 4. Deploy to Vercel

1. Push this repo to GitHub.
2. In Vercel, "Add New Project" → import the repo.
3. Vercel reads `vercel.json` and builds from `web/`. Done.

### 5. Automate the weekly refresh

1. In your repo's GitHub settings, add a Variable named `DOL_XLSX_URL`
   with the current quarter's DOL file URL.
2. The Action at `.github/workflows/refresh-data.yml` will run weekly and
   commit any changes. Update `DOL_XLSX_URL` when a new quarter drops
   (~every 3 months).

## Local development workflow

- Edit React code in `web/src/`, live-reload at `localhost:5173`
- Edit pipeline in `pipeline/`, re-run `python3 -m pipeline.main`
- The frontend just re-fetches `data.json` on refresh, no rebuild needed

## Roadmap

Things worth adding later, roughly in priority order:

1. **Non-YC NYC startups.** Right now we only see YC-backed companies. Adding
   a source that pulls all NYC-based Form D filings (SEC EDGAR) would widen
   the corpus to any startup that has raised a priced round. See stub in
   `pipeline/sources/sec.py`.
2. **Historical LCA data.** Currently we only ingest the most recent quarter
   the user has downloaded. Ingesting all published quarters back to ~2020
   would give real trend data ("this company sponsored 5/quarter in 2022,
   then 0 since 2023 — probably not sponsoring anymore").
3. **USCIS approval cross-check.** LCA = intent to sponsor. USCIS I-129
   approval = they actually got the person. USCIS publishes annual counts per
   employer at uscis.gov/tools/reports-and-studies/h-1b-employer-data-hub.
4. **Job scraping.** YC's `isHiring` flag doesn't tell you which specific
   roles are open. Ashby, Greenhouse, and Lever job boards have public JSON
   endpoints for many companies — scraping these gets you actual role listings.
5. **Personal application tracker.** Add a "starred" / "applied" flag stored
   in `localStorage` (no backend needed).
6. **sql.js in the browser.** If the data grows past ~5MB, swap the JSON
   fetch for `sql.js` loading `companies.db` directly. Enables complex
   client-side queries and keeps the no-backend architecture.

## Honest caveats

- **Sponsorship data is a signal, not a promise.** A certified LCA is what
  an employer files *before* filing a visa petition. Companies can and do
  file LCAs and then not follow through. Say "certified LCAs on file", not
  "sponsors visas".
- **The DOL file format changes.** OFLC has renamed columns and restructured
  files a few times. If the pipeline breaks on ingestion, first check the
  record-layout PDF on the OFLC performance page against the columns in
  `pipeline/sources/dol.py`.
- **Fuzzy matching misses.** Some real employer-to-YC matches will slip
  through. Manually spot-check well-known NYC YC companies you know sponsor
  (Ramp, Cedar, Flatiron Health) after each pipeline run — if their
  sponsorship count looks wrong, they probably need a manual override.

## Credits

- YC data mirror: [yc-oss/api](https://github.com/yc-oss/api)
- DOL disclosure data: U.S. Department of Labor OFLC

Not affiliated with Y Combinator, USCIS, or the Department of Labor.
