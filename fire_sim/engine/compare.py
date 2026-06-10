"""Compare the historical and Monte Carlo engines on baseline scenarios.

Run with:

    python -m fire_sim.engine.compare

See docs/MC_VS_HISTORICAL.md for a written discussion of the results.
"""
import numpy as np

from fire_sim.engine.historical import run_historical_simulation
from fire_sim.engine.monte_carlo import run_monte_carlo_simulation
from fire_sim.engine.returns import load_monthly_returns

SCENARIOS = [
    {"label": "60/40, 4%, 30yr", "stock_alloc": 0.6, "withdrawal_rate": 0.04, "horizon_years": 30},
    {"label": "100/0, 4%, 30yr", "stock_alloc": 1.0, "withdrawal_rate": 0.04, "horizon_years": 30},
    {"label": "60/40, 5%, 30yr", "stock_alloc": 0.6, "withdrawal_rate": 0.05, "horizon_years": 30},
]

N_PATHS = 50_000
SEED = 42


def run_comparison():
    monthly_returns = load_monthly_returns()
    rows = []
    for sc in SCENARIOS:
        kwargs = {k: v for k, v in sc.items() if k != "label"}
        hist = run_historical_simulation(monthly_returns, **kwargs)
        ln = run_monte_carlo_simulation(
            monthly_returns, n_paths=N_PATHS, mode="lognormal", seed=SEED, **kwargs
        )
        bb = run_monte_carlo_simulation(
            monthly_returns, n_paths=N_PATHS, mode="block_bootstrap", block_months=12, seed=SEED, **kwargs
        )
        rows.append(
            {
                "label": sc["label"],
                "n_windows": hist.n_windows,
                "success": {"historical": hist.success_rate, "lognormal": ln.success_rate, "block_bootstrap": bb.success_rate},
                "p5": {"historical": hist.percentile(5)[-1], "lognormal": ln.percentile(5)[-1], "block_bootstrap": bb.percentile(5)[-1]},
                "p50": {"historical": hist.percentile(50)[-1], "lognormal": ln.percentile(50)[-1], "block_bootstrap": bb.percentile(50)[-1]},
                "p95": {"historical": hist.percentile(95)[-1], "lognormal": ln.percentile(95)[-1], "block_bootstrap": bb.percentile(95)[-1]},
            }
        )
    return rows


def _print_table(rows, key, fmt):
    print(f"\n{key} (ending balance, multiple of starting balance)" if key != "success" else "\nSuccess rate")
    print(f"{'Scenario':<20} {'Historical':>12} {'Lognormal MC':>14} {'Block Bootstrap':>16}")
    for r in rows:
        v = r[key]
        print(
            f"{r['label']:<20} "
            f"{v['historical']:>12{fmt}} "
            f"{v['lognormal']:>14{fmt}} "
            f"{v['block_bootstrap']:>16{fmt}}"
        )


def main():
    rows = run_comparison()
    print(f"Historical engine: {rows[0]['n_windows']} rolling windows. Monte Carlo: {N_PATHS} paths, seed={SEED}.")
    _print_table(rows, "success", ".1%")
    _print_table(rows, "p5", ".2f")
    _print_table(rows, "p50", ".2f")
    _print_table(rows, "p95", ".2f")


if __name__ == "__main__":
    main()
