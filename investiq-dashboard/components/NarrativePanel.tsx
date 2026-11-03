export function NarrativePanel({
  narrative,
  provider,
  heading,
}: {
  narrative: string;
  provider: string;
  heading: string;
}) {
  const paragraphs = narrative.split(/\n\s*\n/).filter(Boolean);

  return (
    <div className="bg-panel border border-hairline rounded-lg p-6">
      <div className="flex items-center justify-between mb-4 pb-4 border-b border-hairline">
        <h2 className="text-sm uppercase tracking-widest text-muted">{heading}</h2>
        <span className="font-mono text-[10px] text-muted-dim uppercase tracking-wider">
          {provider}
        </span>
      </div>
      <div className="space-y-4">
        {paragraphs.map((p, i) => (
          <p key={i} className="text-[15px] leading-relaxed text-ink/90">
            {p}
          </p>
        ))}
      </div>
    </div>
  );
}
