import { RiskMetrics } from "./api";

const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: "$",
  EGP: "E£",
  EUR: "€",
  GBP: "£",
};

export function formatPrice(price: number, currency: string): string {
  const symbol = CURRENCY_SYMBOLS[currency] || `${currency} `;
  return `${symbol}${price.toFixed(2)}`;
}

/**
 * Maps annualized volatility to a 0-100 risk score using rough real-world
 * bands: <15% vol is low-risk (defensive blue chips, utilities), 15-25% is
 * moderate (broad market / large-cap tech), 25-40% is elevated (growth
 * stocks), 40%+ is high (speculative/small-cap). This is a simplification
 * for visual positioning, not a formal risk model - it exists to give an
 * at-a-glance read, not a precise score.
 */
export function volatilityToRiskScore(annualizedVolatility: number): number {
  const volPct = annualizedVolatility * 100;
  const clamped = Math.max(5, Math.min(60, volPct));
  return Math.round(((clamped - 5) / (60 - 5)) * 100);
}

export function riskScoreLabel(score: number): { label: string; tone: "green" | "amber" | "neutral" } {
  if (score < 30) return { label: "Lower risk", tone: "green" };
  if (score < 60) return { label: "Moderate risk", tone: "neutral" };
  return { label: "Elevated risk", tone: "amber" };
}

export function formatPercent(value: number, decimals = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatSignedPercent(value: number, decimals = 2): string {
  const pct = value * 100;
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(decimals)}%`;
}

export function toneForReturn(value: number): "green" | "amber" | "neutral" {
  if (value > 0.05) return "green";
  if (value < -0.05) return "amber";
  return "neutral";
}

export function toneForSharpe(value: number): "green" | "amber" | "neutral" {
  if (value >= 1) return "green";
  if (value < 0) return "amber";
  return "neutral";
}

export function computeRiskScore(metrics: RiskMetrics): number {
  return volatilityToRiskScore(metrics.annualized_volatility);
}
