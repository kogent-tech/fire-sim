import { useEffect, useState } from "react";
import { ApiRequestError, sequenceRisk, simulate, successRateCurve } from "../lib/api";
import { DEFAULT_SCENARIO } from "../lib/types";
import { paramsToScenario, scenarioToParams } from "../lib/url";
import type {
  ScenarioRequest,
  SequenceRiskResponse,
  SimulateResponse,
  SuccessRateCurveResponse,
} from "../lib/types";
import ScenarioForm from "./ScenarioForm";
import ResultsView from "./ResultsView";
import SuccessRateCurveChart from "./charts/SuccessRateCurveChart";
import SequenceRiskChart from "./charts/SequenceRiskChart";

type Tab = "overview" | "success-rate" | "sequence-risk";

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Forecast" },
  { id: "success-rate", label: "Success Rate Curve" },
  { id: "sequence-risk", label: "Sequence Risk" },
];

function defaultScenario(): ScenarioRequest {
  return { ...DEFAULT_SCENARIO, percentiles: [...DEFAULT_SCENARIO.percentiles] };
}

export default function App() {
  // Always start from the same defaults the server rendered, to avoid a
  // hydration mismatch. The actual URL is read in an effect after mount.
  const [scenario, setScenario] = useState<ScenarioRequest>(defaultScenario);
  const [submitted, setSubmitted] = useState<ScenarioRequest>(scenario);
  const [submitCount, setSubmitCount] = useState(0);
  const [ready, setReady] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  const [simResult, setSimResult] = useState<SimulateResponse | null>(null);
  const [simError, setSimError] = useState<string | null>(null);
  const [simLoading, setSimLoading] = useState(false);

  const [curveResult, setCurveResult] = useState<SuccessRateCurveResponse | null>(null);
  const [curveError, setCurveError] = useState<string | null>(null);
  const [curveLoading, setCurveLoading] = useState(false);
  const [curveFetchedAt, setCurveFetchedAt] = useState(-1);

  const [seqResult, setSeqResult] = useState<SequenceRiskResponse | null>(null);
  const [seqError, setSeqError] = useState<string | null>(null);
  const [seqLoading, setSeqLoading] = useState(false);
  const [seqFetchedAt, setSeqFetchedAt] = useState(-1);

  // Read the scenario from the URL once the component has mounted (avoids an
  // SSR/client hydration mismatch from reading window.location during render).
  useEffect(() => {
    const fromUrl = paramsToScenario(new URLSearchParams(window.location.search));
    setScenario(fromUrl);
    setSubmitted(fromUrl);
    setReady(true);
  }, []);

  // Update the URL whenever a scenario is submitted, so it's shareable.
  useEffect(() => {
    if (!ready) return;
    const params = scenarioToParams(submitted);
    const qs = params.toString();
    const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    window.history.replaceState(null, "", url);
  }, [submitted, ready]);

  // Run the main simulation whenever a new scenario is submitted.
  useEffect(() => {
    if (!ready) return;
    let cancelled = false;
    setSimLoading(true);
    setSimError(null);
    simulate(submitted)
      .then((res) => {
        if (cancelled) return;
        setSimResult(res);
      })
      .catch((err) => {
        if (cancelled) return;
        setSimResult(null);
        setSimError(err instanceof ApiRequestError ? err.message : "Something went wrong running the simulation.");
      })
      .finally(() => {
        if (!cancelled) setSimLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, submitCount]);

  // Lazily fetch the success-rate curve when that tab is opened (or scenario changes).
  useEffect(() => {
    if (!ready || activeTab !== "success-rate" || curveFetchedAt === submitCount) return;
    let cancelled = false;
    setCurveLoading(true);
    setCurveError(null);
    successRateCurve({
      method: submitted.method === "montecarlo" ? "montecarlo" : "historical",
      stock_alloc: submitted.stock_alloc,
      horizon_years: submitted.horizon_years,
      starting_balance: submitted.starting_balance,
      wr_min: 0.02,
      wr_max: 0.06,
      wr_step: 0.0025,
      mc_mode: submitted.mc_mode,
      n_paths: submitted.n_paths,
      block_months: submitted.block_months,
      seed: submitted.seed,
    })
      .then((res) => {
        if (cancelled) return;
        setCurveResult(res);
        setCurveFetchedAt(submitCount);
      })
      .catch((err) => {
        if (cancelled) return;
        setCurveError(
          err instanceof ApiRequestError ? err.message : "Something went wrong computing the success-rate curve."
        );
      })
      .finally(() => {
        if (!cancelled) setCurveLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, activeTab, submitCount]);

  // Lazily fetch sequence-risk data when that tab is opened (or scenario changes).
  useEffect(() => {
    if (!ready || activeTab !== "sequence-risk" || seqFetchedAt === submitCount) return;
    let cancelled = false;
    setSeqLoading(true);
    setSeqError(null);
    const periodYears = Math.min(10, submitted.horizon_years);
    const downsampleMonths = Math.min(60, Math.max(1, Math.round((submitted.horizon_years * 12) / 30)));
    sequenceRisk({
      stock_alloc: submitted.stock_alloc,
      withdrawal_rate: submitted.withdrawal_rate,
      horizon_years: submitted.horizon_years,
      starting_balance: submitted.starting_balance,
      period_years: periodYears,
      downsample_months: downsampleMonths,
    })
      .then((res) => {
        if (cancelled) return;
        setSeqResult(res);
        setSeqFetchedAt(submitCount);
      })
      .catch((err) => {
        if (cancelled) return;
        setSeqError(
          err instanceof ApiRequestError ? err.message : "Something went wrong computing sequence-risk data."
        );
      })
      .finally(() => {
        if (!cancelled) setSeqLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, activeTab, submitCount]);

  const handleSubmit = () => {
    setSubmitted(scenario);
    setSubmitCount((c) => c + 1);
  };

  return (
    <div className="app">
      <ScenarioForm scenario={scenario} onChange={setScenario} onSubmit={handleSubmit} loading={simLoading} />

      <div className="tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`tab ${activeTab === tab.id ? "tab-active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="tab-panel">
        {activeTab === "overview" && (
          <>
            {simLoading && <p className="status status-loading">Running simulation...</p>}
            {simError && <p className="status status-error">{simError}</p>}
            {!simLoading && !simError && simResult && <ResultsView result={simResult} />}
          </>
        )}

        {activeTab === "success-rate" && (
          <>
            {curveLoading && <p className="status status-loading">Computing success-rate curve...</p>}
            {curveError && <p className="status status-error">{curveError}</p>}
            {!curveLoading && !curveError && curveResult && (
              <SuccessRateCurveChart curve={curveResult} currentWithdrawalRate={submitted.withdrawal_rate} />
            )}
          </>
        )}

        {activeTab === "sequence-risk" && (
          <>
            {seqLoading && <p className="status status-loading">Computing sequence-risk data...</p>}
            {seqError && <p className="status status-error">{seqError}</p>}
            {!seqLoading && !seqError && seqResult && <SequenceRiskChart result={seqResult} />}
          </>
        )}
      </div>
    </div>
  );
}
