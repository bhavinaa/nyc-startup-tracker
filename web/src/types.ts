export interface Sponsorship {
  employer_name: string;
  total_lcas: number;
  h1b_count: number;
  h1b1_sg_count: number;
  h1b1_cl_count: number;
  e3_count: number;
  most_recent_date: string | null;
  median_wage_usd: number | null;
  top_titles: string[];
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  one_liner: string;
  long_description: string;
  website: string;
  yc_url: string;
  yc_batch: string;
  team_size: number | null;
  stage: string;         // "Early" | "Growth" | ""
  status: string;        // "Active" | "Public" | "Acquired" | "Inactive"
  industries: string[];
  tags: string[];
  locations: string[];
  is_hiring: boolean;
  logo_url: string;
  sponsorship: Sponsorship | null;
}

export interface DataFile {
  generated_at: string;
  company_count: number;
  companies: Company[];
  _note?: string;
}

export type StageFilter = "all" | "early" | "growth";
export type SponsorFilter = "all" | "any" | "h1b1_sg" | "h1b";
