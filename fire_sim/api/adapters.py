"""Translate API requests into engine calls, and engine results into API responses."""
import numpy as np
import pandas as pd

from fire_sim.api.cache import get_cape_model, get_latest_cape, get_monthly_returns
from fire_sim.api.schemas import (
    CapeMethodResponse,
    CapeModelInfo,
    CapeResponse,
    CompareResponse,
    PercentileBands,
    ScenarioRequest,
    SequenceRiskPath,
    SequenceRiskRequest,
    SequenceRiskResponse,
    SequenceRiskSensitivity,
    SimulationResponse,
    SuccessRateCurvePoint,
    SuccessRateCurveRequest,
    SuccessRateCurveResponse,
)
from fire_sim.engine.historical import run_historical_simulation
from fire_sim.engine.monte_carlo import run_monte_carlo_simulation
from fire_sim.engine.result import SimulationResult
from fire_sim.engine.sequence_risk import early_vs_late_sensitivity, run_sequence_risk_analysis
from fire_sim.engine.withdrawal_strategies import (
    run_constant_percentage_simulation,
    run_guyton_klinger_simulation,
)


def _fmt_pct(p: float) -> str:
    return f"{p:g}"


def _to_simulation_response(
    result: SimulationResult, *, method: str, withdrawal_strategy: str, percentiles: list[float]
) -> SimulationResponse:
    months = list(range(result.balances.shape[1]))
    series = {_fmt_pct(p): result.percentile(p).tolist() for p in percentiles}
    ending = result.ending_balances
    ending_pct = {_fmt_pct(p): float(np.percentile(ending, p)) for p in percentiles}

    return SimulationResponse(
        method=method,
        withdrawal_strategy=withdrawal_strategy,
        n_paths=result.n_paths,
        success_rate=result.success_rate,
        starting_balance=result.starting_balance,
        stock_alloc=result.stock_alloc,
        withdrawal_rate=result.withdrawal_rate,
        horizon_years=result.horizon_years,
        balance_percentiles=PercentileBands(months=months, series=series),
        ending_balance_percentiles=ending_pct,
    )


def _run_historical_result(
    monthly_returns: pd.DataFrame,
    *,
    stock_alloc: float,
    withdrawal_rate: float,
    horizon_years: int,
    starting_balance: float,
    withdrawal_strategy: str,
    upper_guardrail: float,
    lower_guardrail: float,
    adjustment_pct: float,
) -> SimulationResult:
    common = dict(
        monthly_returns=monthly_returns,
        stock_alloc=stock_alloc,
        horizon_years=horizon_years,
        starting_balance=starting_balance,
    )
    if withdrawal_strategy == "fixed":
        return run_historical_simulation(withdrawal_rate=withdrawal_rate, **common)
    if withdrawal_strategy == "guyton_klinger":
        return run_guyton_klinger_simulation(
            initial_withdrawal_rate=withdrawal_rate,
            upper_guardrail=upper_guardrail,
            lower_guardrail=lower_guardrail,
            adjustment_pct=adjustment_pct,
            **common,
        )
    if withdrawal_strategy == "constant_percentage":
        return run_constant_percentage_simulation(withdrawal_rate=withdrawal_rate, **common)
    raise ValueError(f"Unknown withdrawal_strategy {withdrawal_strategy!r}")


def _run_montecarlo_result(monthly_returns: pd.DataFrame, req: ScenarioRequest) -> SimulationResult:
    return run_monte_carlo_simulation(
        monthly_returns,
        stock_alloc=req.stock_alloc,
        withdrawal_rate=req.withdrawal_rate,
        horizon_years=req.horizon_years,
        starting_balance=req.starting_balance,
        mode=req.mc_mode,
        n_paths=req.n_paths,
        block_months=req.block_months,
        seed=req.seed,
    )


def _cape_response(monthly_returns: pd.DataFrame, req: ScenarioRequest) -> CapeResponse:
    model = get_cape_model(req.stock_alloc, req.horizon_years)
    current_cape = req.current_cape if req.current_cape is not None else get_latest_cape()
    suggested = model.predict(current_cape)
    return CapeResponse(
        current_cape=current_cape,
        suggested_withdrawal_rate=suggested,
        model=CapeModelInfo(slope=model.slope, intercept=model.intercept, r_squared=model.r_squared, n=model.n),
    )


