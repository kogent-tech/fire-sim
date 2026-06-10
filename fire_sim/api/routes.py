"""API routes for the fire-sim simulation engine."""
from fastapi import APIRouter, Request

from fire_sim.api.adapters import run_sequence_risk, run_simulation, run_success_rate_curve
from fire_sim.api.schemas import (
    CapeMethodResponse,
    CompareResponse,
    ScenarioRequest,
    SequenceRiskRequest,
    SequenceRiskResponse,
    SimulationResponse,
    SuccessRateCurveRequest,
    SuccessRateCurveResponse,
)

router = APIRouter()


@router.get("/health", summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/simulate",
    summary="Run a retirement simulation",
    response_model=SimulationResponse | CapeMethodResponse | CompareResponse,
)
def simulate(request: Request, payload: ScenarioRequest):
    """Run a simulation for the given scenario.

    `method` selects the engine:
    - `historical`: rolling-window simulation over the Shiller dataset
      (Trinity Study / cFIREsim style). Supports `withdrawal_strategy`
      (`fixed`, `guyton_klinger`, `constant_percentage`).
    - `montecarlo`: vectorized Monte Carlo (`mc_mode` = `lognormal` or
      `block_bootstrap`).
    - `cape`: suggests a withdrawal rate from the current CAPE ratio (via a
      regression against historical SWRs) and runs a historical simulation
      at that rate.
    - `compare`: runs `historical`, `montecarlo`, and a CAPE-adjusted
      historical simulation side by side.
    """
    return run_simulation(payload)


@router.post(
    "/success-rate-curve",
    summary="Success rate vs. withdrawal rate curve",
    response_model=SuccessRateCurveResponse,
)
def success_rate_curve(request: Request, payload: SuccessRateCurveRequest):
    """Sweep withdrawal rates over `[wr_min, wr_max]` and return the success
    rate at each step, for plotting a success-rate-vs-withdrawal-rate curve."""
    return run_success_rate_curve(payload)


@router.post(
    "/sequence-risk",
    summary="Sequence-of-returns risk analysis",
    response_model=SequenceRiskResponse,
)
def sequence_risk(request: Request, payload: SequenceRiskRequest):
    """Per-window early/late period returns and balance paths, plus
    sensitivity statistics, for a "path colored by early-period
    performance" chart."""
    return run_sequence_risk(payload)
