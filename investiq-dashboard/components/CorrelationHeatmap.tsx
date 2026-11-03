function correlationColor(value: number, isDiagonal: boolean): string {
  if (isDiagonal) return "var(--panel-raised)";
  // Diverging scale: -1 -> teal (good diversification), 0 -> neutral, +1 -> amber (poor diversification)
  const clamped = Math.max(-1, Math.min(1, value));
  if (clamped >= 0) {
    // 0 -> transparent, 1 -> full amber
    const alpha = clamped * 0.55;
    return `rgba(232, 163, 61, ${alpha})`;
  } else {
    const alpha = Math.abs(clamped) * 0.55;
    return `rgba(79, 169, 128, ${alpha})`;
  }
}

function correlationTextColor(value: number, isDiagonal: boolean): string {
  if (isDiagonal) return "var(--muted-dim)";
  return Math.abs(value) > 0.5 ? "var(--ink)" : "var(--muted)";
}

export function CorrelationHeatmap({
  tickers,
  matrix,
  heading,
}: {
  tickers: string[];
  matrix: Record<string, Record<string, number>>;
  heading: string;
}) {
  return (
    <div className="bg-panel border border-hairline rounded-lg p-5">
      <div className="text-xs uppercase tracking-widest text-muted mb-4">{heading}</div>

      <div className="overflow-x-auto">
        <table className="border-collapse w-full">
          <thead>
            <tr>
              <th className="w-16"></th>
              {tickers.map((t) => (
                <th key={t} className="font-mono text-[11px] text-muted-dim font-normal pb-2 px-1">
                  {t}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tickers.map((rowTicker) => (
              <tr key={rowTicker}>
                <td className="font-mono text-[11px] text-muted-dim pr-2 text-right whitespace-nowrap">
                  {rowTicker}
                </td>
                {tickers.map((colTicker) => {
                  const value = matrix[rowTicker]?.[colTicker] ?? 0;
                  const isDiagonal = rowTicker === colTicker;
                  return (
                    <td key={colTicker} className="p-1">
                      <div
                        className="w-14 h-14 rounded-md flex items-center justify-center border border-hairline"
                        style={{ backgroundColor: correlationColor(value, isDiagonal) }}
                      >
                        <span
                          className="font-mono text-xs"
                          style={{ color: correlationTextColor(value, isDiagonal) }}
                        >
                          {value.toFixed(2)}
                        </span>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-4 mt-4 text-[11px] font-mono text-muted-dim">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: "rgba(79, 169, 128, 0.55)" }} />
          <span>Low / negative correlation</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: "rgba(232, 163, 61, 0.55)" }} />
          <span>High correlation</span>
        </div>
      </div>
    </div>
  );
}
