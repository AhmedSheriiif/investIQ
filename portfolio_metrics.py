"""
InvestIQ Phase 2 - Portfolio Risk Engine

Extends the single-asset risk_metrics.py to a multi-asset portfolio: given a
set of tickers with weights, computes portfolio-level return, volatility,
Sharpe, diversification benefit, and the correlation matrix between holdings.

Pure math module - no network calls. Takes a DataFrame of price series
(one column per ticker) plus a weights dict, returns a dict of portfolio
metrics and a correlation matrix DataFrame.
"""

import numpy as np
import pandas as pd

from risk_metrics import (
    TRADING_DAYS_PER_YEAR,
    compute_daily_returns,
    sharpe_ratio,
    sortino_ratio,
    max_drawdown,
    historical_var,
    conditional_var,
)


def compute_returns_matrix(prices_df: pd.DataFrame) -> pd.DataFrame:
    """Daily returns for every column (ticker) in a multi-asset price DataFrame."""
    return prices_df.pct_change().dropna()


def compute_correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """Pairwise correlation between every pair of assets' daily returns."""
    return returns_df.corr()


def compute_covariance_matrix(returns_df: pd.DataFrame, annualize: bool = True) -> pd.DataFrame:
    """Covariance matrix of daily returns, optionally annualized (x252)."""
    cov = returns_df.cov()
    return cov * TRADING_DAYS_PER_YEAR if annualize else cov


def portfolio_weighted_returns(returns_df: pd.DataFrame, weights: dict) -> pd.Series:
    """
    Combine individual asset daily returns into a single portfolio daily
    return series, weighted by position size. weights must sum to ~1.0 and
    keys must match returns_df's columns.
    """
    tickers = list(returns_df.columns)
    weight_vector = np.array([weights[t] for t in tickers])

    if not np.isclose(weight_vector.sum(), 1.0, atol=0.01):
        raise ValueError(f"Weights must sum to 1.0, got {weight_vector.sum():.4f}")

    return returns_df[tickers].dot(weight_vector)


def portfolio_volatility(weights: dict, annualized_cov: pd.DataFrame) -> float:
    """
    True portfolio volatility accounting for correlation between holdings -
    this is NOT the weighted average of individual volatilities. Two assets
    with low or negative correlation reduce combined volatility below what
    a naive weighted average would suggest - this is the mathematical basis
    of diversification.
    """
    tickers = list(annualized_cov.columns)
    weight_vector = np.array([weights[t] for t in tickers])
    portfolio_variance = weight_vector.T @ annualized_cov.values @ weight_vector
    return np.sqrt(portfolio_variance)


def naive_weighted_volatility(weights: dict, individual_volatilities: dict) -> float:
    """
    The volatility you'd get by simply weighted-averaging individual asset
    volatilities, ignoring correlation. Used only as a comparison baseline
    to show the diversification benefit - never used as the actual risk figure.
    """
    return sum(weights[t] * individual_volatilities[t] for t in weights)


def diversification_benefit(weights: dict, annualized_cov: pd.DataFrame,
                             individual_volatilities: dict) -> float:
    """
    How much volatility is "saved" by combining assets versus holding them
    unweighted-summed with no correlation benefit. Positive = diversification
    is helping; near zero = holdings are too correlated to diversify much.
    Expressed as a percentage reduction from the naive baseline.
    """
    naive = naive_weighted_volatility(weights, individual_volatilities)
    actual = portfolio_volatility(weights, annualized_cov)
    if naive == 0:
        return 0.0
    return (naive - actual) / naive


def compute_portfolio_metrics(prices_df: pd.DataFrame, weights: dict,
                               risk_free_rate: float = 0.04) -> dict:
    """
    Full portfolio-level metrics set, mirroring the single-asset metrics in
    risk_metrics.py but computed for the combined weighted portfolio.

    prices_df: DataFrame, one column per ticker, indexed by date.
    weights: dict of {ticker: weight}, must sum to ~1.0.
    """
    returns_df = compute_returns_matrix(prices_df)
    portfolio_returns = portfolio_weighted_returns(returns_df, weights)

    annualized_cov = compute_covariance_matrix(returns_df, annualize=True)
    correlation = compute_correlation_matrix(returns_df)

    individual_vols = {
        t: returns_df[t].std() * np.sqrt(TRADING_DAYS_PER_YEAR) for t in returns_df.columns
    }

    # Portfolio price series (normalized to start at 100) for drawdown calc.
    portfolio_index = (1 + portfolio_returns).cumprod() * 100

    mean_daily = portfolio_returns.mean()
    annualized_return = (1 + mean_daily) ** TRADING_DAYS_PER_YEAR - 1
    volatility = portfolio_volatility(weights, annualized_cov)

    return {
        "annualized_return": annualized_return,
        "annualized_volatility": volatility,
        "sharpe_ratio": sharpe_ratio(portfolio_returns, risk_free_rate),
        "sortino_ratio": sortino_ratio(portfolio_returns, risk_free_rate),
        "max_drawdown": max_drawdown(portfolio_index),
        "var_95": historical_var(portfolio_returns, 0.95),
        "var_99": historical_var(portfolio_returns, 0.99),
        "cvar_95": conditional_var(portfolio_returns, 0.95),
        "diversification_benefit": diversification_benefit(weights, annualized_cov, individual_vols),
        "individual_volatilities": individual_vols,
        "correlation_matrix": correlation,
        "weights": weights,
        "trading_days": len(portfolio_returns),
        "period_start": prices_df.index[0],
        "period_end": prices_df.index[-1],
    }