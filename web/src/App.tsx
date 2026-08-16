import { useMemo, useState } from "react";
import { useCompanies } from "./hooks/useCompanies";
import { FilterBar } from "./components/FilterBar";
import { CompanyCard } from "./components/CompanyCard";
import { CompanyDetail } from "./components/CompanyDetail";
import { MethodologyModal } from "./components/MethodologyModal";
import type { Company, SponsorFilter, StageFilter } from "./types";

export function App() {
  const { data, loading, error } = useCompanies();

  const [query, setQuery] = useState("");
  const [stage, setStage] = useState<StageFilter>("all");
  const [sponsor, setSponsor] = useState<SponsorFilter>("all");
  const [hiringOnly, setHiringOnly] = useState(false);
  const [selected, setSelected] = useState<Company | null>(null);
  const [showMethodology, setShowMethodology] = useState(false);

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toLowerCase();
    return data.companies.filter((c) => {
      if (hiringOnly && !c.is_hiring) return false;
      if (stage === "early" && c.stage !== "Early") return false;
      if (stage === "growth" && c.stage !== "Growth") return false;
      if (sponsor === "any" && !c.sponsorship) return false;
      if (sponsor === "h1b" && (c.sponsorship?.h1b_count ?? 0) === 0) return false;
      if (sponsor === "h1b1_sg" && (c.sponsorship?.h1b1_sg_count ?? 0) === 0)
        return false;
      if (q) {
        const hay = [
          c.name,
          c.one_liner,
          c.tags.join(" "),
          c.industries.join(" "),
        ]
          .join(" ")
          .toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [data, query, stage, sponsor, hiringOnly]);

  const stats = useMemo(() => {
    if (!data) return null;
    const withAny = data.companies.filter((c) => c.sponsorship).length;
    const withH1b1Sg = data.companies.filter(
      (c) => (c.sponsorship?.h1b1_sg_count ?? 0) > 0
    ).length;
    return { total: data.companies.length, withAny, withH1b1Sg };
  }, [data]);

  return (
    <div className="min-h-screen">
      <Header
        generatedAt={data?.generated_at}
        onOpenMethodology={() => setShowMethodology(true)}
      />

      {loading && (
        <div className="mx-auto max-w-5xl px-6 py-16 text-muted">
          Loading NYC startups…
        </div>
      )}

      {error && (
        <div className="mx-auto max-w-5xl px-6 py-16 text-red-700">
          Couldn't load data.json — {error}. Have you run the pipeline yet?
          See README.
        </div>
      )}

      {data && stats && (
        <>
          <StatsBar stats={stats} showing={filtered.length} />

          <FilterBar
            query={query}
            onQuery={setQuery}
            stage={stage}
            onStage={setStage}
            sponsor={sponsor}
            onSponsor={setSponsor}
            hiringOnly={hiringOnly}
            onHiringOnly={setHiringOnly}
          />

          <main className="mx-auto max-w-5xl px-6 py-8">
            {filtered.length === 0 ? (
              <div className="py-16 text-center text-muted">
                No companies match your filters.
              </div>
            ) : (
              <ul className="grid gap-3">
                {filtered.map((c) => (
                  <li key={c.id}>
                    <CompanyCard company={c} onClick={() => setSelected(c)} />
                  </li>
                ))}
              </ul>
            )}
          </main>

          {data._note && (
            <div className="mx-auto max-w-5xl px-6 pb-8 text-xs text-muted">
              {data._note}
            </div>
          )}
        </>
      )}

      <Footer onOpenMethodology={() => setShowMethodology(true)} />

      {selected && (
        <CompanyDetail company={selected} onClose={() => setSelected(null)} />
      )}
      {showMethodology && (
        <MethodologyModal onClose={() => setShowMethodology(false)} />
      )}
    </div>
  );
}

function Header({
  generatedAt,
  onOpenMethodology,
}: {
  generatedAt?: string;
  onOpenMethodology: () => void;
}) {
  const dateStr = generatedAt
    ? new Date(generatedAt).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "";
  return (
    <header className="rule bg-white">
      <div className="mx-auto max-w-5xl px-6 py-6 flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            NYC Startup Visa Tracker
          </h1>
          <p className="mt-1 text-sm text-muted">
            YC-backed New York startups, joined with public H-1B and H-1B1
            sponsorship records from the U.S. Department of Labor.
          </p>
        </div>
        <button
          onClick={onOpenMethodology}
          className="text-sm text-muted hover:text-ink underline underline-offset-4"
        >
          Methodology
        </button>
      </div>
      {dateStr && (
        <div className="mx-auto max-w-5xl px-6 pb-4 text-xs text-muted">
          Data refreshed {dateStr}
        </div>
      )}
    </header>
  );
}

function StatsBar({
  stats,
  showing,
}: {
  stats: { total: number; withAny: number; withH1b1Sg: number };
  showing: number;
}) {
  return (
    <div className="rule bg-white">
      <div className="mx-auto max-w-5xl px-6 py-4 flex gap-8 text-sm">
        <Stat label="Total NYC companies" value={stats.total} />
        <Stat label="With any LCA on file" value={stats.withAny} />
        <Stat label="With H-1B1 (Singapore)" value={stats.withH1b1Sg} />
        <Stat label="Showing after filters" value={showing} highlight />
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  highlight,
}: {
  label: string;
  value: number;
  highlight?: boolean;
}) {
  return (
    <div>
      <div
        className={`text-2xl font-semibold tabular-nums ${
          highlight ? "text-accent" : "text-ink"
        }`}
      >
        {value.toLocaleString()}
      </div>
      <div className="text-xs uppercase tracking-wider text-muted">{label}</div>
    </div>
  );
}

function Footer({ onOpenMethodology }: { onOpenMethodology: () => void }) {
  return (
    <footer className="rule border-t border-b-0 mt-8 py-8">
      <div className="mx-auto max-w-5xl px-6 text-xs text-muted space-y-2">
        <p>
          Sponsorship figures reflect <em>certified Labor Condition Applications
          on file</em> with the U.S. Department of Labor's Office of Foreign
          Labor Certification. An LCA on file is not a guarantee of future
          sponsorship. See{" "}
          <button
            onClick={onOpenMethodology}
            className="underline underline-offset-2"
          >
            methodology
          </button>
          .
        </p>
        <p>
          Not affiliated with Y Combinator, USCIS, or the Department of Labor.
          Company data via yc-oss.github.io/api. LCA data via
          dol.gov/agencies/eta/foreign-labor/performance.
        </p>
      </div>
    </footer>
  );
}
