"""
Test stress_test.py using synthetic data with a deliberate volatility gap
between two assets, to prove parametric shocks distribute correctly
(higher-vol asset should take a bigger hit than lower-vol asset under the
same market-wide shock) and that historical worst-day replay pulls the
correct actual worst dates from the data.
"""

import numpy as np
import pandas as pd
from stress_test import parametric_shock_scenario, historical_worst_day_scenario, run_all_scenarios

np.random.seed(7)

n_days = 300
dates = pd.bdate_range(start="2024-01-01", periods=n_days)

# LOWVOL: steady, low-volatility asset (like a utility or bond proxy)
# HIGHVOL: choppy, high-volatility asset (like a small-cap growth stock)
lowvol_returns = np.random.normal(0.0002, 0.006, n_days)
highvol_returns = np.random.normal(0.0004, 0.025, n_days)

# Inject one deliberate, known crash day into HIGHVOL so we can verify
# historical_worst_day_scenario finds the exact right date and magnitude.
crash_index = 150
highvol_returns[crash_index] = -0.18  # a known, deliberate -18% single day

prices_df = pd.DataFrame({
    "LOWVOL": 100 * (1 + lowvol_returns).cumprod(),
    "HIGHVOL": 100 * (1 + highvol_returns).cumprod(),
}, index=dates)

weights = {"LOWVOL": 0.5, "HIGHVOL": 0.5}
individual_volatilities = {
    "LOWVOL": lowvol_returns.std() * np.sqrt(252),
    "HIGHVOL": highvol_returns.std() * np.sqrt(252),
}

print("=" * 60)
print("TEST 1: Parametric shock scenario (-20% market crash)")
print("=" * 60)
print(f"LOWVOL annualized volatility:  {individual_volatilities['LOWVOL']*100:.2f}%")
print(f"HIGHVOL annualized volatility: {individual_volatilities['HIGHVOL']*100:.2f}%")

result = parametric_shock_scenario(weights, individual_volatilities, -0.20)
print(f"\nAsset-level shocks under -20% market crash:")
print(f"  LOWVOL:  {result['asset_shocks']['LOWVOL']*100:.2f}%")
print(f"  HIGHVOL: {result['asset_shocks']['HIGHVOL']*100:.2f}%")
print(f"Portfolio impact: {result['portfolio_impact']*100:.2f}%")

print()
print("=" * 60)
print("TEST 2: Historical worst-day replay")
print("=" * 60)
hist_result = historical_worst_day_scenario(prices_df, weights)
print(f"LOWVOL worst day:  {hist_result['asset_worst_days']['LOWVOL']*100:.2f}% "
      f"on {hist_result['asset_worst_day_dates']['LOWVOL']}")
print(f"HIGHVOL worst day: {hist_result['asset_worst_days']['HIGHVOL']*100:.2f}% "
      f"on {hist_result['asset_worst_day_dates']['HIGHVOL']}")
print(f"Portfolio impact if both hit their worst day simultaneously: "
      f"{hist_result['portfolio_impact']*100:.2f}%")

expected_crash_date = str(dates[crash_index].date())

print()
print("--- Sanity checks ---")
checks = [
    ("HIGHVOL takes a bigger shock than LOWVOL under the same market crash",
     abs(result['asset_shocks']['HIGHVOL']) > abs(result['asset_shocks']['LOWVOL'])),
    ("Portfolio impact is between the two individual asset shocks (weighted avg-ish)",
     min(result['asset_shocks'].values()) <= result['portfolio_impact'] <= max(result['asset_shocks'].values())),
    ("Historical worst-day correctly identifies the injected -18% crash day",
     hist_result['asset_worst_days']['HIGHVOL'] < -0.15),
    ("Historical worst-day correctly identifies the exact injected crash date",
     hist_result['asset_worst_day_dates']['HIGHVOL'] == expected_crash_date),
    ("Historical worst-day portfolio impact is worse than a normal trading day",
     hist_result['portfolio_impact'] < -0.05),
]

all_passed = True
for description, passed in checks:
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_passed = False
    print(f"[{status}] {description}")

print("\n" + ("ALL CHECKS PASSED" if all_passed else "SOME CHECKS FAILED"))

print()
print("=" * 60)
print("TEST 3: run_all_scenarios (full preset sweep)")
print("=" * 60)
all_results = run_all_scenarios(prices_df, weights, individual_volatilities, custom_shock_pct=-0.30)
for name, res in all_results.items():
    print(f"  {name:22s}: portfolio impact = {res['portfolio_impact']*100:.2f}%")