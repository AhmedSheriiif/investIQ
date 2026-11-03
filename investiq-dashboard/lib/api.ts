const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface RiskMetrics {
  current_price: number;
  currency: string;
  annualized_return: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  var_95: number;
  var_99: number;
  cvar_95: number;
  beta: number | null;
  period_start: string;
  period_end: string;
  trading_days: number;
}

export interface ReportResponse {
  ticker: string;
  resolved_ticker: string;
  benchmark: string;
  metrics: RiskMetrics;
  narrative: string;
  llm_provider: string;
  language: string;
}

export interface PortfolioMetrics {
  annualized_return: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  var_95: number;
  var_99: number;
  cvar_95: number;
  diversification_benefit: number;
  individual_volatilities: Record<string, number>;
  correlation_matrix: Record<string, Record<string, number>>;
  period_start: string;
  period_end: string;
  trading_days: number;
}

export interface PortfolioReportResponse {
  tickers: string[];
  weights: Record<string, number>;
  metrics: PortfolioMetrics;
  narrative: string;
  llm_provider: string;
  language: string;
}

export interface ScenarioResult {
  scenario_type: string;
  shock_pct?: number;
  asset_shocks?: Record<string, number>;
  asset_worst_days?: Record<string, number>;
  asset_worst_day_dates?: Record<string, string>;
  portfolio_impact: number;
}

export interface StressTestResponse {
  tickers: string[];
  weights: Record<string, number>;
  scenarios: Record<string, ScenarioResult>;
}

export async function fetchStressTest(
  holdings: { ticker: string; weight: number }[],
  customShockPct?: number
): Promise<StressTestResponse> {
  const res = await fetch(`${API_BASE}/portfolio-stress-test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      holdings,
      custom_shock_pct: customShockPct ?? null,
    }),
    cache: "no-store",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    let message = `Request failed with status ${res.status}`;
    if (typeof body.detail === "string") {
      message = body.detail;
    } else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      message = body.detail[0].msg;
    }
    throw new ApiError(message, res.status, body);
  }

  return res.json();
}

export interface SavedPortfolio {
  id: number;
  name: string;
  holdings: { ticker: string; weight: number }[];
  created_at: string;
}

export async function savePortfolio(
  name: string,
  holdings: { ticker: string; weight: number }[],
  accessToken: string
): Promise<SavedPortfolio> {
  const res = await fetch(`${API_BASE}/portfolios`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ name, holdings }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(body.detail || `Failed to save portfolio (${res.status})`, res.status, body);
  }
  return res.json();
}

export async function listSavedPortfolios(accessToken: string): Promise<SavedPortfolio[]> {
  const res = await fetch(`${API_BASE}/portfolios`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(body.detail || `Failed to load portfolios (${res.status})`, res.status, body);
  }
  return res.json();
}

export async function deleteSavedPortfolio(id: number, accessToken: string): Promise<void> {
  const res = await fetch(`${API_BASE}/portfolios/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(body.detail || `Failed to delete portfolio (${res.status})`, res.status, body);
  }
}

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(message: string, status: number, body?: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export async function fetchReport(ticker: string, lang: "en" | "ar" = "en"): Promise<ReportResponse> {
  const res = await fetch(
    `${API_BASE}/report/${encodeURIComponent(ticker)}?lang=${lang}`,
    { cache: "no-store" }
  );

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      body.detail || `Request failed with status ${res.status}`,
      res.status,
      body
    );
  }

  return res.json();
}

export async function fetchPortfolioReport(
  holdings: { ticker: string; weight: number }[],
  lang: "en" | "ar" = "en"
): Promise<PortfolioReportResponse> {
  const res = await fetch(`${API_BASE}/portfolio-report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ holdings, lang }),
    cache: "no-store",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    // FastAPI validation errors (422) come back as a list under `detail`
    let message = `Request failed with status ${res.status}`;
    if (typeof body.detail === "string") {
      message = body.detail;
    } else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      message = body.detail[0].msg;
    }
    throw new ApiError(message, res.status, body);
  }

  return res.json();
}
