import type { SponsorFilter, StageFilter } from "../types";

interface Props {
  query: string;
  onQuery: (q: string) => void;
  stage: StageFilter;
  onStage: (s: StageFilter) => void;
  sponsor: SponsorFilter;
  onSponsor: (s: SponsorFilter) => void;
  hiringOnly: boolean;
  onHiringOnly: (b: boolean) => void;
}

export function FilterBar({
  query, onQuery, stage, onStage, sponsor, onSponsor, hiringOnly, onHiringOnly,
}: Props) {
  return (
    <div className="rule bg-white sticky top-0 z-10">
      <div className="mx-auto max-w-5xl px-6 py-3 flex flex-wrap gap-3 items-center">
        <input
          type="search"
          value={query}
          onChange={(e) => onQuery(e.target.value)}
          placeholder="Search by name, industry, tag…"
          className="flex-1 min-w-[220px] px-3 py-2 text-sm border border-rule rounded focus:outline-none focus:ring-2 focus:ring-accent/40"
        />

        <SegmentedControl
          label="Stage"
          value={stage}
          onChange={onStage}
          options={[
            { value: "all", label: "All" },
            { value: "early", label: "Early" },
            { value: "growth", label: "Growth" },
          ]}
        />

        <SegmentedControl
          label="Sponsorship"
          value={sponsor}
          onChange={onSponsor}
          options={[
            { value: "all", label: "Any" },
            { value: "any", label: "Has LCA" },
            { value: "h1b", label: "H-1B" },
            { value: "h1b1_sg", label: "H-1B1 SG" },
          ]}
        />

        <label className="flex items-center gap-2 text-sm text-muted">
          <input
            type="checkbox"
            checked={hiringOnly}
            onChange={(e) => onHiringOnly(e.target.checked)}
            className="accent-accent"
          />
          Hiring now
        </label>
      </div>
    </div>
  );
}

function SegmentedControl<T extends string>({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: T;
  onChange: (v: T) => void;
  options: { value: T; label: string }[];
}) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-muted text-xs uppercase tracking-wider">{label}</span>
      <div className="flex border border-rule rounded overflow-hidden">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={`px-2.5 py-1 text-xs ${
              value === opt.value
                ? "bg-ink text-white"
                : "bg-white text-ink hover:bg-paper"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
