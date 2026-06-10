import { DEFAULT_SCENARIO, type ScenarioRequest } from "../lib/types";
import { PRESETS } from "../lib/presets";

interface Props {
  onSelect: (scenario: ScenarioRequest) => void;
}

export default function PresetBar({ onSelect }: Props) {
  const apply = (preset: (typeof PRESETS)[number]) => {
    onSelect({
      ...DEFAULT_SCENARIO,
      percentiles: [...DEFAULT_SCENARIO.percentiles],
      ...preset.scenario,
    });
  };

  return (
    <div className="preset-bar">
      <span className="preset-label">Try a preset:</span>
      {PRESETS.map((preset) => (
        <button
          key={preset.id}
          type="button"
          className="preset-button"
          title={preset.description}
          onClick={() => apply(preset)}
        >
          {preset.label}
        </button>
      ))}
    </div>
  );
}
