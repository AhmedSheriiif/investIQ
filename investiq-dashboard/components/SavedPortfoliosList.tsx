"use client";

import { SavedPortfolio } from "@/lib/api";

export function SavedPortfoliosList({
  portfolios,
  onLoad,
  onDelete,
  labels,
}: {
  portfolios: SavedPortfolio[];
  onLoad: (portfolio: SavedPortfolio) => void;
  onDelete: (id: number) => void;
  labels: { heading: string; load: string; delete: string; empty: string };
}) {
  if (portfolios.length === 0) {
    return (
      <div className="bg-panel border border-hairline rounded-lg p-5">
        <div className="text-xs uppercase tracking-widest text-muted mb-2">{labels.heading}</div>
        <p className="text-sm text-muted-dim">{labels.empty}</p>
      </div>
    );
  }

  return (
    <div className="bg-panel border border-hairline rounded-lg p-5">
      <div className="text-xs uppercase tracking-widest text-muted mb-3">{labels.heading}</div>
      <div className="space-y-2">
        {portfolios.map((p) => (
          <div
            key={p.id}
            className="flex items-center justify-between px-3 py-2.5 rounded-md bg-panel-raised border border-hairline"
          >
            <div>
              <div className="text-sm font-medium text-ink">{p.name}</div>
              <div className="text-xs font-mono text-muted-dim">
                {p.holdings.map((h) => `${h.ticker} ${(h.weight * 100).toFixed(0)}%`).join(" · ")}
              </div>
            </div>
            <div className="flex gap-2 text-xs font-mono">
              <button
                onClick={() => onLoad(p)}
                className="text-muted hover:text-signal-amber transition-colors"
              >
                {labels.load}
              </button>
              <button
                onClick={() => onDelete(p.id)}
                className="text-muted-dim hover:text-signal-amber transition-colors"
              >
                {labels.delete}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
