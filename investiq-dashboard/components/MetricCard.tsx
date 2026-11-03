type Tone = "green" | "amber" | "neutral";

const toneClasses: Record<Tone, string> = {
  green: "text-signal-green",
  amber: "text-signal-amber",
  neutral: "text-ink",
};

export function MetricCard({
  label,
  value,
  detail,
  tone = "neutral",
}: {
  label: string;
  value: string;
  detail?: string;
  tone?: Tone;
}) {
  return (
    <div className="bg-panel border border-hairline rounded-lg px-4 py-3.5 flex flex-col gap-1">
      <span className="text-[11px] uppercase tracking-widest text-muted">{label}</span>
      <span className={`font-mono text-2xl font-medium leading-none ${toneClasses[tone]}`}>
        {value}
      </span>
      {detail && <span className="text-xs text-muted-dim mt-0.5">{detail}</span>}
    </div>
  );
}
