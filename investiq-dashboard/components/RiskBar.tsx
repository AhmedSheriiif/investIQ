import { riskScoreLabel } from "@/lib/risk";

export function RiskBar({
  score,
  labels,
}: {
  score: number;
  labels: {
    riskPosition: string;
    lowerRisk: string;
    moderateRisk: string;
    elevatedRisk: string;
    low: string;
    moderate: string;
    elevated: string;
  };
}) {
  const { tone } = riskScoreLabel(score);
  const toneLabel =
    tone === "green" ? labels.lowerRisk : tone === "amber" ? labels.elevatedRisk : labels.moderateRisk;

  const toneColor =
    tone === "green" ? "var(--signal-green)" : tone === "amber" ? "var(--signal-amber)" : "var(--muted)";

  return (
    <div className="w-full">
      <div className="flex items-baseline justify-between mb-2">
        <span className="text-xs uppercase tracking-widest text-muted">{labels.riskPosition}</span>
        <span className="font-mono text-xs uppercase tracking-wider" style={{ color: toneColor }}>
          {toneLabel}
        </span>
      </div>
      <div className="relative h-2 rounded-full overflow-hidden bg-panel-raised border border-hairline">
        <div
          className="absolute inset-y-0 left-0 rounded-full"
          style={{
            width: "100%",
            background:
              "linear-gradient(90deg, var(--signal-green) 0%, var(--muted-dim) 45%, var(--signal-amber) 100%)",
            opacity: 0.35,
          }}
        />
        <div
          className="absolute top-1/2 -translate-y-1/2 h-4 w-1 rounded-full"
          style={{
            insetInlineStart: `calc(${score}% - 2px)`,
            background: toneColor,
            boxShadow: `0 0 8px ${toneColor}`,
          }}
        />
      </div>
      <div className="flex justify-between mt-1.5 font-mono text-[10px] text-muted-dim tracking-wide">
        <span>{labels.low}</span>
        <span>{labels.moderate}</span>
        <span>{labels.elevated}</span>
      </div>
    </div>
  );
}
