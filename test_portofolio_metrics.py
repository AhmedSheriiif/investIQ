"""
Test portfolio_metrics.py using synthetic multi-asset price data with known
correlation properties, to prove the portfolio math (especially the
diversification benefit) behaves correctly before touching real data.
"""

import numpy as np
import pandas as pd
from portfolio_metrics import compute_portfolio_metrics, portfolio_volatility, compute_covariance_matrix

np.random.seed(42)

n_days = 504
dates = pd.bdate_range(start="2024-01-01", periods=n_days)

# Three synthetic assets:
# A and B: highly correlated (both driven by the same underlying factor) -
#   diversifying between them should barely reduce volatility.
# C: independent / uncorrelated with A and B - diversifying with C should
#   meaningfully reduce portfolio volatility.
common_factor = np.random.normal(0.0004, 0.015, n_days)

a_returns = common_factor + np.random.normal(0, 0.003, n_days)  # mostly common_factor
b_returns = common_factor + np.random.normal(0, 0.003, n_days)  # mostly common_factor (correlated with A)
c_returns = np.random.normal(0.0003, 0.018, n_days)             # independent

prices_df = pd.DataFrame({
    "ASSET_A": 100 * (1 + a_returns).cumprod(),
    "ASSET_B": 100 * (1 + b_returns).cumprod(),
    "ASSET_C": 100 * (1 + c_returns).cumprod(),
}, index=dates)

print("=" * 60)
print("TEST 1: Portfolio of highly-correlated assets (A + B only)")
print("=" * 60)
weights_correlated = {"ASSET_A": 0.5, "ASSET_B": 0.5}
metrics_correlated = compute_portfolio_metrics(prices_df[["ASSET_A", "ASSET_B"]], weights_correlated)

print(f"Annualized volatility:     {metrics_correlated['annualized_volatility']*100:.2f}%")
print(f"Diversification benefit:   {metrics_correlated['diversification_benefit']*100:.2f}%")
print(f"Correlation A-B:           {metrics_correlated['correlation_matrix'].loc['ASSET_A', 'ASSET_B']:.3f}")

print()
print("=" * 60)
print("TEST 2: Portfolio with an uncorrelated asset added (A + C)")
print("=" * 60)
weights_diversified = {"ASSET_A": 0.5, "ASSET_C": 0.5}
metrics_diversified = compute_portfolio_metrics(prices_df[["ASSET_A", "ASSET_C"]], weights_diversified)

print(f"Annualized volatility:     {metrics_diversified['annualized_volatility']*100:.2f}%")
print(f"Diversification benefit:   {metrics_diversified['diversification_benefit']*100:.2f}%")
print(f"Correlation A-C:           {metrics_diversified['correlation_matrix'].loc['ASSET_A', 'ASSET_C']:.3f}")

print()
print("--- Sanity checks ---")
checks = [
    ("A-B correlation is high (>0.7, same underlying factor)",
     metrics_correlated['correlation_matrix'].loc['ASSET_A', 'ASSET_B'] > 0.7),
    ("A-C correlation is low (<0.3, independent assets)",
     abs(metrics_diversified['correlation_matrix'].loc['ASSET_A', 'ASSET_C']) < 0.3),
    ("Diversification benefit is LARGER for uncorrelated pair (A+C) than correlated pair (A+B)",
     metrics_diversified['diversification_benefit'] > metrics_correlated['diversification_benefit']),
    ("Weights sum validation rejects bad weights",
     True),  # tested separately below
]

# Test that bad weights raise an error
try:
    compute_portfolio_metrics(prices_df[["ASSET_A", "ASSET_B"]], {"ASSET_A": 0.5, "ASSET_B": 0.3})
    checks[-1] = ("Weights sum validation rejects bad weights", False)
except ValueError:
    pass  # expected

all_passed = True
for description, passed in checks:
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_passed = False
    print(f"[{status}] {description}")

print("\n" + ("ALL CHECKS PASSED" if all_passed else "SOME CHECKS FAILED"))

print()
print("--- Correlation matrix (all 3 assets) ---")
returns_df = prices_df.pct_change().dropna()
print(returns_df.corr().round(3))