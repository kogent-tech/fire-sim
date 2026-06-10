// Mirrors fire_sim/api/schemas.py

export type Method = "historical" | "montecarlo" | "cape" | "compare";
export type WithdrawalStrategy = "fixed" | "guyton_klinger" | "constant_percentage";
export type MonteCarloMode = "lognormal" | "block_bootstrap";

export const DEFAULT_PERCENTILES = [5, 25, 50, 75, 95] as const;

export interface ScenarioRequest {
  method: Method;
  starting_balance: number;
  stock_alloc: number;
  withdrawal_rate: number;
  horizon_years: number;
  withdrawal_strategy: WithdrawalStrategy;
  percentiles: number[];
  mc_mode: MonteCarloMode;
  n_paths: number;
  block_months: number;
  seed: number | null;
  current_cape: number | null;
  upper_guardrail: number;
  lower_guardrail: number;
  adjustment_pct: number;
}

export const DEFAULT_SCENARIO: ScenarioRequest = {
  method: "historical",
  starting_balance: 1_000_000,
  stock_alloc: 0.6,
  withdrawal_rate: 0.04,
  horizon_years: 30,
  withdrawal_strategy: "fixed",
  percentiles: [...DEFAULT_PERCENTILES],
  mc_mode: "lognormal",
  n_paths: 2000,
  block_months: 12,
  seed: 42,
  current_cape: null,
  upper_guardrail: 1.2,
  lower_guardrail: 0.0,
  adjustment_pct: 0.1,
};

export interface PercentileBands {
  months: number[];
  series: Record<string, number[]>;
}

export interface SimulationResponse {
  method: string;
  withdrawal_strategy: string;
  n_paths: number;
  success_rate: number;
  starting_balance: number;
  stock_alloc: number;
  withdrawal_rate: number;
  horizon_years: number;
  balance_percentiles: PercentileBands;
  ending_balance_percentiles: Record<string, number>;
}

export interface CapeModelInfo {
  slope: number;
  intercept: number;
  r_squared: number;
  n: number;
}

export interface CapeResponse {
  current_cape: number;
  suggested_withdrawal_rate: number;
  model: CapeModelInfo;
}

export interface CapeMethodResponse {
  cape: CapeResponse;
  simulation: SimulationResponse;
}

export interface CompareResponse {
  results: Record<string, SimulationResponse>;
  cape: CapeResponse;
}

export type SimulateResponse = SimulationResponse | CapeMethodResponse | CompareResponse;

export function isCapeMethodResponse(r: SimulateResponse): r is CapeMethodResponse {
  return "simulation" in r && "cape" in r;
}

export function isCompareResponse(r: SimulateResponse): r is CompareResponse {
  return "results" in r;
}

export interface SuccessRateCurvePoint {
  withdrawal_rate: number;
  success_rate: number;
}

export interface SuccessRateCurveRequest {
  method: "historical" | "montecarlo";
  stock_alloc: number;
  horizon_years: number;
  starting_balance: number;
  wr_min: number;
  wr_max: number;
  wr_step: number;
  mc_mode: MonteCarloMode;
  n_paths: number;
  block_months: number;
  seed: number | null;
}

export interface SuccessRateCurveResponse {
  method: string;
  stock_alloc: number;
  horizon_years: number;
  points: SuccessRateCurvePoint[];
}

export interface SequenceRiskRequest {
  stock_alloc: number;
  withdrawal_rate: number;
  horizon_years: number;
  starting_balance: number;
  period_years: number;
  downsample_months: number;
}

export interface SequenceRiskSensitivity {
  early_return_corr_with_ending_balance: number;
  late_return_corr_with_ending_balance: number;
  early_return_mean_success: number;
  late_return_mean_success: number;
  early_return_mean_failure: number | null;
  late_return_mean_failure: number | null;
}

export interface SequenceRiskPath {
  start_date: string;
  early_return: number;
  late_return: number;
  success: boolean;
  ending_balance: number;
  balances: number[];
}

export interface SequenceRiskResponse {
  stock_alloc: number;
  withdrawal_rate: number;
  horizon_years: number;
  period_years: number;
  months: number[];
  success_rate: number;
  sensitivity: SequenceRiskSensitivity;
  paths: SequenceRiskPath[];
}

export interface ApiError {
  error: {
    type: string;
    message: unknown;
  };
}
