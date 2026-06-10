import { isCapeMethodResponse, isCompareResponse, type SimulateResponse } from "../lib/types";
import CapeInfo from "./CapeInfo";
import FanChart from "./charts/FanChart";
import MethodComparisonChart from "./charts/MethodComparisonChart";
import SummaryStats from "./SummaryStats";

export default function ResultsView({ result }: { result: SimulateResponse }) {
  if (isCompareResponse(result)) {
    return (
      <div className="results-view">
        <CapeInfo cape={result.cape} />
        <MethodComparisonChart compare={result} />
      </div>
    );
  }

  if (isCapeMethodResponse(result)) {
    return (
      <div className="results-view">
        <CapeInfo cape={result.cape} />
        <SummaryStats result={result.simulation} />
        <FanChart bands={result.simulation.balance_percentiles} title="Portfolio balance over time" />
      </div>
    );
  }

  return (
    <div className="results-view">
      <SummaryStats result={result} />
      <FanChart bands={result.balance_percentiles} title="Portfolio balance over time" />
    </div>
  );
}
