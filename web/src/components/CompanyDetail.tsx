import { useEffect } from "react";
import type { Company } from "../types";

interface Props {
  company: Company;
  onClose: () => void;
}

export function CompanyDetail({ company: c, onClose }: Props) {
  // Close on Escape key
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const s = c.sponsorship;

  return (
    <div
      className="fixed inset-0 z-50 bg-ink/30 backdrop-blur-sm flex items-start justify-center overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="bg-white max-w-2xl w-full mx-4 mt-16 mb-16 rounded shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="rule px-6 py-4 flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold">{c.name}</h2>
            <p className="text-sm text-muted mt-1">
              {c.yc_batch}
              {c.team_size ? ` · ${c.team_size} people` : ""}
              {c.stage ? ` · ${c.stage}` : ""} · {c.status}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-muted hover:text-ink text-xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="px-6 py-4 space-y-6">
          {c.one_liner && (
            <p className="text-ink/90">{c.one_liner}</p>
          )}

          <section>
            <h3 className="text-xs uppercase tracking-wider text-muted mb-2">
              Links
            </h3>
            <div className="flex gap-4 text-sm">
              {c.website && (
                <a
                  href={c.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent hover:underline underline-offset-4"
                >
                  Website ↗
                </a>
              )}
              {c.yc_url && (
                <a
                  href={c.yc_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent hover:underline underline-offset-4"
                >
                  YC page ↗
                </a>
              )}
              {c.website && (
                <a
                  href={c.website.replace(/\/$/, "") + "/careers"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent hover:underline underline-offset-4"
                >
                  Careers (guessed) ↗
                </a>
              )}
            </div>
          </section>

          {s && (
            <section>
              <h3 className="text-xs uppercase tracking-wider text-muted mb-2">
                Sponsorship history (public DOL data)
              </h3>
              <div className="grid grid-cols-4 gap-4 mb-3">
                <Metric label="Total LCAs" value={s.total_lcas} />
                <Metric label="H-1B" value={s.h1b_count} />
                <Metric label="H-1B1 SG" value={s.h1b1_sg_count} accent />
                <Metric label="E-3 AUS" value={s.e3_count} />
              </div>
              <dl className="text-sm space-y-1">
                <Row
                  k="Most recent"
                  v={
                    s.most_recent_date
                      ? new Date(s.most_recent_date).toLocaleDateString()
                      : "—"
                  }
                />
                <Row
                  k="Median wage"
                  v={
                    s.median_wage_usd
                      ? `$${Math.round(s.median_wage_usd).toLocaleString()}/yr`
                      : "—"
                  }
                />
                <Row k="DOL employer name" v={s.employer_name} mono />
                {s.top_titles.length > 0 && (
                  <Row k="Top titles" v={s.top_titles.join(", ")} />
                )}
              </dl>
              <p className="mt-3 text-xs text-muted">
                A certified LCA is a filing an employer must submit before
                sponsoring a specific role at a specific wage. Prior LCAs
                indicate the employer has done the process before — they do not
                guarantee future sponsorship.
              </p>
            </section>
          )}

          {!s && (
            <section>
              <h3 className="text-xs uppercase tracking-wider text-muted mb-2">
                Sponsorship history
              </h3>
              <p className="text-sm text-muted">
                No certified LCAs matched to this company in the current data
                snapshot. This may mean they have never sponsored, or the name
                didn't match our records — check DOL's public database directly
                to be sure.
              </p>
            </section>
          )}

          {c.industries.length > 0 && (
            <section>
              <h3 className="text-xs uppercase tracking-wider text-muted mb-2">
                Industries
              </h3>
              <div className="flex gap-1.5 flex-wrap">
                {c.industries.map((i) => (
                  <span
                    key={i}
                    className="text-xs border border-rule px-2 py-0.5 rounded"
                  >
                    {i}
                  </span>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent?: boolean;
}) {
  return (
    <div>
      <div
        className={`text-2xl font-semibold tabular-nums ${
          accent && value > 0 ? "text-accent" : "text-ink"
        }`}
      >
        {value}
      </div>
      <div className="text-[10px] uppercase tracking-wider text-muted">
        {label}
      </div>
    </div>
  );
}

function Row({ k, v, mono }: { k: string; v: string; mono?: boolean }) {
  return (
    <div className="grid grid-cols-[130px_1fr] gap-2">
      <dt className="text-muted">{k}</dt>
      <dd className={mono ? "font-mono text-xs" : ""}>{v}</dd>
    </div>
  );
}
