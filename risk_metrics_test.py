"""
Test risk_metrics.py using synthetic price data with known statistical properties,
so we can sanity-check the outputs against expected ranges before touching real data.
"""

import numpy as np
import pandas as pd
from risk_metrics import compute_all_metrics

np.random.seed(42)

# Simulate 2 years of daily prices (~504 trading days)
# Asset: starts at $100, drifts up ~15%/yr with ~25% annualized vol (a "risky growth stock" profile)
n_days = 504
dates = pd.bdate_range(start="2024-01-01", periods=n_days)

daily_drift = (1.15) ** (1 / 252) - 1
daily_vol = 0.25 / np.sqrt(252)
daily_returns_sim = np.random.normal(daily_drift, daily_vol, n_days)
prices = pd.Series(100 * (1 + daily_returns_sim).cumprod(), index=dates, name="ASSET")

# Benchmark: lower vol, lower drift (e.g. "SPY-like")
bench_drift = (1.10) ** (1 / 252) - 1
bench_vol = 0.15 / np.sqrt(252)
# Correlate benchmark with asset ~0.6 by blending in some of the asset's noise
bench_returns_sim = 0.6 * daily_returns_sim + 0.4 * np.random.normal(bench_drift, bench_vol, n_days)
benchmark_prices = pd.Series(100 * (1 + bench_returns_sim).cumprod(), index=dates, name="BENCHMARK")

metrics = compute_all_metrics(prices, benchmark_prices)

print("=" * 50)
print("RISK METRICS TEST OUTPUT (synthetic data)")
print("=" * 50)
for key, value in metrics.items():
    if isinstance(value, float):
        print(f"{key:25s}: {value:.4f}")
    else:
        print(f"{key:25s}: {value}")

print("\n--- Sanity checks ---")
checks = [
    ("Annualized return near +15% target", 0.05 < metrics["annualized_return"] < 0.30),
    ("Annualized volatility near 25% target", 0.18 < metrics["annualized_volatility"] < 0.35),
    ("Sharpe ratio is a plausible finite number", -3 < metrics["sharpe_ratio"] < 5),
    ("Max drawdown is negative", metrics["max_drawdown"] < 0),
    ("VaR 95 is negative (a loss threshold)", metrics["var_95"] < 0),
    ("VaR 99 is more negative than VaR 95", metrics["var_99"] < metrics["var_95"]),
    ("CVaR 95 is more negative than VaR 95 (tail avg worse than threshold)",
     metrics["cvar_95"] < metrics["var_95"]),
    ("Beta is positive and plausible (asset is riskier than benchmark)", 0.5 < metrics["beta"] < 2.5),
]

all_passed = True
for description, passed in checks:
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_passed = False
    print(f"[{status}] {description}")

print("\n" + ("ALL CHECKS PASSED" if all_passed else "SOME CHECKS FAILED"))