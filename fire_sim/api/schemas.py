"""Pydantic request/response schemas for the fire-sim API."""
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Method = Literal["historical", "montecarlo", "cape", "compare"]
WithdrawalStrategy = Literal["fixed", "guyton_klinger", "constant_percentage"]
MonteCarloMode = Literal["lognormal", "block_bootstrap"]

DEFAULT_PERCENTILES = (5.0, 25.0, 50.0, 75.0, 95.0)


class ScenarioRequest(BaseModel):
    """A retirement scenario: portfolio, withdrawal plan, and simulation method."""

    method: Method = "historical"
    starting_balance: float = Field(1.0, gt=0, description="Starting portfolio balance (any currency unit).")
    stock_alloc: float = Field(0.6, ge=0, le=1, description="Fraction of the portfolio in stocks; the rest is bonds.")
    withdrawal_rate: float = Field(
        0.04, ge=0, le=0.20, description="Initial annual withdrawal rate, as a fraction of starting_balance."
    )
    horizon_years: int = Field(30, ge=1, le=60, description="Retirement horizon in years.")
    withdrawal_strategy: WithdrawalStrategy = Field(
        "fixed", description="'fixed' (4%-rule style), 'guyton_klinger' guardrails, or 'constant_percentage'."
    )
    percentiles: list[float] = Field(
        default_factory=lambda: list(DEFAULT_PERCENTILES),
        description="Percentile bands (0-100) to return for the balance-over-time series.",
    )

    # Monte Carlo
    mc_mode: MonteCarloMode = Field("lognormal", description="Monte Carlo return-generation mode.")
    n_paths: int = Field(2000, ge=100, le=20000, description="Number of Monte Carlo paths.")
    block_months: int = Field(12, ge=1, le=600, description="Block length (months) for block_bootstrap mode.")
    seed: int | None = Field(42, description="Random seed for Monte Carlo. Use null for non-reproducible draws.")

    # CAPE
    current_cape: float | None = Field(
        None, gt=0, description="Current CAPE ratio. Defaults to the latest value in the bundled dataset."
    )

    # Guyton-Klinger guardrails
    upper_guardrail: float = Field(1.20, gt=1.0, description="Capital-preservation guardrail multiplier.")
    lower_guardrail: float = Field(0.0, ge=0.0, lt=1.0, description="Prosperity guardrail multiplier.")
    adjustment_pct: float = Field(0.10, ge=0, le=1, description="Withdrawal adjustment when a guardrail is breached.")

    @model_validator(mode="after")
    def _validate(self) -> "ScenarioRequest":
        if not all(0 <= p <= 100 for p in self.percentiles):
            raise ValueError("percentiles must each be between 0 and 100")
        if self.lower_guardrail >= self.upper_guardrail:
            raise ValueError("lower_guardrail must be less than upper_guardrail")
        if self.method != "historical" and self.withdrawal_strategy != "fixed":
            raise ValueError(f"method={self.method!r} only supports withdrawal_strategy='fixed'")
        if self.block_months > self.horizon_years * 12:
            raise ValueError("block_months cannot exceed horizon_years * 12")
        return self


class PercentileBands(BaseModel):
    months: list[int]
    series: dict[str, list[float]]


class SimulationResponse(BaseModel):
    method: str
    withdrawal_strategy: str
    n_paths: int
    success_rate: float
    starting_balance: float
    stock_alloc: float
    withdrawal_rate: float
    horizon_years: int
    balance_percentiles: PercentileBands
    ending_balance_percentiles: dict[str, float]


class CapeModelInfo(BaseModel):
    slope: float
    intercept: float
    r_squared: float
    n: int


class CapeResponse(BaseModel):
    current_cape: float
    suggested_withdrawal_rate: float
    model: CapeModelInfo


class CapeMethodResponse(BaseModel):
    cape: CapeResponse
    simulation: SimulationResponse


class CompareResponse(BaseModel):
    results: dict[str, SimulationResponse]
    cape: CapeResponse


class SuccessRateCurvePoint(BaseModel):
    withdrawal_rate: float
    success_rate: float


class SuccessRateCurveRequest(BaseModel):
    method: Literal["historical", "montecarlo"] = "historical"
    stock_alloc: float = Field(0.6, ge=0, le=1)
    horizon_years: int = Field(30, ge=1, le=60)
    starting_balance: float = Field(1.0, gt=0)
    wr_min: float = Field(0.02, ge=0, le=0.20)
    wr_max: float = Field(0.06, ge=0, le=0.20)
    wr_step: float = Field(0.0025, gt=0, le=0.02)
    mc_mode: MonteCarloMode = "lognormal"
    n_paths: int = Field(2000, ge=100, le=20000)
    block_months: int = Field(12, ge=1, le=600)
    seed: int | None = 42

    @model_validator(mode="after")
    def _validate(self) -> "SuccessRateCurveRequest":
        if self.wr_max <= self.wr_min:
            raise ValueError("wr_max must be greater than wr_min")
        n_points = (self.wr_max - self.wr_min) / self.wr_step
        if n_points > 200:
            raise ValueError("too many points requested - narrow the range or increase wr_step")
        if self.block_months > self.horizon_years * 12:
            raise ValueError("block_months cannot exceed horizon_years * 12")
        return self


class SuccessRateCurveResponse(BaseModel):
    method: str
    stock_alloc: float
    horizon_years: int
    points: list[SuccessRateCurvePoint]


class SequenceRiskRequest(BaseModel):
    stock_alloc: float = Field(0.6, ge=0, le=1)
    withdrawal_rate: float = Field(0.04, ge=0, le=0.20)
    horizon_years: int = Field(30, ge=1, le=60)
    starting_balance: float = Field(1.0, gt=0)
    period_years: int = Field(10, ge=1, le=30)
    downsample_months: int = Field(12, ge=1, le=60)

    @model_validator(mode="after")
    def _validate(self) -> "SequenceRiskRequest":
        if self.period_years > self.horizon_years:
            raise ValueError("period_years cannot exceed horizon_years")
        return self


class SequenceRiskSensitivity(BaseModel):
    early_return_corr_with_ending_balance: float
    late_return_corr_with_ending_balance: float
    early_return_mean_success: float
    late_return_mean_success: float
    early_return_mean_failure: float | None
    late_return_mean_failure: float | None


class SequenceRiskPath(BaseModel):
    start_date: str
    early_return: float
    late_return: float
    success: bool
    ending_balance: float
    balances: list[float]


class SequenceRiskResponse(BaseModel):
    stock_alloc: float
    withdrawal_rate: float
    horizon_years: int
    period_years: int
    months: list[int]
    success_rate: float
    sensitivity: SequenceRiskSensitivity
    paths: list[SequenceRiskPath]
