"use client";

import { useState } from "react";

export interface HoldingInput {
  ticker: string;
  weight: string; // kept as string while editing, parsed to number on submit
}

export function PortfolioBuilder({
  onSubmit,
  loading,
  labels,
  initialHoldings,
}: {
  onSubmit: (holdings: { ticker: string; weight: number }[]) => void;
  loading: boolean;
  labels: {
    holdings: string;
    ticker: string;
    weight: string;
    addHolding: string;
    remove: string;
    totalWeight: string;
    weightsMustSumTo100: string;
    analyzePortfolio: string;
    analyzing: string;
  };
  initialHoldings?: { ticker: string; weight: number }[];
}) {
  const [rows, setRows] = useState<HoldingInput[]>(
    initialHoldings && initialHoldings.length >= 2
      ? initialHoldings.map((h) => ({ ticker: h.ticker, weight: String(h.weight * 100) }))
      : [
          { ticker: "", weight: "" },
          { ticker: "", weight: "" },
        ]
  );

  const totalWeight = rows.reduce((sum, r) => sum + (parseFloat(r.weight) || 0), 0);
  const weightIsValid = Math.abs(totalWeight - 100) < 0.5;
  const tickersAreValid = rows.every((r) => r.ticker.trim().length > 0) && rows.length >= 2;
  const canSubmit = weightIsValid && tickersAreValid && !loading;

  function updateRow(index: number, field: keyof HoldingInput, value: string) {
    setRows((prev) => prev.map((r, i) => (i === index ? { ...r, [field]: value } : r)));
  }

  function addRow() {
    setRows((prev) => [...prev, { ticker: "", weight: "" }]);
  }

  function removeRow(index: number) {
    setRows((prev) => prev.filter((_, i) => i !== index));
  }

  function handleSubmit() {
    if (!canSubmit) return;
    const holdings = rows.map((r) => ({
      ticker: r.ticker.trim().toUpperCase(),
      weight: parseFloat(r.weight) / 100,
    }));
    onSubmit(holdings);
  }

  return (
    <div className="bg-panel border border-hairline rounded-lg p-5">
      <div className="text-xs uppercase tracking-widest text-muted mb-3">{labels.holdings}</div>

      <div className="space-y-2 mb-3">
        {rows.map((row, i) => (
          <div key={i} className="flex gap-2 items-center">
            <input
              type="text"
              value={row.ticker}
              onChange={(e) => updateRow(i, "ticker", e.target.value)}
              placeholder={labels.ticker}
              className="flex-1 bg-panel-raised border border-hairline rounded-md px-3 py-2 text-sm font-mono
                         text-ink placeholder:text-muted-dim outline-none
                         focus:border-signal-amber/60 focus:ring-1 focus:ring-signal-amber/30 transition-colors"
              disabled={loading}
            />
            <input
              type="number"
              value={row.weight}
              onChange={(e) => updateRow(i, "weight", e.target.value)}
              placeholder={labels.weight}
              className="w-28 bg-panel-raised border border-hairline rounded-md px-3 py-2 text-sm font-mono
                         text-ink placeholder:text-muted-dim outline-none
                         focus:border-signal-amber/60 focus:ring-1 focus:ring-signal-amber/30 transition-colors"
              disabled={loading}
            />
            <button
              onClick={() => removeRow(i)}
              disabled={rows.length <= 2 || loading}
              className="px-2.5 py-2 rounded-md border border-hairline text-muted-dim hover:text-signal-amber
                         hover:border-signal-amber/50 disabled:opacity-30 disabled:hover:text-muted-dim
                         disabled:hover:border-hairline transition-colors text-sm"
              aria-label={labels.remove}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between mb-4">
        <button
          onClick={addRow}
          disabled={loading}
          className="text-xs font-mono text-muted hover:text-signal-amber transition-colors"
        >
          + {labels.addHolding}
        </button>
        <div className="text-xs font-mono">
          <span className="text-muted">{labels.totalWeight}: </span>
          <span className={weightIsValid ? "text-signal-green" : "text-signal-amber"}>
            {totalWeight.toFixed(1)}%
          </span>
        </div>
      </div>

      {!weightIsValid && totalWeight > 0 && (
        <div className="text-xs text-signal-amber mb-3">{labels.weightsMustSumTo100}</div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className="w-full px-5 py-2.5 rounded-md bg-panel-raised border border-hairline text-sm font-medium
                   text-ink hover:border-signal-amber/50 hover:text-signal-amber
                   disabled:opacity-40 disabled:hover:border-hairline disabled:hover:text-ink
                   transition-colors"
      >
        {loading ? labels.analyzing : labels.analyzePortfolio}
      </button>
    </div>
  );
}