def run_simulation(req: ScenarioRequest) -> SimulationResponse | CapeMethodResponse | CompareResponse:
    monthly_returns = get_monthly_returns()

    if req.method == "historical":
        result = _run_historical_result(
            monthly_returns,
            stock_alloc=req.stock_alloc,
            withdrawal_rate=req.withdrawal_rate,
            horizon_years=req.horizon_years,
            starting_balance=req.starting_balance,
            withdrawal_strategy=req.withdrawal_strategy,
            upper_guardrail=req.upper_guardrail,
            lower_guardrail=req.lower_guardrail,
            adjustment_pct=req.adjustment_pct,
        )
        return _to_simulation_response(
            result, method="historical", withdrawal_strategy=req.withdrawal_strategy, percentiles=req.percentiles
        )

    if req.method == "montecarlo":
        result = _run_montecarlo_result(monthly_returns, req)
        return _to_simulation_response(
            result, method="montecarlo", withdrawal_strategy="fixed", percentiles=req.percentiles
        )

    if req.method == "cape":
        cape = _cape_response(monthly_returns, req)
        result = run_historical_simulation(
            monthly_returns,
            stock_alloc=req.stock_alloc,
            withdrawal_rate=cape.suggested_withdrawal_rate,
            horizon_years=req.horizon_years,
            starting_balance=req.starting_balance,
        )
        simulation = _to_simulation_response(
            result, method="cape", withdrawal_strategy="fixed", percentiles=req.percentiles
        )
        return CapeMethodResponse(cape=cape, simulation=simulation)

    if req.method == "compare":
        cape = _cape_response(monthly_returns, req)

        historical = _run_historical_result(
            monthly_returns,
            stock_alloc=req.stock_alloc,
            withdrawal_rate=req.withdrawal_rate,
            horizon_years=req.horizon_years,
            starting_balance=req.starting_balance,
            withdrawal_strategy="fixed",
            upper_guardrail=req.upper_guardrail,
            lower_guardrail=req.lower_guardrail,
            adjustment_pct=req.adjustment_pct,
        )
        montecarlo = _run_montecarlo_result(monthly_returns, req)
        cape_adjusted = run_historical_simulation(
            monthly_returns,
            stock_alloc=req.stock_alloc,
            withdrawal_rate=cape.suggested_withdrawal_rate,
            horizon_years=req.horizon_years,
            starting_balance=req.starting_balance,
        )

        results = {
            "historical": _to_simulation_response(
                historical, method="historical", withdrawal_strategy="fixed", percentiles=req.percentiles
            ),
            "montecarlo": _to_simulation_response(
                montecarlo, method="montecarlo", withdrawal_strategy="fixed", percentiles=req.percentiles
            ),
            "cape_adjusted": _to_simulation_response(
                cape_adjusted, method="cape_adjusted", withdrawal_strategy="fixed", percentiles=req.percentiles
            ),
        }
        return CompareResponse(results=results, cape=cape)

    raise ValueError(f"Unknown method {req.method!r}")


def run_success_rate_curve(req: SuccessRateCurveRequest) -> SuccessRateCurveResponse:
    monthly_returns = get_monthly_returns()

    rates = np.arange(req.wr_min, req.wr_max + req.wr_step / 2.0, req.wr_step)
    points = []
    for rate in rates:
        rate = float(rate)
        if req.method == "historical":
            result = run_historical_simulation(
                monthly_returns,
                stock_alloc=req.stock_alloc,
                withdrawal_rate=rate,
                horizon_years=req.horizon_years,
                starting_balance=req.starting_balance,
            )
        else:
            result = run_monte_carlo_simulation(
                monthly_returns,
                stock_alloc=req.stock_alloc,
                withdrawal_rate=rate,
                horizon_years=req.horizon_years,
                starting_balance=req.starting_balance,
                mode=req.mc_mode,
                n_paths=req.n_paths,
                block_months=req.block_months,
                seed=req.seed,
            )
        points.append(SuccessRateCurvePoint(withdrawal_rate=rate, success_rate=result.success_rate))

    return SuccessRateCurveResponse(
        method=req.method, stock_alloc=req.stock_alloc, horizon_years=req.horizon_years, points=points
    )


def run_sequence_risk(req: SequenceRiskRequest) -> SequenceRiskResponse:
    monthly_returns = get_monthly_returns()

    result = run_sequence_risk_analysis(
        monthly_returns,
        stock_alloc=req.stock_alloc,
        withdrawal_rate=req.withdrawal_rate,
        horizon_years=req.horizon_years,
        starting_balance=req.starting_balance,
        period_years=req.period_years,
    )
    sensitivity = early_vs_late_sensitivity(result)

    months = list(range(0, result.balances.shape[1], req.downsample_months))
    if months[-1] != result.balances.shape[1] - 1:
        months.append(result.balances.shape[1] - 1)

    paths = [
        SequenceRiskPath(
            start_date=result.start_dates[i].date().isoformat(),
            early_return=float(result.early_return[i]),
            late_return=float(result.late_return[i]),
            success=not bool(result.depleted[i]),
            ending_balance=float(result.ending_balances[i]),
            balances=result.balances[i, months].tolist(),
        )
        for i in range(result.n_windows)
    ]

    return SequenceRiskResponse(
        stock_alloc=result.stock_alloc,
        withdrawal_rate=result.withdrawal_rate,
        horizon_years=result.horizon_years,
        period_years=result.period_years,
        months=months,
        success_rate=result.success_rate,
        sensitivity=SequenceRiskSensitivity(**sensitivity),
        paths=paths,
    )
