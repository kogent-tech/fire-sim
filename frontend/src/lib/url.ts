import { DEFAULT_SCENARIO, type ScenarioRequest } from "./types";

/** Encode a scenario as a query string, omitting fields that match the default. */
export function scenarioToParams(scenario: ScenarioRequest): URLSearchParams {
  const params = new URLSearchParams();

  for (const key of Object.keys(DEFAULT_SCENARIO) as (keyof ScenarioRequest)[]) {
    const value = scenario[key];
    const defaultValue = DEFAULT_SCENARIO[key];

    if (key === "percentiles") {
      const arr = value as number[];
      const def = defaultValue as number[];
      if (arr.length !== def.length || arr.some((v, i) => v !== def[i])) {
        params.set(key, arr.join(","));
      }
      continue;
    }

    if (value === defaultValue) continue;
    if (value === null) {
      // null differs from a non-null default (e.g. current_cape, seed) - encode explicitly.
      params.set(key, "null");
      continue;
    }

    params.set(key, String(value));
  }

  return params;
}

/** Decode a scenario from a query string, falling back to defaults for missing/invalid fields. */
export function paramsToScenario(params: URLSearchParams): ScenarioRequest {
  const scenario: ScenarioRequest = { ...DEFAULT_SCENARIO, percentiles: [...DEFAULT_SCENARIO.percentiles] };

  const str = (key: string): string | undefined => params.get(key) ?? undefined;
  const num = (key: string): number | undefined => {
    const v = params.get(key);
    if (v === null) return undefined;
    const n = Number(v);
    return Number.isFinite(n) ? n : undefined;
  };
  const nullableNum = (key: string): number | null | undefined => {
    const v = params.get(key);
    if (v === null) return undefined;
    if (v === "null") return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : undefined;
  };

  const method = str("method");
  if (method === "historical" || method === "montecarlo" || method === "cape" || method === "compare") {
    scenario.method = method;
  }

  const withdrawalStrategy = str("withdrawal_strategy");
  if (
    withdrawalStrategy === "fixed" ||
    withdrawalStrategy === "guyton_klinger" ||
    withdrawalStrategy === "constant_percentage"
  ) {
    scenario.withdrawal_strategy = withdrawalStrategy;
  }

  const mcMode = str("mc_mode");
  if (mcMode === "lognormal" || mcMode === "block_bootstrap") {
    scenario.mc_mode = mcMode;
  }

  const numericKeys: (keyof ScenarioRequest)[] = [
    "starting_balance",
    "stock_alloc",
    "withdrawal_rate",
    "horizon_years",
    "n_paths",
    "block_months",
    "upper_guardrail",
    "lower_guardrail",
    "adjustment_pct",
  ];
  for (const key of numericKeys) {
    const v = num(key);
    if (v !== undefined) (scenario[key] as number) = v;
  }

  const seed = nullableNum("seed");
  if (seed !== undefined) scenario.seed = seed;

  const currentCape = nullableNum("current_cape");
  if (currentCape !== undefined) scenario.current_cape = currentCape;

  const percentiles = str("percentiles");
  if (percentiles) {
    const parsed = percentiles
      .split(",")
      .map((p) => Number(p.trim()))
      .filter((p) => Number.isFinite(p));
    if (parsed.length > 0) scenario.percentiles = parsed;
  }

  return scenario;
}
