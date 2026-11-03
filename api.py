"""
InvestIQ Phase 1 - API Backend

Wraps the Phase 0 pipeline (fetch -> risk metrics -> AI narrative) behind a
FastAPI JSON endpoint so the Next.js dashboard can call it.

Supports:
- Non-US tickers via .CA suffix fallback (Egyptian Exchange / EGX)
- Per-market benchmark selection (SPY for US, ^CASE30 / EGX30 for Egypt)
- Bilingual narrative generation (English / Arabic) via ?lang=

Run locally with:
    uvicorn api:app --reload --port 8000

Then test at:
    http://localhost:8000/docs
    http://localhost:8000/report/AAPL
    http://localhost:8000/report/COMI?lang=ar
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import Literal, Any
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime

from data_fetcher import fetch_ticker_data, resolve_benchmark
from risk_metrics import compute_all_metrics
from portfolio_metrics import compute_portfolio_metrics
from stress_test import run_all_scenarios
from narrative_generator import generate_risk_narrative, generate_portfolio_narrative, PROVIDER
from database import get_db
from models import Portfolio, SavedReport
from supabase_auth import get_current_user, AuthenticatedUser

app = FastAPI(title="InvestIQ API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_benchmark_cache: dict[str, object] = {}
_report_cache: dict[str, "ReportResponse"] = {}
_portfolio_cache: dict[str, "PortfolioReportResponse"] = {}
_stress_test_cache: dict[str, "StressTestResponse"] = {}


class Holding(BaseModel):
    ticker: str
    weight: float


class PortfolioRequest(BaseModel):
    holdings: list[Holding]
    lang: Literal["en", "ar"] = "en"

    @field_validator("holdings")
    @classmethod
    def weights_must_sum_to_one(cls, holdings):
        if len(holdings) < 2:
            raise ValueError("A portfolio needs at least 2 holdings")
        total = sum(h.weight for h in holdings)
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Weights must sum to 1.0 (100%), got {total:.4f}")
        return holdings


class PortfolioMetrics(BaseModel):
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float
    var_99: float
    cvar_95: float
    diversification_benefit: float
    individual_volatilities: dict[str, float]
    correlation_matrix: dict[str, dict[str, float]]
    period_start: str
    period_end: str
    trading_days: int


class PortfolioReportResponse(BaseModel):
    tickers: list[str]
    weights: dict[str, float]
    metrics: PortfolioMetrics
    narrative: str
    llm_provider: str
    language: str


class StressTestRequest(BaseModel):
    holdings: list[Holding]
    custom_shock_pct: float | None = None

    @field_validator("holdings")
    @classmethod
    def weights_must_sum_to_one(cls, holdings):
        if len(holdings) < 2:
            raise ValueError("A portfolio needs at least 2 holdings")
        total = sum(h.weight for h in holdings)
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Weights must sum to 1.0 (100%), got {total:.4f}")
        return holdings


class StressTestResponse(BaseModel):
    tickers: list[str]
    weights: dict[str, float]
    scenarios: dict[str, dict[str, Any]]


class RiskMetrics(BaseModel):
    current_price: float
    currency: str
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float
    var_99: float
    cvar_95: float
    beta: float | None = None
    period_start: str
    period_end: str
    trading_days: int


class ReportResponse(BaseModel):
    ticker: str
    resolved_ticker: str
    benchmark: str
    metrics: RiskMetrics
    narrative: str
    llm_provider: str
    language: str


def get_benchmark_prices(benchmark_symbol: str):
    if benchmark_symbol not in _benchmark_cache:
        _benchmark_cache[benchmark_symbol] = fetch_ticker_data(benchmark_symbol)["prices"]
    return _benchmark_cache[benchmark_symbol]


class SavePortfolioRequest(BaseModel):
    name: str
    holdings: list[Holding]

    @field_validator("holdings")
    @classmethod
    def weights_must_sum_to_one(cls, holdings):
        if len(holdings) < 2:
            raise ValueError("A portfolio needs at least 2 holdings")
        total = sum(h.weight for h in holdings)
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Weights must sum to 1.0 (100%), got {total:.4f}")
        return holdings


class SavedPortfolioOut(BaseModel):
    id: int
    name: str
    holdings: list[dict]
    created_at: datetime

    class Config:
        from_attributes = True  # lets Pydantic read directly from a SQLAlchemy object


class SaveReportRequest(BaseModel):
    report_type: Literal["single", "portfolio"]
    tickers: list[str]
    report_data: dict


class SavedReportOut(BaseModel):
    id: int
    report_type: str
    tickers: list[str]
    report_data: dict
    created_at: datetime

    class Config:
        from_attributes = True


@app.get("/")
def root():
    return {"status": "ok", "service": "InvestIQ API"}


@app.post("/portfolio-stress-test", response_model=StressTestResponse)
def get_stress_test(request: StressTestRequest, refresh: bool = False):
    """
    Runs preset stress scenarios (market crash, correction, rate hike shock,
    rally) plus an optional custom shock, and a historical worst-day replay,
    against a multi-asset portfolio. See stress_test.py for methodology.
    """
    tickers = [h.ticker.upper() for h in request.holdings]
    weights = {h.ticker.upper(): h.weight for h in request.holdings}

    cache_key = f"{','.join(sorted(tickers))}:{request.custom_shock_pct}"
    if not refresh and cache_key in _stress_test_cache:
        return _stress_test_cache[cache_key]

    try:
        series_list = []
        for ticker in tickers:
            asset_data = fetch_ticker_data(ticker)
            prices = asset_data["prices"]
            prices.name = ticker
            series_list.append(prices)

        prices_df = pd.concat(series_list, axis=1, join="inner").dropna()

        if len(prices_df) < 30:
            raise ValueError(
                f"Only {len(prices_df)} overlapping trading days across all holdings - "
                f"too little shared history to run a reliable stress test."
            )

        portfolio_metrics = compute_portfolio_metrics(prices_df, weights)
        scenarios = run_all_scenarios(
            prices_df, weights, portfolio_metrics["individual_volatilities"],
            custom_shock_pct=request.custom_shock_pct,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run stress test: {e}")

    response = StressTestResponse(tickers=tickers, weights=weights, scenarios=scenarios)
    _stress_test_cache[cache_key] = response
    return response


@app.post("/portfolio-report", response_model=PortfolioReportResponse)
def get_portfolio_report(request: PortfolioRequest, refresh: bool = False):
    """
    Multi-asset portfolio pipeline: resolve + fetch each holding's price
    history, align on shared trading dates, compute portfolio-level risk
    metrics (return, volatility via the full covariance matrix, VaR/CVaR,
    correlation matrix, diversification benefit), then generate an AI
    narrative covering the combined portfolio.
    """
    tickers = [h.ticker.upper() for h in request.holdings]
    weights = {h.ticker.upper(): h.weight for h in request.holdings}
    lang = request.lang

    cache_key = f"{','.join(sorted(tickers))}:{lang}"
    if not refresh and cache_key in _portfolio_cache:
        return _portfolio_cache[cache_key]

    try:
        series_list = []
        for ticker in tickers:
            asset_data = fetch_ticker_data(ticker)
            prices = asset_data["prices"]
            prices.name = ticker  # keep the ORIGINAL ticker as the column name,
            # not the resolved symbol (e.g. "COMI" not "COMI.CA"), so it matches
            # the weights dict keys the caller sent us.
            series_list.append(prices)

        prices_df = pd.concat(series_list, axis=1, join="inner").dropna()

        if len(prices_df) < 30:
            raise ValueError(
                f"Only {len(prices_df)} overlapping trading days across all holdings - "
                f"too little shared history to compute reliable portfolio metrics."
            )

        metrics = compute_portfolio_metrics(prices_df, weights)
        narrative = generate_portfolio_narrative(tickers, weights, metrics, language=lang)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate portfolio report: {e}")

    response = PortfolioReportResponse(
        tickers=tickers,
        weights=weights,
        metrics=PortfolioMetrics(
            annualized_return=metrics["annualized_return"],
            annualized_volatility=metrics["annualized_volatility"],
            sharpe_ratio=metrics["sharpe_ratio"],
            sortino_ratio=metrics["sortino_ratio"],
            max_drawdown=metrics["max_drawdown"],
            var_95=metrics["var_95"],
            var_99=metrics["var_99"],
            cvar_95=metrics["cvar_95"],
            diversification_benefit=metrics["diversification_benefit"],
            individual_volatilities=metrics["individual_volatilities"],
            correlation_matrix=metrics["correlation_matrix"].to_dict(),
            period_start=str(metrics["period_start"].date()),
            period_end=str(metrics["period_end"].date()),
            trading_days=metrics["trading_days"],
        ),
        narrative=narrative,
        llm_provider=PROVIDER,
        language=lang,
    )

    _portfolio_cache[cache_key] = response
    return response
@app.get("/report/{ticker}", response_model=ReportResponse)
def get_report(
    ticker: str,
    refresh: bool = False,
    lang: Literal["en", "ar"] = Query("en", description="Narrative language: en or ar"),
):
    ticker = ticker.upper()
    cache_key = f"{ticker}:{lang}"

    if not refresh and cache_key in _report_cache:
        return _report_cache[cache_key]

    try:
        asset_data = fetch_ticker_data(ticker)
        resolved_ticker = asset_data["resolved_ticker"]
        currency = asset_data["currency"]

        benchmark_symbol = resolve_benchmark(resolved_ticker)
        benchmark_prices = get_benchmark_prices(benchmark_symbol)

        metrics = compute_all_metrics(asset_data["prices"], benchmark_prices)
        narrative = generate_risk_narrative(resolved_ticker, metrics, language=lang)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")

    response = ReportResponse(
        ticker=ticker,
        resolved_ticker=resolved_ticker,
        benchmark=benchmark_symbol,
        metrics=RiskMetrics(
            current_price=metrics["current_price"],
            currency=currency,
            annualized_return=metrics["annualized_return"],
            annualized_volatility=metrics["annualized_volatility"],
            sharpe_ratio=metrics["sharpe_ratio"],
            sortino_ratio=metrics["sortino_ratio"],
            max_drawdown=metrics["max_drawdown"],
            var_95=metrics["var_95"],
            var_99=metrics["var_99"],
            cvar_95=metrics["cvar_95"],
            beta=metrics.get("beta"),
            period_start=str(metrics["period_start"].date()),
            period_end=str(metrics["period_end"].date()),
            trading_days=metrics["trading_days"],
        ),
        narrative=narrative,
        llm_provider=PROVIDER,
        language=lang,
    )

    _report_cache[cache_key] = response
    return response


# ============================================================
# Protected endpoints (require a valid Supabase auth token)
# ============================================================

@app.post("/portfolios", response_model=SavedPortfolioOut)
def save_portfolio(
    request: SavePortfolioRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Saves a named portfolio (list of holdings) for the authenticated user."""
    portfolio = Portfolio(
        user_id=user.user_id,
        name=request.name,
        holdings=[h.model_dump() for h in request.holdings],
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@app.get("/portfolios", response_model=list[SavedPortfolioOut])
def list_portfolios(
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists every saved portfolio belonging to the authenticated user."""
    return db.query(Portfolio).filter(Portfolio.user_id == user.user_id).order_by(Portfolio.created_at.desc()).all()


@app.delete("/portfolios/{portfolio_id}")
def delete_portfolio(
    portfolio_id: int,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes a portfolio - only if it belongs to the authenticated user."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id, Portfolio.user_id == user.user_id
    ).first()
    if not portfolio:
        # Deliberately the same 404 whether the portfolio doesn't exist or
        # belongs to someone else - don't leak which case it is.
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(portfolio)
    db.commit()
    return {"status": "deleted", "id": portfolio_id}


@app.post("/reports", response_model=SavedReportOut)
def save_report(
    request: SaveReportRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Saves a full report payload (single-asset or portfolio) for later retrieval."""
    report = SavedReport(
        user_id=user.user_id,
        report_type=request.report_type,
        tickers=request.tickers,
        report_data=request.report_data,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@app.get("/reports", response_model=list[SavedReportOut])
def list_reports(
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists every saved report belonging to the authenticated user."""
    return db.query(SavedReport).filter(SavedReport.user_id == user.user_id).order_by(SavedReport.created_at.desc()).all()