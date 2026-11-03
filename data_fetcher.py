"""
InvestIQ Phase 0 - Data Fetcher

Pulls historical daily close prices via yfinance for a list of tickers + a benchmark,
then runs each through risk_metrics.compute_all_metrics().

NOTE: This will NOT run in a network-restricted sandbox. Run it on your own machine
or the Oracle VM where yfinance can reach Yahoo Finance directly.
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd

from risk_metrics import compute_all_metrics

# .env loader - needed for ANTHROPIC_API_KEY/GROQ_API_KEY (narrative layer)
# and now EODHD_API_KEY (EGX fallback data source, same account as IR Reporter).
load_dotenv()

TICKERS = ["AAPL", "MSFT"]
BENCHMARK = "SPY"
EGX_BENCHMARK = "^CASE30"  # EGX 30 index - use for Egyptian Exchange tickers
PERIOD = "2y"  # 2 years of daily history

EODHD_API_KEY = os.environ.get("EODHD_API_KEY")


def resolve_benchmark(resolved_ticker: str) -> str:
    """Pick a sensible benchmark based on which market the ticker resolved to."""
    if resolved_ticker.endswith(".CA") or resolved_ticker.endswith(".EGX"):
        return EGX_BENCHMARK
    return BENCHMARK


def fetch_from_eodhd(ticker: str, period: str = PERIOD) -> dict:
    """
    Fallback data source for EGX tickers when Yahoo/yfinance has no coverage.
    Uses EODHD's official Python library (pip install eodhd), reusing the
    EODHD_API_KEY already set up for IR Reporter's EODHD adapter.

    EODHD's exchange code for the Egyptian Exchange is 'EGX' (ticker format:
    'SYMBOL.EGX'), confirmed against their official docs:
    https://eodhd.com/financial-apis/python-financial-libraries-and-code-samples
    """
    if not EODHD_API_KEY:
        raise ValueError("EODHD_API_KEY not set in .env - required for the EODHD fallback")

    from eodhd import APIClient

    symbol = f"{ticker}.EGX"
    years = 1
    end = datetime.now().date()
    start = end - timedelta(days=years * 365)
    api = APIClient(EODHD_API_KEY)
    rows = api.get_eod_historical_stock_market_data(
        symbol=symbol,
        period="d",
        from_date=start.isoformat(),
        to_date=end.isoformat(),
        order="a",
    )
    print(rows)

    if not rows or not isinstance(rows, list):
        raise ValueError(f"No data returned from EODHD for '{symbol}'")

    print("Data Returned", rows)
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()

    close = df["adjusted_close"] if "adjusted_close" in df.columns else df["close"]
    close = close.dropna()
    close.name = symbol

    # All EGX-listed instruments trade in Egyptian pounds.
    return {"prices": close, "resolved_ticker": symbol, "currency": "EGP"}


def fetch_close_prices(ticker: str, period: str = PERIOD) -> pd.Series:
    """
    Fetch daily close prices for a single ticker.
    Returns a pd.Series indexed by date, ascending, no NaNs.
    Backward-compatible wrapper around fetch_ticker_data() for the CLI pipeline.
    """
    return fetch_ticker_data(ticker, period)["prices"]


def fetch_ticker_data(ticker: str, period: str = PERIOD) -> dict:
    """
    Fetch price history for a ticker, trying three sources in order:
      1. yfinance, symbol as given (covers US and most global tickers)
      2. yfinance with '.CA' suffix (Yahoo's Egyptian Exchange / EGX suffix,
         covers major EGX names like COMI, SWDY, HRHO, ETEL)
      3. EODHD with '.EGX' suffix, if EODHD_API_KEY is set - a fallback for
         EGX names that Yahoo doesn't carry, using the same EODHD account
         already wired into IR Reporter

    Returns dict: {prices, resolved_ticker, currency}
    """
    yf_candidates = [ticker]
    if "." not in ticker:
        yf_candidates.append(f"{ticker}.CA")

    last_error = None

    for candidate in yf_candidates:
        try:
            yf_ticker = yf.Ticker(candidate)
            data = yf_ticker.history(period=period, auto_adjust=True)

            if data.empty:
                last_error = ValueError(f"No data returned for '{candidate}'")
                continue

            close = data["Close"].dropna()
            close.name = candidate

            currency = "USD"
            try:
                currency = yf_ticker.fast_info.get("currency") or "USD"
            except Exception:
                pass  # currency lookup is best-effort, don't fail the fetch over it

            return {"prices": close, "resolved_ticker": candidate, "currency": currency}

        except Exception as e:
            last_error = e
            continue

    # Both yfinance attempts failed - try EODHD as a last resort for EGX names.
    if "." not in ticker and EODHD_API_KEY:
        try:
            print("YFinance Failed: Fetching from EODHD...")
            return fetch_from_eodhd(ticker, period)
        except Exception as e:
            last_error = e

    tried = ", ".join(yf_candidates + ([f"{ticker}.EGX (EODHD)"] if EODHD_API_KEY else []))
    raise ValueError(
        f"No data found for '{ticker}' (tried: {tried}). "
        f"Check the exact symbol on finance.yahoo.com or eodhd.com/exchange/EGX - "
        f"smaller/less liquid EGX names may not be covered by either source."
    )


def run_phase0(tickers: list, benchmark: str = BENCHMARK):
    print(f"Fetching benchmark ({benchmark})...")
    benchmark_prices = fetch_close_prices(benchmark)
    print(f"  -> {len(benchmark_prices)} trading days, "
          f"{benchmark_prices.index[0].date()} to {benchmark_prices.index[-1].date()}")

    results = {}
    for ticker in tickers:
        print(f"\nFetching {ticker}...")
        prices = fetch_close_prices(ticker)
        print(f"  -> {len(prices)} trading days, "
              f"{prices.index[0].date()} to {prices.index[-1].date()}")

        metrics = compute_all_metrics(prices, benchmark_prices)
        results[ticker] = metrics

        print(f"\n  --- {ticker} Risk Metrics ---")
        print(f"  Current price:          ${metrics['current_price']:.2f}")
        print(f"  Annualized return:      {metrics['annualized_return']*100:.2f}%")
        print(f"  Annualized volatility:  {metrics['annualized_volatility']*100:.2f}%")
        print(f"  Sharpe ratio:           {metrics['sharpe_ratio']:.2f}")
        print(f"  Sortino ratio:          {metrics['sortino_ratio']:.2f}")
        print(f"  Max drawdown:           {metrics['max_drawdown']*100:.2f}%")
        print(f"  VaR (95%, daily):       {metrics['var_95']*100:.2f}%")
        print(f"  VaR (99%, daily):       {metrics['var_99']*100:.2f}%")
        print(f"  CVaR (95%, daily):      {metrics['cvar_95']*100:.2f}%")
        print(f"  Beta (vs {benchmark}):        {metrics['beta']:.2f}")

    return results


if __name__ == "__main__":
    run_phase0(TICKERS, BENCHMARK)