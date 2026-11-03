"use client";

import { useState, useEffect } from "react";
import {
  fetchReport, fetchPortfolioReport, fetchStressTest,
  savePortfolio, listSavedPortfolios, deleteSavedPortfolio,
  ReportResponse, PortfolioReportResponse, StressTestResponse, SavedPortfolio, ApiError,
} from "@/lib/api";
import {
  computeRiskScore,
  formatPercent,
  formatSignedPercent,
  formatPrice,
  toneForReturn,
  toneForSharpe,
} from "@/lib/risk";
import { Lang, getTranslation } from "@/lib/i18n";
import { useAuth } from "@/lib/useAuth";
import { TickerSearch } from "@/components/TickerSearch";
import { MetricCard } from "@/components/MetricCard";
import { RiskBar } from "@/components/RiskBar";
import { NarrativePanel } from "@/components/NarrativePanel";
import { LanguageToggle } from "@/components/LanguageToggle";
import { PortfolioBuilder } from "@/components/PortfolioBuilder";
import { CorrelationHeatmap } from "@/components/CorrelationHeatmap";
import { ScenarioChart } from "@/components/ScenarioChart";
import { AuthPanel } from "@/components/AuthPanel";
import { SavedPortfoliosList } from "@/components/SavedPortfoliosList";

type Mode = "single" | "portfolio";

