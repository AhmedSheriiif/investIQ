"""
InvestIQ Phase 2 - Scenario / Stress Testing

Two stress-test methodologies, both grounded in the portfolio's own real
historical data (no external scenario data source needed):

1. Parametric shock: a named or custom market-wide shock (e.g. "-20% crash")
   distributed across holdings proportional to each asset's own volatility
   relative to the portfolio average. Higher-volatility holdings take a
   larger hit than lower-volatility ones - consistent with how real
   diversified portfolios actually behave in broad selloffs.

2. Historical worst-day replay: takes each holding's own worst single
   historical daily return and applies them all simultaneously. This
   answers "what if every holding had its worst day on the same day" -
   a standard stress technique that doesn't require assuming a specific
   market-wide shock size.

Pure math module - takes the same prices_df/weights inputs as
portfolio_metrics.py, no network calls.
"""

import pandas as pd

from portfolio_metrics import compute_returns_matrix, naive_weighted_volatility

# Named preset scenarios, expressed as a market-wide shock percentage.
# Rate hike and rally are illustrative magnitudes, not derived from any
# specific historical event - treat as round-number stress levels, not
# predictions.
SCENARIO_PRESETS = {
    "market_crash": -0.20,
    "correction": -0.10,
    "rate_hike_shock": -0.08,
    "rally": 0.15,
}


def parametric_shock_scenario(weights: dict, individual_volatilities: dict, shock_pct: float) -> dict:
    """
    Distributes a market-wide shock across holdings proportional to each
    asset's own volatility relative to the weighted-average portfolio
    volatility. An asset with double the average volatility takes roughly
    double the shock; an asset with half the average volatility takes
    roughly half.
    """
    tickers = list(weights.keys())
    avg_vol = naive_weighted_volatility(weights, individual_volatilities)

    if avg_vol == 0:
        # Degenerate case: no volatility data, apply shock uniformly.
        asset_shocks = {t: shock_pct for t in tickers}
    else:
        asset_shocks = {
            t: shock_pct * (individual_volatilities[t] / avg_vol) for t in tickers
        }

    portfolio_loss = sum(weights[t] * asset_shocks[t] for t in tickers)

    return {
        "scenario_type": "parametric_shock",
        "shock_pct": shock_pct,
        "asset_shocks": asset_shocks,
        "portfolio_impact": portfolio_loss,
    }


def historical_worst_day_scenario(prices_df: pd.DataFrame, weights: dict) -> dict:
    """
    For each holding, finds its single worst historical daily return in the
    given price history, then computes what the portfolio would lose if
    every holding experienced its own worst day simultaneously. This is
    more conservative (worse) than any single day the portfolio actually
    experienced historically, since real worst-days for different assets
    rarely land on the exact same date - it's an intentional upper-bound
    stress case, not a "this happened" claim.
    """
    returns_df = compute_returns_matrix(prices_df)
    tickers = list(weights.keys())

    worst_day_per_asset = {t: returns_df[t].min() for t in tickers}
    worst_day_dates = {t: returns_df[t].idxmin() for t in tickers}

    portfolio_loss = sum(weights[t] * worst_day_per_asset[t] for t in tickers)

    return {
        "scenario_type": "historical_worst_day",
        "asset_worst_days": worst_day_per_asset,
        "asset_worst_day_dates": {t: str(d.date()) for t, d in worst_day_dates.items()},
        "portfolio_impact": portfolio_loss,
    }


def run_all_scenarios(prices_df: pd.DataFrame, weights: dict, individual_volatilities: dict,
                       custom_shock_pct: float = None) -> dict:
    """Runs every named preset plus the historical worst-day scenario, returns a dict keyed by scenario name."""
    results = {}

    for name, shock_pct in SCENARIO_PRESETS.items():
        results[name] = parametric_shock_scenario(weights, individual_volatilities, shock_pct)

    if custom_shock_pct is not None:
        results["custom"] = parametric_shock_scenario(weights, individual_volatilities, custom_shock_pct)

    results["historical_worst_day"] = historical_worst_day_scenario(prices_df, weights)

    return results