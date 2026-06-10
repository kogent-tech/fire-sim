import type { ChangeEvent, FormEvent } from "react";
import type { Method, MonteCarloMode, ScenarioRequest, WithdrawalStrategy } from "../lib/types";

interface Props {
  scenario: ScenarioRequest;
  onChange: (scenario: ScenarioRequest) => void;
  onSubmit: () => void;
  loading: boolean;
}

const METHOD_LABELS: Record<Method, string> = {
  historical: "Historical (rolling windows)",
  montecarlo: "Monte Carlo",
  cape: "CAPE-adjusted",
  compare: "Compare all methods",
};

const STRATEGY_LABELS: Record<WithdrawalStrategy, string> = {
  fixed: "Fixed (inflation-adjusted)",
  guyton_klinger: "Guyton-Klinger guardrails",
  constant_percentage: "Constant % of portfolio",
};

const MC_MODE_LABELS: Record<MonteCarloMode, string> = {
  lognormal: "Lognormal",
  block_bootstrap: "Block bootstrap",
};

export default function ScenarioForm({ scenario, onChange, onSubmit, loading }: Props) {
  const set = <K extends keyof ScenarioRequest>(key: K, value: ScenarioRequest[K]) => {
    onChange({ ...scenario, [key]: value });
  };

  const setNumber = (key: keyof ScenarioRequest) => (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.valueAsNumber;
    if (!Number.isNaN(value)) set(key, value as never);
  };

  const setPercent = (key: keyof ScenarioRequest) => (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.valueAsNumber;
    if (!Number.isNaN(value)) set(key, (value / 100) as never);
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  const isHistoricalLike = scenario.method === "historical" || scenario.method === "compare";
  const showMonteCarloOptions = scenario.method === "montecarlo" || scenario.method === "compare";
  const showCapeOptions = scenario.method === "cape" || scenario.method === "compare";
  const showWithdrawalStrategy = scenario.method === "historical";
  const showGuardrails = showWithdrawalStrategy && scenario.withdrawal_strategy === "guyton_klinger";
  const showAdjustmentPct =
    showWithdrawalStrategy &&
    (scenario.withdrawal_strategy === "guyton_klinger" || scenario.withdrawal_strategy === "constant_percentage");

  return (
    <form className="scenario-form" onSubmit={handleSubmit}>
      <fieldset disabled={loading}>
        <div className="field-grid">
          <label className="field">
            <span>Method</span>
            <select value={scenario.method} onChange={(e) => set("method", e.target.value as Method)}>
              {Object.entries(METHOD_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Starting balance</span>
            <input
              type="number"
              min={1}
              step={1000}
              value={scenario.starting_balance}
              onChange={setNumber("starting_balance")}
            />
          </label>

          <label className="field">
            <span>Stock allocation (%)</span>
            <input
              type="number"
              min={0}
              max={100}
              step={1}
              value={Math.round(scenario.stock_alloc * 100)}
              onChange={setPercent("stock_alloc")}
            />
          </label>

          <label className="field">
            <span>Initial withdrawal rate (%)</span>
            <input
              type="number"
              min={0}
              max={20}
              step={0.1}
              value={Number((scenario.withdrawal_rate * 100).toFixed(2))}
              onChange={setPercent("withdrawal_rate")}
            />
          </label>

          <label className="field">
            <span>Horizon (years)</span>
            <input
              type="number"
              min={1}
              max={60}
              step={1}
              value={scenario.horizon_years}
              onChange={setNumber("horizon_years")}
            />
          </label>

          {showWithdrawalStrategy && (
            <label className="field">
              <span>Withdrawal strategy</span>
              <select
                value={scenario.withdrawal_strategy}
                onChange={(e) => set("withdrawal_strategy", e.target.value as WithdrawalStrategy)}
              >
                {Object.entries(STRATEGY_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>

        {showGuardrails && (
          <div className="field-grid">
            <label className="field">
              <span>Upper guardrail (x of initial WR)</span>
              <input
                type="number"
                min={1.01}
                step={0.05}
                value={scenario.upper_guardrail}
                onChange={setNumber("upper_guardrail")}
              />
            </label>
            <label className="field">
              <span>Lower guardrail (x of initial WR)</span>
              <input
                type="number"
                min={0}
                max={0.99}
                step={0.05}
                value={scenario.lower_guardrail}
                onChange={setNumber("lower_guardrail")}
              />
            </label>
          </div>
        )}

        {showAdjustmentPct && (
          <div className="field-grid">
            <label className="field">
              <span>Guardrail adjustment (%)</span>
              <input
                type="number"
                min={0}
                max={100}
                step={1}
                value={Math.round(scenario.adjustment_pct * 100)}
                onChange={setPercent("adjustment_pct")}
              />
            </label>
          </div>
        )}

        {showMonteCarloOptions && (
          <div className="field-group">
            <h3>Monte Carlo</h3>
            <div className="field-grid">
              <label className="field">
                <span>Return model</span>
                <select value={scenario.mc_mode} onChange={(e) => set("mc_mode", e.target.value as MonteCarloMode)}>
                  {Object.entries(MC_MODE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Paths</span>
                <input
                  type="number"
                  min={100}
                  max={20000}
                  step={100}
                  value={scenario.n_paths}
                  onChange={setNumber("n_paths")}
                />
              </label>
              {scenario.mc_mode === "block_bootstrap" && (
                <label className="field">
                  <span>Block length (months)</span>
                  <input
                    type="number"
                    min={1}
                    max={600}
                    step={1}
                    value={scenario.block_months}
                    onChange={setNumber("block_months")}
                  />
                </label>
              )}
              <label className="field">
                <span>Random seed (blank = random)</span>
                <input
                  type="number"
                  step={1}
                  value={scenario.seed ?? ""}
                  placeholder="random"
                  onChange={(e) => {
                    const v = e.target.value;
                    set("seed", v === "" ? null : Number(v));
                  }}
                />
              </label>
            </div>
          </div>
        )}

        {showCapeOptions && (
          <div className="field-group">
            <h3>CAPE</h3>
            <div className="field-grid">
              <label className="field">
                <span>Current CAPE ratio (blank = latest data)</span>
                <input
                  type="number"
                  min={0}
                  step={0.1}
                  value={scenario.current_cape ?? ""}
                  placeholder="latest"
                  onChange={(e) => {
                    const v = e.target.value;
                    set("current_cape", v === "" ? null : Number(v));
                  }}
                />
              </label>
            </div>
          </div>
        )}

        {!isHistoricalLike && (
          <p className="form-note">
            Withdrawal strategy is fixed (inflation-adjusted) for {METHOD_LABELS[scenario.method].toLowerCase()}.
          </p>
        )}

        <div className="form-actions">
          <button type="submit" disabled={loading}>
            {loading ? "Running..." : "Run simulation"}
          </button>
        </div>
      </fieldset>
    </form>
  );
}