export default function Home() {
  const [lang, setLang] = useState<Lang>("en");
  const [mode, setMode] = useState<Mode>("single");
  const { user, accessToken, signIn, signUp, signOut } = useAuth();

  const [savedPortfolios, setSavedPortfolios] = useState<SavedPortfolio[]>([]);
  const [loadedHoldings, setLoadedHoldings] = useState<{ ticker: string; weight: number }[] | undefined>(undefined);
  const [builderKey, setBuilderKey] = useState(0);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [portfolioReport, setPortfolioReport] = useState<PortfolioReportResponse | null>(null);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioError, setPortfolioError] = useState<string | null>(null);
  const [lastHoldings, setLastHoldings] = useState<{ ticker: string; weight: number }[] | null>(null);

  const [stressTest, setStressTest] = useState<StressTestResponse | null>(null);
  const [stressTestLoading, setStressTestLoading] = useState(false);
  const [stressTestError, setStressTestError] = useState<string | null>(null);

  const t = getTranslation(lang);

  useEffect(() => {
    if (accessToken) {
      listSavedPortfolios(accessToken).then(setSavedPortfolios).catch(() => setSavedPortfolios([]));
    } else {
      setSavedPortfolios([]);
    }
  }, [accessToken]);

  async function handleSavePortfolio() {
    if (!accessToken || !lastHoldings) return;
    setSaveStatus(null);
    try {
      const name = `${lastHoldings.map((h) => h.ticker).join(" + ")}`;
      await savePortfolio(name, lastHoldings, accessToken);
      setSaveStatus(t.portfolioSaved);
      const updated = await listSavedPortfolios(accessToken);
      setSavedPortfolios(updated);
    } catch (e) {
      setSaveStatus(e instanceof ApiError ? e.message : t.errorNoBackend);
    }
  }

  function handleLoadSavedPortfolio(p: SavedPortfolio) {
    setLoadedHoldings(p.holdings);
    setBuilderKey((k) => k + 1); // force PortfolioBuilder to remount with new initial values
  }

  async function handleDeleteSavedPortfolio(id: number) {
    if (!accessToken) return;
    try {
      await deleteSavedPortfolio(id, accessToken);
      setSavedPortfolios((prev) => prev.filter((p) => p.id !== id));
    } catch {
      // silently ignore - list will just still show it, user can retry
    }
  }

  async function handleSearch(ticker: string) {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReport(ticker, lang);
      setReport(data);
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.status === 404 ? t.errorNoData(ticker) : e.message);
      } else {
        setError(t.errorNoBackend);
      }
      setReport(null);
    } finally {
      setLoading(false);
    }
  }

  async function handlePortfolioSubmit(holdings: { ticker: string; weight: number }[]) {
    setPortfolioLoading(true);
    setPortfolioError(null);
    setStressTest(null);
    setStressTestError(null);
    try {
      const data = await fetchPortfolioReport(holdings, lang);
      setPortfolioReport(data);
      setLastHoldings(holdings);
    } catch (e) {
      if (e instanceof ApiError) {
        setPortfolioError(e.message);
      } else {
        setPortfolioError(t.errorNoBackend);
      }
      setPortfolioReport(null);
    } finally {
      setPortfolioLoading(false);
    }
  }

  async function handleRunStressTest() {
    if (!lastHoldings) return;
    setStressTestLoading(true);
    setStressTestError(null);
    try {
      const data = await fetchStressTest(lastHoldings);
      setStressTest(data);
    } catch (e) {
      if (e instanceof ApiError) {
        setStressTestError(e.message);
      } else {
        setStressTestError(t.errorNoBackend);
      }
      setStressTest(null);
    } finally {
      setStressTestLoading(false);
    }
  }

  return (
    <div className="min-h-screen relative" dir={t.dir}>
      <div className="instrument-bg absolute inset-0 h-[600px] pointer-events-none" />

      <div className="relative max-w-5xl mx-auto px-6 py-16">
        <header className="mb-10">
          <div className="flex items-start justify-between gap-4 mb-1">
            <div className="flex items-baseline gap-3">
              <h1 className="text-2xl font-semibold tracking-tight">{t.title}</h1>
              <span className="font-mono text-xs text-muted-dim uppercase tracking-widest">
                {t.subtitle}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <AuthPanel
                user={user}
                onSignIn={signIn}
                onSignUp={signUp}
                onSignOut={signOut}
                labels={{
                  signIn: t.signIn,
                  signUp: t.signUp,
                  signOut: t.signOut,
                  email: t.email,
                  password: t.password,
                  createAccount: t.createAccount,
                  alreadyHaveAccount: t.alreadyHaveAccount,
                  checkEmailToConfirm: t.checkEmailToConfirm,
                }}
              />
              <LanguageToggle lang={lang} onChange={setLang} />
            </div>
          </div>
          <p className="text-muted text-sm mb-6">{t.tagline}</p>

          <div className="inline-flex rounded-md border border-hairline bg-panel overflow-hidden text-sm mb-5">
            <button
              onClick={() => setMode("single")}
              className={`px-4 py-2 transition-colors ${
                mode === "single" ? "bg-panel-raised text-signal-amber" : "text-muted hover:text-ink"
              }`}
            >
              {t.singleAsset}
            </button>
            <button
              onClick={() => setMode("portfolio")}
              className={`px-4 py-2 transition-colors ${
                mode === "portfolio" ? "bg-panel-raised text-signal-amber" : "text-muted hover:text-ink"
              }`}
            >
              {t.portfolio}
            </button>
          </div>

          {mode === "single" && (
            <TickerSearch
              onSearch={handleSearch}
              loading={loading}
              placeholder={t.searchPlaceholder}
              buttonText={t.analyze}
              loadingText={t.analyzing}
            />
          )}
        </header>

        {mode === "single" && (
          <>
            {error && (
              <div className="mb-8 px-4 py-3 rounded-md bg-signal-amber-dim/40 border border-signal-amber/30 text-sm text-signal-amber">
                {error}
              </div>
            )}

            {!report && !loading && !error && (
              <div className="text-muted-dim text-sm border border-dashed border-hairline rounded-lg px-6 py-12 text-center">
                {t.emptyState}
              </div>
            )}

            {loading && (
              <div className="text-muted text-sm border border-hairline rounded-lg px-6 py-12 text-center font-mono">
                {t.loadingState}
              </div>
            )}

            {report && !loading && (
              <div className="space-y-6">
                <div className="flex items-baseline justify-between">
                  <div>
                    <h2 className="text-3xl font-mono font-semibold">{report.resolved_ticker}</h2>
                    {report.resolved_ticker !== report.ticker && (
                      <p className="text-muted-dim text-xs mt-0.5 font-mono">
                        {t.resolvedAs} {report.resolved_ticker}
                      </p>
                    )}
                    <p className="text-muted text-sm mt-0.5">
                      {report.metrics.period_start} — {report.metrics.period_end} ·{" "}
                      {report.metrics.trading_days} {t.tradingDays}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-3xl font-mono font-semibold">
                      {formatPrice(report.metrics.current_price, report.metrics.currency)}
                    </span>
                  </div>
                </div>

                <div className="bg-panel border border-hairline rounded-lg p-5">
                  <RiskBar
                    score={computeRiskScore(report.metrics)}
                    labels={{
                      riskPosition: t.riskPosition,
                      lowerRisk: t.lowerRisk,
                      moderateRisk: t.moderateRisk,
                      elevatedRisk: t.elevatedRisk,
                      low: t.low,
                      moderate: t.moderate,
                      elevated: t.elevated,
                    }}
                  />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <MetricCard
                    label={t.annualizedReturn}
                    value={formatSignedPercent(report.metrics.annualized_return)}
                    tone={toneForReturn(report.metrics.annualized_return)}
                  />
                  <MetricCard label={t.volatility} value={formatPercent(report.metrics.annualized_volatility)} />
                  <MetricCard
                    label={t.sharpeRatio}
                    value={report.metrics.sharpe_ratio.toFixed(2)}
                    tone={toneForSharpe(report.metrics.sharpe_ratio)}
                  />
                  <MetricCard label={t.sortinoRatio} value={report.metrics.sortino_ratio.toFixed(2)} />
                  <MetricCard
                    label={t.maxDrawdown}
                    value={formatPercent(report.metrics.max_drawdown)}
                    tone="amber"
                  />
                  <MetricCard
                    label={t.var95}
                    value={formatPercent(report.metrics.var_95)}
                    detail={`${t.cvar}: ${formatPercent(report.metrics.cvar_95)}`}
                  />
                  <MetricCard label={t.var99} value={formatPercent(report.metrics.var_99)} />
                  {report.metrics.beta !== null && (
                    <MetricCard
                      label={`${t.betaVs} ${report.benchmark}`}
                      value={report.metrics.beta.toFixed(2)}
                    />
                  )}
                </div>

                <NarrativePanel narrative={report.narrative} provider={report.llm_provider} heading={t.riskNarrative} />

                <p className="text-xs text-muted-dim text-center pt-4">{t.disclaimer}</p>
              </div>
            )}
          </>
        )}

        {mode === "portfolio" && (
          <div className="space-y-6">
            <PortfolioBuilder
              key={builderKey}
              initialHoldings={loadedHoldings}
              onSubmit={handlePortfolioSubmit}
              loading={portfolioLoading}
              labels={{
                holdings: t.holdings,
                ticker: t.ticker,
                weight: t.weight,
                addHolding: t.addHolding,
                remove: t.remove,
                totalWeight: t.totalWeight,
                weightsMustSumTo100: t.weightsMustSumTo100,
                analyzePortfolio: t.analyzePortfolio,
                analyzing: t.analyzing,
              }}
            />

            {user ? (
              <SavedPortfoliosList
                portfolios={savedPortfolios}
                onLoad={handleLoadSavedPortfolio}
                onDelete={handleDeleteSavedPortfolio}
                labels={{
                  heading: t.savedPortfolios,
                  load: t.load,
                  delete: t.delete,
                  empty: t.noSavedPortfolios,
                }}
              />
            ) : (
              <div className="text-xs text-muted-dim text-center">{t.signInToSave}</div>
            )}

            {portfolioError && (
              <div className="px-4 py-3 rounded-md bg-signal-amber-dim/40 border border-signal-amber/30 text-sm text-signal-amber">
                {portfolioError}
              </div>
            )}

            {!portfolioReport && !portfolioLoading && !portfolioError && (
              <div className="text-muted-dim text-sm border border-dashed border-hairline rounded-lg px-6 py-12 text-center">
                {t.portfolioEmptyState}
              </div>
            )}

            {portfolioLoading && (
              <div className="text-muted text-sm border border-hairline rounded-lg px-6 py-12 text-center font-mono">
                {t.loadingState}
              </div>
            )}

            {portfolioReport && !portfolioLoading && (
              <>
                <div>
                  <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-mono font-semibold">
                      {portfolioReport.tickers.join(" + ")}
                    </h2>
                    {user ? (
                      <button
                        onClick={handleSavePortfolio}
                        className="px-4 py-2 rounded-md bg-panel-raised border border-hairline text-sm font-medium
                                   text-ink hover:border-signal-amber/50 hover:text-signal-amber transition-colors"
                      >
                        {t.savePortfolio}
                      </button>
                    ) : (
                      <span className="text-xs text-muted-dim">{t.signInToSave}</span>
                    )}
                  </div>
                  <p className="text-muted text-sm mt-0.5">
                    {portfolioReport.metrics.period_start} — {portfolioReport.metrics.period_end} ·{" "}
                    {portfolioReport.metrics.trading_days} {t.tradingDays}
                  </p>
                  {saveStatus && <p className="text-xs text-signal-green mt-1">{saveStatus}</p>}
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <MetricCard
                    label={t.annualizedReturn}
                    value={formatSignedPercent(portfolioReport.metrics.annualized_return)}
                    tone={toneForReturn(portfolioReport.metrics.annualized_return)}
                  />
                  <MetricCard
                    label={t.volatility}
                    value={formatPercent(portfolioReport.metrics.annualized_volatility)}
                  />
                  <MetricCard
                    label={t.sharpeRatio}
                    value={portfolioReport.metrics.sharpe_ratio.toFixed(2)}
                    tone={toneForSharpe(portfolioReport.metrics.sharpe_ratio)}
                  />
                  <MetricCard label={t.sortinoRatio} value={portfolioReport.metrics.sortino_ratio.toFixed(2)} />
                  <MetricCard
                    label={t.maxDrawdown}
                    value={formatPercent(portfolioReport.metrics.max_drawdown)}
                    tone="amber"
                  />
                  <MetricCard
                    label={t.var95}
                    value={formatPercent(portfolioReport.metrics.var_95)}
                    detail={`${t.cvar}: ${formatPercent(portfolioReport.metrics.cvar_95)}`}
                  />
                  <MetricCard label={t.var99} value={formatPercent(portfolioReport.metrics.var_99)} />
                  <MetricCard
                    label={t.diversificationBenefit}
                    value={formatPercent(portfolioReport.metrics.diversification_benefit)}
                    tone={portfolioReport.metrics.diversification_benefit > 0.1 ? "green" : "neutral"}
                  />
                </div>

                <CorrelationHeatmap
                  tickers={portfolioReport.tickers}
                  matrix={portfolioReport.metrics.correlation_matrix}
                  heading={t.correlationMatrix}
                />

                <div className="bg-panel border border-hairline rounded-lg p-5">
                  <button
                    onClick={handleRunStressTest}
                    disabled={stressTestLoading}
                    className="px-5 py-2.5 rounded-md bg-panel-raised border border-hairline text-sm font-medium
                               text-ink hover:border-signal-amber/50 hover:text-signal-amber
                               disabled:opacity-40 transition-colors"
                  >
                    {stressTestLoading ? t.runningStressTest : t.runStressTest}
                  </button>
                </div>

                {stressTestError && (
                  <div className="px-4 py-3 rounded-md bg-signal-amber-dim/40 border border-signal-amber/30 text-sm text-signal-amber">
                    {stressTestError}
                  </div>
                )}

                {stressTest && !stressTestLoading && (
                  <ScenarioChart
                    scenarios={stressTest.scenarios}
                    labels={{
                      heading: t.stressTestHeading,
                      market_crash: t.market_crash,
                      correction: t.correction,
                      rate_hike_shock: t.rate_hike_shock,
                      rally: t.rally,
                      historical_worst_day: t.historical_worst_day,
                      custom: t.custom,
                    }}
                  />
                )}

                <NarrativePanel
                  narrative={portfolioReport.narrative}
                  provider={portfolioReport.llm_provider}
                  heading={t.riskNarrative}
                />

                <p className="text-xs text-muted-dim text-center pt-4">{t.disclaimer}</p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}