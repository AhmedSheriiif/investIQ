"""
InvestIQ Phase 0 - Risk Metrics Engine

Computes core portfolio risk metrics from a price series:
- Annualized return & volatility
- Sharpe ratio
- Sortino ratio
- Max drawdown
- Historical VaR (95%, 99%)
- CVaR (Expected Shortfall)
- Beta vs a benchmark

Pure math module - no network calls. Takes pandas Series of prices, returns a dict of metrics.
"""

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def compute_daily_returns(prices: pd.Series) -> pd.Series:
    """Simple daily percentage returns from a price series."""
    return prices.pct_change().dropna()


def annualized_return(daily_returns: pd.Series) -> float:
    mean_daily = daily_returns.mean()
    return (1 + mean_daily) ** TRADING_DAYS_PER_YEAR - 1


def annualized_volatility(daily_returns: pd.Series) -> float:
    return daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)


def sharpe_ratio(daily_returns: pd.Series, risk_free_rate: float = 0.04) -> float:
    """risk_free_rate is annualized (default 4%, roughly current T-bill territory)."""
    excess_daily_rf = (1 + risk_free_rate) ** (1 / TRADING_DAYS_PER_YEAR) - 1
    excess_returns = daily_returns - excess_daily_rf
    if excess_returns.std() == 0:
        return 0.0
    return (excess_returns.mean() / excess_returns.std()) * np.sqrt(TRADING_DAYS_PER_YEAR)


def sortino_ratio(daily_returns: pd.Series, risk_free_rate: float = 0.04) -> float:
    """Like Sharpe, but only penalizes downside volatility."""
    excess_daily_rf = (1 + risk_free_rate) ** (1 / TRADING_DAYS_PER_YEAR) - 1
    excess_returns = daily_returns - excess_daily_rf
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = downside_returns.std()
    if downside_std == 0 or pd.isna(downside_std):
        return 0.0
    return (excess_returns.mean() / downside_std) * np.sqrt(TRADING_DAYS_PER_YEAR)


def max_drawdown(prices: pd.Series) -> float:
    """Largest peak-to-trough decline, as a negative percentage."""
    cumulative_max = prices.cummax()
    drawdown = (prices - cumulative_max) / cumulative_max
    return drawdown.min()


def historical_var(daily_returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Historical VaR: the loss threshold not expected to be exceeded
    on (confidence)% of days, based on actual historical return distribution.
    Returned as a negative daily percentage (e.g. -0.032 = -3.2%).
    """
    return np.percentile(daily_returns, (1 - confidence) * 100)


def conditional_var(daily_returns: pd.Series, confidence: float = 0.95) -> float:
    """
    CVaR / Expected Shortfall: average loss on the days that fall
    beyond the VaR threshold. More conservative than VaR alone.
    """
    var_threshold = historical_var(daily_returns, confidence)
    tail_losses = daily_returns[daily_returns <= var_threshold]
    if len(tail_losses) == 0:
        return var_threshold
    return tail_losses.mean()


def beta(daily_returns: pd.Series, benchmark_daily_returns: pd.Series) -> float:
    """Covariance(asset, benchmark) / Variance(benchmark)."""
    aligned = pd.concat([daily_returns, benchmark_daily_returns], axis=1, join="inner").dropna()
    aligned.columns = ["asset", "benchmark"]
    covariance = aligned["asset"].cov(aligned["benchmark"])
    benchmark_variance = aligned["benchmark"].var()
    if benchmark_variance == 0:
        return 0.0
    return covariance / benchmark_variance


def compute_all_metrics(prices: pd.Series, benchmark_prices: pd.Series = None,
                         risk_free_rate: float = 0.04) -> dict:
    """
    Compute the full Phase 0 metrics set for a single asset.
    prices: pd.Series of closing prices, indexed by date, ascending.
    benchmark_prices: optional pd.Series for beta calculation (e.g. SPY).
    """
    daily_returns = compute_daily_returns(prices)

    metrics = {
        "annualized_return": annualized_return(daily_returns),
        "annualized_volatility": annualized_volatility(daily_returns),
        "sharpe_ratio": sharpe_ratio(daily_returns, risk_free_rate),
        "sortino_ratio": sortino_ratio(daily_returns, risk_free_rate),
        "max_drawdown": max_drawdown(prices),
        "var_95": historical_var(daily_returns, 0.95),
        "var_99": historical_var(daily_returns, 0.99),
        "cvar_95": conditional_var(daily_returns, 0.95),
        "current_price": prices.iloc[-1],
        "period_start": prices.index[0],
        "period_end": prices.index[-1],
        "trading_days": len(prices),
    }

    if benchmark_prices is not None:
        benchmark_daily_returns = compute_daily_returns(benchmark_prices)
        metrics["beta"] = beta(daily_returns, benchmark_daily_returns)

    return metrics