import type { Company } from "../types";

interface Props {
  company: Company;
  onClick: () => void;
}

export function CompanyCard({ company: c, onClick }: Props) {
  const s = c.sponsorship;
  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white border border-rule rounded p-4 hover:border-ink transition-colors flex gap-4 items-start"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-3 flex-wrap">
          <h2 className="text-lg font-semibold">{c.name}</h2>
          <span className="text-xs text-muted">
            {c.yc_batch}
            {c.team_size ? ` · ${c.team_size} people` : ""}
            {c.stage ? ` · ${c.stage}` : ""}
          </span>
          {c.is_hiring && (
            <span className="text-xs px-1.5 py-0.5 bg-accent/10 text-accent rounded">
              Hiring
            </span>
          )}
        </div>
        {c.one_liner && (
          <p className="mt-1 text-sm text-ink/80 line-clamp-2">{c.one_liner}</p>
        )}
        <div className="mt-2 flex gap-1.5 flex-wrap">
          {c.tags.slice(0, 4).map((t) => (
            <span
              key={t}
              className="text-[10px] uppercase tracking-wider text-muted border border-rule px-1.5 py-0.5 rounded"
            >
              {t}
            </span>
          ))}
        </div>
      </div>

      <div className="text-right shrink-0">
        {s ? (
          <>
            <div className="text-3xl font-semibold text-accent tabular-nums leading-none">
              {s.total_lcas}
            </div>
            <div className="text-[10px] uppercase tracking-wider text-muted mt-1">
              Certified LCAs
            </div>
            <div className="text-xs text-muted mt-2 tabular-nums">
              H-1B: {s.h1b_count}
              {s.h1b1_sg_count > 0 && (
                <span className="ml-2 text-accent font-medium">
                  H-1B1 SG: {s.h1b1_sg_count}
                </span>
              )}
            </div>
          </>
        ) : (
          <div className="text-xs text-muted">No LCAs on file</div>
        )}
      </div>
    </button>
  );
}
