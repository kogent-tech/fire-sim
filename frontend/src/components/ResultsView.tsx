import { isCapeMethodResponse, isCompareResponse, type SimulateResponse } from "../lib/types";
import CapeInfo from "./CapeInfo";
import FanChart from "./charts/FanChart";
import MethodComparisonChart from "./charts/MethodComparisonChart";
import SummaryStats from "./SummaryStats";

interface Props {
  result: SimulateResponse;
  onOpenInfo: (topic: string) => void;
}

export default function ResultsView({ result, onOpenInfo }: Props) {
  if (isCompareResponse(result)) {
    return (
      <div className="results-view">
        <CapeInfo cape={result.cape} onOpenInfo={onOpenInfo} />
        <MethodComparisonChart compare={result} />
      </div>
    );
  }

  if (isCapeMethodResponse(result)) {
    return (
      <div className="results-view">
        <CapeInfo cape={result.cape} onOpenInfo={onOpenInfo} />
        <SummaryStats result={result.simulation} onOpenInfo={onOpenInfo} />
        <FanChart bands={result.simulation.balance_percentiles} title="Portfolio balance over time" onOpenInfo={onOpenInfo} />
      </div>
    );
  }

  return (
    <div className="results-view">
      <SummaryStats result={result} onOpenInfo={onOpenInfo} />
      <FanChart bands={result.balance_percentiles} title="Portfolio balance over time" onOpenInfo={onOpenInfo} />
    </div>
  );
}
