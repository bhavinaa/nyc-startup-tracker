import { useEffect } from "react";

export function MethodologyModal({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 bg-ink/30 backdrop-blur-sm flex items-start justify-center overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="bg-white max-w-2xl w-full mx-4 my-16 rounded shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="rule px-6 py-4 flex items-start justify-between">
          <h2 className="text-xl font-semibold">Methodology</h2>
          <button
            onClick={onClose}
            className="text-muted hover:text-ink text-xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="px-6 py-4 space-y-4 text-sm text-ink/90 leading-relaxed">
          <section>
            <h3 className="font-semibold mb-1">Company universe</h3>
            <p>
              Companies here are drawn from Y Combinator's public directory (via{" "}
              <code className="text-xs bg-paper px-1">yc-oss.github.io/api</code>),
              filtered to those with at least one NYC-area location. This is not
              every NYC startup — it's the YC-backed subset. Non-YC NYC startups
              (e.g. many raised via other accelerators or non-accelerator paths)
              are not included yet.
            </p>
          </section>

          <section>
            <h3 className="font-semibold mb-1">Sponsorship data</h3>
            <p>
              Every certified <em>Labor Condition Application</em> (LCA, Form
              ETA-9035) filed with the U.S. Department of Labor's Office of
              Foreign Labor Certification is published quarterly as a public
              disclosure file. We ingest the file, filter to NY-worksite
              certified rows, group by employer, and match those employers back
              to companies in our list using fuzzy name matching.
            </p>
            <p className="mt-2">
              What an LCA means: an employer must file (and get certified) an
              LCA <em>before</em> filing an H-1B, H-1B1, or E-3 visa petition
              for a specific role at a specific wage. A certified LCA on file
              indicates the employer has done the sponsorship process before.
            </p>
          </section>

          <section>
            <h3 className="font-semibold mb-1">Important caveats</h3>
            <ul className="list-disc pl-5 space-y-1">
              <li>
                An LCA on file is <strong>not</strong> a guarantee the company
                will sponsor future hires. It's a signal of past behavior.
              </li>
              <li>
                A company can file an LCA and then withdraw or not follow
                through with the visa petition. USCIS approval data (a separate
                dataset) tells the actual approval story.
              </li>
              <li>
                Name matching is fuzzy. "Ramp" (YC), "Ramp Business
                Corporation" (DOL), and "RAMP INC" (SEC) should all match, but
                imperfect normalization means some real matches may be missed
                and some false matches may sneak through.
              </li>
              <li>
                Sponsorship counts include only the most recent
                published quarters of DOL data, not the full historical record.
              </li>
            </ul>
          </section>

          <section>
            <h3 className="font-semibold mb-1">H-1B1 (Singapore &amp; Chile)</h3>
            <p>
              The H-1B1 is a separate visa category for Singapore and Chile
              citizens with a specialty-occupation job offer. Unlike the
              regular H-1B, it has no lottery, is available year-round, and its
              annual cap has historically gone unfilled. If you're a Singapore
              or Chile citizen, an H-1B1 filing on a company's record is a
              particularly strong signal — they know the process and it was
              worth their while.
            </p>
          </section>

          <section>
            <h3 className="font-semibold mb-1">Refresh cadence</h3>
            <p>
              A GitHub Actions job re-runs the pipeline weekly. YC data updates
              daily; DOL publishes new LCA quarters roughly every three months.
            </p>
          </section>

          <section>
            <h3 className="font-semibold mb-1">Source code</h3>
            <p>
              This site is open source. The full pipeline (Python) and frontend
              (React) are in the repo. See the project README for setup.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
