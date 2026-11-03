"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";
import { ScenarioResult } from "@/lib/api";

const SCENARIO_ORDER = ["market_crash", "correction", "rate_hike_shock", "custom", "historical_worst_day", "rally"];

export function ScenarioChart({
  scenarios,
  labels,
}: {
  scenarios: Record<string, ScenarioResult>;
  labels: Record<string, string>;
}) {
  const data = SCENARIO_ORDER
    .filter((key) => key in scenarios)
    .map((key) => ({
      key,
      name: labels[key] || key,
      impact: scenarios[key].portfolio_impact * 100,
    }));

  return (
    <div className="bg-panel border border-hairline rounded-lg p-5">
      <div className="text-xs uppercase tracking-widest text-muted mb-4">{labels.heading}</div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
          <XAxis
            dataKey="name"
            tick={{ fill: "var(--muted)", fontSize: 11, fontFamily: "var(--font-mono)" }}
            axisLine={{ stroke: "var(--hairline)" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "var(--muted)", fontSize: 11, fontFamily: "var(--font-mono)" }}
            axisLine={{ stroke: "var(--hairline)" }}
            tickLine={false}
            tickFormatter={(v) => `${v}%`}
          />
          <ReferenceLine y={0} stroke="var(--hairline)" />
          <Tooltip
            contentStyle={{
              background: "var(--panel-raised)",
              border: "1px solid var(--hairline)",
              borderRadius: 8,
              fontSize: 12,
              fontFamily: "var(--font-mono)",
            }}
            labelStyle={{ color: "var(--ink)" }}
            formatter={(value) => {
              const num = Array.isArray(value) ? Number(value[0]) : Number(value);
              return [`${(isNaN(num) ? 0 : num).toFixed(2)}%`, "Portfolio impact"];
            }}
          />
          <Bar dataKey="impact" radius={[4, 4, 4, 4]}>
            {data.map((entry) => (
              <Cell
                key={entry.key}
                fill={entry.impact < 0 ? "var(--signal-amber)" : "var(--signal-green)"}
                fillOpacity={0.75}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
