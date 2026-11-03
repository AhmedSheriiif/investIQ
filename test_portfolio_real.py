"""
InvestIQ Phase 2 - Portfolio Math, Real Data Test

Fetches real price history for two ticker pairs and runs them through
portfolio_metrics.py:
  1. AAPL + MSFT  - both US mega-cap tech, expected to be HIGHLY correlated
  2. AAPL + GLD   - stock vs gold, expected to be LOW/weakly correlated

If the math is right, pair 2 should show a meaningfully higher
diversification_benefit than pair 1 - the same pattern we proved with
synthetic data, now on real market data.

Run locally:
    python3 test_portfolio_real.py
"""

import pandas as pd
from data_fetcher import fetch_close_prices
from portfolio_metrics import compute_portfolio_metrics


def build_price_df(tickers: list) -> pd.DataFrame:
    """Fetch and align multiple tickers into one DataFrame, one column each."""
    series_list = []
    for ticker in tickers:
        print(f"Fetching {ticker}...")
        prices = fetch_close_prices(ticker)
        series_list.append(prices)
    df = pd.concat(series_list, axis=1, join="inner")  # inner join aligns on shared dates
    df.columns = tickers
    return df.dropna()


def run_pair_test(tickers: list, weights: dict, label: str):
    print(f"\n{'=' * 60}")
    print(f"{label}: {' + '.join(tickers)}")
    print("=" * 60)

    prices_df = build_price_df(tickers)
    print(f"Aligned data: {len(prices_df)} trading days, "
          f"{prices_df.index[0].date()} to {prices_df.index[-1].date()}")

    metrics = compute_portfolio_metrics(prices_df, weights)

    print(f"\nPortfolio annualized return:     {metrics['annualized_return']*100:.2f}%")
    print(f"Portfolio annualized volatility: {metrics['annualized_volatility']*100:.2f}%")
    print(f"Portfolio Sharpe ratio:          {metrics['sharpe_ratio']:.2f}")
    print(f"Portfolio max drawdown:          {metrics['max_drawdown']*100:.2f}%")
    print(f"Diversification benefit:         {metrics['diversification_benefit']*100:.2f}%")
    print(f"\nCorrelation matrix:")
    print(metrics['correlation_matrix'].round(3))
    print(f"\nIndividual annualized volatilities:")
    for t, v in metrics['individual_volatilities'].items():
        print(f"  {t}: {v*100:.2f}%")

    return metrics


if __name__ == "__main__":
    result_correlated = run_pair_test(
        tickers=["AAPL", "MSFT"],
        weights={"AAPL": 0.5, "MSFT": 0.5},
        label="PAIR 1 (expected HIGH correlation)",
    )

    result_diversified = run_pair_test(
        tickers=["AAPL", "GLD"],
        weights={"AAPL": 0.5, "GLD": 0.5},
        label="PAIR 2 (expected LOW correlation)",
    )

    print(f"\n{'=' * 60}")
    print("COMPARISON")
    print("=" * 60)
    print(f"AAPL+MSFT diversification benefit: {result_correlated['diversification_benefit']*100:.2f}%")
    print(f"AAPL+GLD  diversification benefit: {result_diversified['diversification_benefit']*100:.2f}%")

    if result_diversified['diversification_benefit'] > result_correlated['diversification_benefit']:
        print("\n[EXPECTED] AAPL+GLD shows a bigger diversification benefit than AAPL+MSFT.")
    else:
        print("\n[UNEXPECTED] AAPL+MSFT shows a bigger benefit than AAPL+GLD - worth investigating.")