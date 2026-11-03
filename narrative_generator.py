"""
InvestIQ Phase 0 - AI Narrative Generator

Takes a metrics dict (from risk_metrics.compute_all_metrics) and asks an LLM
to write a plain-English risk narrative: what the numbers mean, what stands out,
and what a reasonable investor should watch for. No investment advice/recommendations
in the "should you buy" sense - narrative and education only.

Provider is swappable: Groq (free, for development) or Anthropic (paid, for
production-quality client-facing reports later). Set PROVIDER below or via .env.

Requires in .env:
  GROQ_API_KEY=...       (get one free at https://console.groq.com)
  ANTHROPIC_API_KEY=...  (only needed if PROVIDER="anthropic")
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Swap this to "anthropic" later for production-quality client reports.
# Can also be overridden via .env: LLM_PROVIDER=anthropic
PROVIDER = os.environ.get("LLM_PROVIDER", "groq")

GROQ_MODEL = "openai/gpt-oss-120b"   # stronger of your two Groq defaults; use -20b if you want faster/cheaper
ANTHROPIC_MODEL = "claude-sonnet-5"

SYSTEM_PROMPT_EN = (
    "You are a risk analyst writing a concise narrative summary for an investment "
    "risk report. You are given computed quantitative risk metrics for a single "
    "asset. Write 3-4 short paragraphs covering: (1) overall risk/return profile "
    "in plain English, (2) what the volatility and drawdown figures imply about "
    "the ride an investor should expect, (3) what the VaR/CVaR figures mean in "
    "concrete terms (translate the daily percentage into what it means for a "
    "realistic position size), (4) how this asset's risk compares to the broader "
    "market via beta, if provided. Be precise and grounded in the numbers given - "
    "do not invent facts about the company, its business, or recent news you were "
    "not given. Do not give buy/sell/hold recommendations; this is risk narrative "
    "only, not investment advice. Keep it tight and readable, no bullet lists. "
    "Budget your length so all four points are fully covered, including the beta "
    "comparison at the end - do not run out of room before addressing beta. "
    "Aim for roughly 350-450 words total. Write your entire response in English."
)

SYSTEM_PROMPT_AR = (
    "أنت محلل مخاطر تكتب ملخصاً سردياً موجزاً لتقرير مخاطر استثمارية. "
    "تُعطى مقاييس مخاطر كمية محسوبة لأصل واحد. اكتب 3-4 فقرات قصيرة تغطي: "
    "(1) ملف المخاطر والعائد بشكل عام بلغة واضحة، (2) ماذا تعني أرقام التقلب "
    "والانخفاض الأقصى بالنسبة لما يجب أن يتوقعه المستثمر، (3) ماذا تعني أرقام "
    "القيمة المعرضة للخطر (VaR) والخسارة المتوقعة (CVaR) بشكل ملموس (حوّل النسبة "
    "اليومية إلى ما تعنيه لحجم مركز واقعي)، (4) كيف تقارن مخاطر هذا الأصل بالسوق "
    "الأوسع من خلال معامل بيتا، إن وُجد. كن دقيقاً ومستنداً إلى الأرقام المعطاة - "
    "لا تختلق حقائق عن الشركة أو نشاطها أو أي أخبار حديثة لم تُعطَ لك. لا تقدم "
    "توصيات شراء أو بيع أو احتفاظ؛ هذا سرد للمخاطر فقط وليس نصيحة استثمارية. "
    "اجعله موجزاً وسهل القراءة، بدون قوائم نقطية. وزّع طول النص بحيث تُغطى جميع "
    "النقاط الأربع بالكامل، بما في ذلك مقارنة بيتا في النهاية. استهدف حوالي "
    "350-450 كلمة إجمالاً. اكتب ردك بالكامل باللغة العربية الفصحى."
)

PORTFOLIO_SYSTEM_PROMPT_EN = (
    "You are a portfolio risk analyst writing a concise narrative summary for a "
    "multi-asset portfolio risk report. You are given the portfolio's combined "
    "risk/return metrics, each holding's weight and individual volatility, the "
    "correlation matrix between holdings, and a diversification benefit figure. "
    "Write 3-4 short paragraphs covering: (1) the portfolio's overall risk/return "
    "profile, (2) what the correlation matrix reveals about how the holdings move "
    "together or independently - name which pairs are highly correlated (weak "
    "diversification between them) and which are not (strong diversification "
    "between them), (3) what the diversification benefit percentage means in "
    "plain terms - how much lower the portfolio's volatility is than a naive "
    "sum of its parts would suggest, (4) what the VaR/CVaR figures mean for a "
    "realistic position size. Be precise and grounded only in the numbers given - "
    "do not invent facts about any company. Do not give buy/sell/hold "
    "recommendations or suggest reweighting the portfolio; this is risk "
    "narrative only. Keep it tight and readable, no bullet lists. Aim for "
    "roughly 350-450 words. Write your entire response in English."
)

PORTFOLIO_SYSTEM_PROMPT_AR = (
    "أنت محلل مخاطر محافظ استثمارية تكتب ملخصاً سردياً موجزاً لتقرير مخاطر "
    "محفظة متعددة الأصول. تُعطى مقاييس المخاطر والعائد المجمعة للمحفظة، ووزن "
    "كل أصل وتقلبه الفردي، ومصفوفة الارتباط بين الأصول، ورقم فائدة التنويع. "
    "اكتب 3-4 فقرات قصيرة تغطي: (1) ملف المخاطر والعائد العام للمحفظة، "
    "(2) ماذا تكشف مصفوفة الارتباط عن كيفية تحرك الأصول معاً أو بشكل مستقل - "
    "اذكر أي الأزواج مرتبطة بشكل كبير (تنويع ضعيف بينها) وأيها غير مرتبطة "
    "(تنويع قوي بينها)، (3) ماذا تعني نسبة فائدة التنويع بشكل عملي - كم "
    "انخفض تقلب المحفظة مقارنة بما كان سيوحي به مجموع بسيط لأجزائها، "
    "(4) ماذا تعني أرقام القيمة المعرضة للخطر لحجم مركز واقعي. كن دقيقاً "
    "ومستنداً فقط إلى الأرقام المعطاة - لا تختلق حقائق عن أي شركة. لا تقدم "
    "توصيات شراء أو بيع أو إعادة توزيع المحفظة؛ هذا سرد للمخاطر فقط. اجعله "
    "موجزاً وسهل القراءة، بدون قوائم نقطية. استهدف حوالي 350-450 كلمة. "
    "اكتب ردك بالكامل باللغة العربية الفصحى."
)


def format_metrics_for_prompt(ticker: str, metrics: dict) -> str:
    """Turn the raw metrics dict into a clean text block for the prompt."""
    lines = [
        f"Ticker: {ticker}",
        f"Period: {metrics['period_start'].date()} to {metrics['period_end'].date()} "
        f"({metrics['trading_days']} trading days)",
        f"Current price: ${metrics['current_price']:.2f}",
        f"Annualized return: {metrics['annualized_return']*100:.2f}%",
        f"Annualized volatility: {metrics['annualized_volatility']*100:.2f}%",
        f"Sharpe ratio: {metrics['sharpe_ratio']:.2f}",
        f"Sortino ratio: {metrics['sortino_ratio']:.2f}",
        f"Max drawdown: {metrics['max_drawdown']*100:.2f}%",
        f"Value at Risk (95% daily): {metrics['var_95']*100:.2f}%",
        f"Value at Risk (99% daily): {metrics['var_99']*100:.2f}%",
        f"Conditional VaR / Expected Shortfall (95%): {metrics['cvar_95']*100:.2f}%",
    ]
    if "beta" in metrics:
        lines.append(f"Beta (vs benchmark): {metrics['beta']:.2f}")
    return "\n".join(lines)


def _call_groq(system_prompt: str, user_prompt: str) -> str:
    from groq import Groq

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=1000,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


# def _call_anthropic(system_prompt: str, user_prompt: str) -> str:
#     import anthropic
#
#     client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
#     response = client.messages.create(
#         model=ANTHROPIC_MODEL,
#         max_tokens=1000,
#         system=system_prompt,
#         messages=[{"role": "user", "content": user_prompt}],
#     )
#     return response.content[0].text


def generate_risk_narrative(ticker: str, metrics: dict, language: str = "en") -> str:
    """Call the configured LLM provider to generate a risk narrative from the metrics.

    language: "en" or "ar" - selects the system prompt and output language.
    """
    metrics_block = format_metrics_for_prompt(ticker, metrics)
    user_prompt = f"Here are the computed risk metrics:\n\n{metrics_block}\n\nWrite the risk narrative."

    system_prompt = SYSTEM_PROMPT_AR if language == "ar" else SYSTEM_PROMPT_EN

    if PROVIDER == "groq":
        return _call_groq(system_prompt, user_prompt)
    elif PROVIDER == "anthropic":
        # return _call_anthropic(system_prompt, user_prompt)
        return ""
    else:
        raise ValueError(f"Unknown PROVIDER '{PROVIDER}'. Use 'groq' or 'anthropic'.")


def format_portfolio_metrics_for_prompt(tickers: list, weights: dict, metrics: dict) -> str:
    """Turn portfolio-level metrics into a clean text block for the prompt."""
    lines = [
        f"Holdings: {', '.join(tickers)}",
        f"Weights: {', '.join(f'{t} {weights[t]*100:.0f}%' for t in tickers)}",
        f"Period: {metrics['period_start'].date()} to {metrics['period_end'].date()} "
        f"({metrics['trading_days']} trading days)",
        f"Portfolio annualized return: {metrics['annualized_return']*100:.2f}%",
        f"Portfolio annualized volatility: {metrics['annualized_volatility']*100:.2f}%",
        f"Portfolio Sharpe ratio: {metrics['sharpe_ratio']:.2f}",
        f"Portfolio Sortino ratio: {metrics['sortino_ratio']:.2f}",
        f"Portfolio max drawdown: {metrics['max_drawdown']*100:.2f}%",
        f"Portfolio VaR (95% daily): {metrics['var_95']*100:.2f}%",
        f"Portfolio VaR (99% daily): {metrics['var_99']*100:.2f}%",
        f"Portfolio CVaR (95%): {metrics['cvar_95']*100:.2f}%",
        f"Diversification benefit: {metrics['diversification_benefit']*100:.2f}%",
        "",
        "Individual holding volatilities (annualized):",
    ]
    for t in tickers:
        lines.append(f"  {t}: {metrics['individual_volatilities'][t]*100:.2f}%")

    lines.append("")
    lines.append("Correlation matrix:")
    corr = metrics["correlation_matrix"]
    for i, t1 in enumerate(tickers):
        for t2 in tickers[i + 1:]:
            lines.append(f"  {t1}-{t2}: {corr.loc[t1, t2]:.3f}")

    return "\n".join(lines)


def generate_portfolio_narrative(tickers: list, weights: dict, metrics: dict, language: str = "en") -> str:
    """Call the configured LLM provider to generate a portfolio-level risk narrative."""
    metrics_block = format_portfolio_metrics_for_prompt(tickers, weights, metrics)
    user_prompt = f"Here are the computed portfolio risk metrics:\n\n{metrics_block}\n\nWrite the portfolio risk narrative."

    system_prompt = PORTFOLIO_SYSTEM_PROMPT_AR if language == "ar" else PORTFOLIO_SYSTEM_PROMPT_EN

    if PROVIDER == "groq":
        return _call_groq(system_prompt, user_prompt)
    elif PROVIDER == "anthropic":
        # return _call_anthropic(system_prompt, user_prompt)
        return ""
    else:
        raise ValueError(f"Unknown PROVIDER '{PROVIDER}'. Use 'groq' or 'anthropic'.")


if __name__ == "__main__":
    # Standalone test using hardcoded sample metrics (mirrors real AAPL output
    # from the data_fetcher test run) so this piece can be tested independently.
    import pandas as pd

    sample_metrics = {
        "annualized_return": 0.2773,
        "annualized_volatility": 0.2838,
        "sharpe_ratio": 0.72,
        "sortino_ratio": 0.98,
        "max_drawdown": -0.3336,
        "var_95": -0.0278,
        "var_99": -0.0485,
        "cvar_95": -0.0415,
        "beta": 1.10,
        "current_price": 333.74,
        "period_start": pd.Timestamp("2024-07-18"),
        "period_end": pd.Timestamp("2026-07-17"),
        "trading_days": 501,
    }

    print(f"Generating narrative for AAPL sample metrics (provider: {PROVIDER})...\n")
    narrative = generate_risk_narrative("AAPL", sample_metrics)
    print("=" * 60)
    print("AI RISK NARRATIVE")
    print("=" * 60)
    print(narrative)