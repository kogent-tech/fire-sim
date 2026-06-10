import pytest
from fastapi.testclient import TestClient

from fire_sim.api.main import app, create_app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_simulate_historical_default(client):
    r = client.post("/simulate", json={"method": "historical"})
    assert r.status_code == 200
    data = r.json()
    assert data["method"] == "historical"
    assert data["withdrawal_strategy"] == "fixed"
    assert data["n_paths"] == 1473
    assert 0.9 < data["success_rate"] < 1.0
    assert set(data["balance_percentiles"]["series"].keys()) == {"5", "25", "50", "75", "95"}
    assert len(data["balance_percentiles"]["months"]) == 30 * 12 + 1
    assert set(data["ending_balance_percentiles"].keys()) == {"5", "25", "50", "75", "95"}


@pytest.mark.parametrize("strategy", ["fixed", "guyton_klinger", "constant_percentage"])
def test_simulate_historical_withdrawal_strategies(client, strategy):
    r = client.post("/simulate", json={"method": "historical", "withdrawal_strategy": strategy})
    assert r.status_code == 200
    assert r.json()["withdrawal_strategy"] == strategy


def test_simulate_montecarlo(client):
    r = client.post("/simulate", json={"method": "montecarlo", "n_paths": 500, "seed": 1})
    assert r.status_code == 200
    data = r.json()
    assert data["method"] == "montecarlo"
    assert data["n_paths"] == 500


@pytest.mark.parametrize("mode", ["lognormal", "block_bootstrap"])
def test_simulate_montecarlo_modes(client, mode):
    r = client.post("/simulate", json={"method": "montecarlo", "n_paths": 200, "mc_mode": mode, "seed": 1})
    assert r.status_code == 200
    assert r.json()["n_paths"] == 200


def test_simulate_montecarlo_seed_reproducible(client):
    payload = {"method": "montecarlo", "n_paths": 200, "seed": 7}
    r1 = client.post("/simulate", json=payload)
    r2 = client.post("/simulate", json=payload)
    assert r1.json() == r2.json()


def test_simulate_cape(client):
    r = client.post("/simulate", json={"method": "cape"})
    assert r.status_code == 200
    data = r.json()
    assert data["cape"]["current_cape"] > 0
    assert 0 < data["cape"]["suggested_withdrawal_rate"] < 0.20
    assert data["cape"]["model"]["n"] > 1000
    assert data["simulation"]["method"] == "cape"


def test_simulate_cape_with_explicit_current_cape(client):
    r = client.post("/simulate", json={"method": "cape", "current_cape": 20.0})
    assert r.status_code == 200
    assert r.json()["cape"]["current_cape"] == 20.0


def test_simulate_compare(client):
    r = client.post("/simulate", json={"method": "compare", "n_paths": 200})
    assert r.status_code == 200
    data = r.json()
    assert set(data["results"].keys()) == {"historical", "montecarlo", "cape_adjusted"}
    assert "cape" in data


def test_simulate_invalid_method_strategy_combo(client):
    r = client.post("/simulate", json={"method": "montecarlo", "withdrawal_strategy": "guyton_klinger"})
    assert r.status_code == 422
    assert r.json()["error"]["type"] == "ValidationError"


def test_simulate_out_of_range_field(client):
    r = client.post("/simulate", json={"method": "historical", "stock_alloc": 1.5})
    assert r.status_code == 422
    assert r.json()["error"]["type"] == "ValidationError"


def test_simulate_invalid_guardrails(client):
    r = client.post("/simulate", json={"method": "historical", "upper_guardrail": 0.5, "lower_guardrail": 0.8})
    assert r.status_code == 422


def test_success_rate_curve(client):
    r = client.post(
        "/success-rate-curve",
        json={"method": "historical", "wr_min": 0.03, "wr_max": 0.05, "wr_step": 0.01},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["method"] == "historical"
    assert len(data["points"]) == 3
    rates = [p["withdrawal_rate"] for p in data["points"]]
    success = [p["success_rate"] for p in data["points"]]
    assert rates == sorted(rates)
    # Higher withdrawal rate -> lower (or equal) success rate.
    assert all(success[i] >= success[i + 1] for i in range(len(success) - 1))


def test_success_rate_curve_too_many_points(client):
    r = client.post(
        "/success-rate-curve",
        json={"method": "historical", "wr_min": 0.0, "wr_max": 0.20, "wr_step": 0.0001},
    )
    assert r.status_code == 422


def test_sequence_risk(client):
    r = client.post("/sequence-risk", json={"period_years": 10, "downsample_months": 60})
    assert r.status_code == 200
    data = r.json()
    assert len(data["paths"]) == 1473
    assert data["months"][0] == 0
    assert data["months"][-1] == 360
    for path in data["paths"][:5]:
        assert len(path["balances"]) == len(data["months"])
    sens = data["sensitivity"]
    assert abs(sens["early_return_corr_with_ending_balance"]) > abs(sens["late_return_corr_with_ending_balance"])


def test_sequence_risk_period_exceeds_horizon(client):
    r = client.post("/sequence-risk", json={"period_years": 25, "horizon_years": 20})
    assert r.status_code == 422


def test_openapi_docs_available(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert {"/health", "/simulate", "/success-rate-curve", "/sequence-risk"} <= set(paths.keys())

    r = client.get("/docs")
    assert r.status_code == 200


def test_rate_limiting():
    limited_app = create_app(rate_limit="2/minute")
    limited_client = TestClient(limited_app)

    assert limited_client.get("/health").status_code == 200
    assert limited_client.get("/health").status_code == 200

    r = limited_client.get("/health")
    assert r.status_code == 429
    assert r.json()["error"]["type"] == "RateLimitExceeded"
