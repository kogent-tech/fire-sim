import type { ScenarioRequest } from "./types";

export interface Preset {
  id: string;
  label: string;
  description: string;
  scenario: Partial<ScenarioRequest>;
}

export const PRESETS: Preset[] = [
  {
    id: "trinity-4",
    label: "Trinity Study (60/40, 4%)",
    description: "The classic 4% rule, tested against real market history.",
    scenario: {
      method: "historical",
      withdrawal_strategy: "fixed",
      stock_alloc: 0.6,
      withdrawal_rate: 0.04,
      horizon_years: 30,
    },
  },
  {
    id: "guyton-klinger-5",
    label: "Guyton-Klinger Guardrails (60/40, 5%)",
    description: "A higher starting rate, with spending adjusted up/down based on portfolio performance.",
    scenario: {
      method: "historical",
      withdrawal_strategy: "guyton_klinger",
      stock_alloc: 0.6,
      withdrawal_rate: 0.05,
      horizon_years: 30,
    },
  },
  {
    id: "cape-today",
    label: "Today's CAPE-Adjusted Rate",
    description: "What withdrawal rate today's market valuation suggests.",
    scenario: {
      method: "cape",
      stock_alloc: 0.6,
      horizon_years: 30,
    },
  },
];
