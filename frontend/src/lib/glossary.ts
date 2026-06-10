// Plain-language explanations for the "?" info links scattered through the
// UI. Keep entries short (2-3 paragraphs) and free of jargon where possible —
// the audience is FIRE-curious readers, not quants.

export interface GlossaryEntry {
  title: string;
  body: string[];
}

const NOT_ADVICE = "Educational tool, not personalized financial advice.";

export const GLOSSARY: Record<string, GlossaryEntry> = {
  "method-historical": {
    title: "Historical simulation",
    body: [
      "This method replays real overlapping windows from market history — the same approach used by the Trinity Study and cFIREsim. For a 30-year retirement, it checks: \"if you'd retired in 1955, would your money have lasted? What about 1956? 1957?\" ...and so on for every starting month in the dataset.",
      "The big advantage is realism: real crashes, recoveries, and the way good and bad years cluster together (autocorrelation) are all baked in. The downside is sample size — about 150 years of data means only a few truly independent 30-year periods, since neighboring windows overlap heavily and share most of their years.",
      NOT_ADVICE,
    ],
  },
  "method-montecarlo": {
    title: "Monte Carlo simulation",
    body: [
      "Instead of replaying real history, Monte Carlo generates thousands of simulated markets using the statistical properties (average return, volatility, correlation) of historical stock and bond returns. This gives smooth probability curves and effectively unlimited scenarios.",
      "The tradeoff: depending on the return model used, simulated markets may not behave like real ones after a crash. A simple model can be too optimistic (no \"hangover\" after a crash) or too pessimistic (recombined sequences worse than anything that's actually happened). See the Monte Carlo return model explainer for details on the two modes available here.",
      NOT_ADVICE,
    ],
  },
  "method-cape": {
    title: "CAPE-adjusted withdrawal rate",
    body: [
      "This method looks at today's market valuation — specifically the CAPE ratio (Cyclically-Adjusted Price/Earnings) — and suggests a withdrawal rate based on the historical relationship between starting valuations and what turned out to be sustainable.",
      "The intuition: when the market is expensive relative to long-run earnings, future returns have historically tended to be lower, so a lower withdrawal rate has historically been safer. This is a statistical tendency from the past, not a prediction.",
      NOT_ADVICE,
    ],
  },
  "method-compare": {
    title: "Compare all methods",
    body: [
      "This runs historical simulation, Monte Carlo, and the CAPE-adjusted rate side-by-side for the same scenario, so you can see where they agree and where they diverge.",
      "Agreement across methods is a (mild) signal that a result isn't an artifact of one particular approach. Divergence is informative too — it usually points to assumptions (like sequence-of-returns risk or current valuations) that matter a lot for your specific scenario.",
      NOT_ADVICE,
    ],
  },
  "withdrawal-strategy": {
    title: "Withdrawal strategies",
    body: [
      "Fixed (inflation-adjusted): the classic \"4% rule\" approach. Withdraw the same inflation-adjusted dollar amount every year, regardless of how the portfolio is doing. Simple and predictable, but doesn't respond to a market downturn.",
      "Guyton-Klinger guardrails: starts like the fixed strategy, but adjusts spending up or down when the withdrawal rate (withdrawal ÷ current balance) drifts outside upper/lower \"guardrail\" bands. Cutting spending in bad years is what allows a higher starting withdrawal rate to be sustainable.",
      "Constant percentage: always withdraw a fixed percentage of the *current* balance, recalculated each year. Mathematically this never truly hits zero — but your income rises and falls directly with the market, which can mean large swings in spending.",
      NOT_ADVICE,
    ],
  },
  "mc-mode": {
    title: "Monte Carlo return models",
    body: [
      "Lognormal: draws independent random monthly returns from a distribution fit to historical stock/bond statistics. Fast and smooth, but each month is independent — the model has no \"memory\" of recent performance, so it doesn't reproduce the way real markets tend to mean-revert after big moves.",
      "Block bootstrap: instead of drawing single months, this resamples whole chunks (blocks) of real historical months and stitches them together. This preserves some short-term patterns within each block, but recombining blocks from different eras can create sequences that are worse (or better) than anything that has actually happened historically.",
      NOT_ADVICE,
    ],
  },
  "success-rate": {
    title: "Success rate",
    body: [
      "The percentage of simulated (or historical) scenarios in which the portfolio lasted the entire time horizon without running out of money.",
      "This is a model output based on past data and assumptions — not a guarantee or a probability of your personal future. A 95% success rate means 5% of the runs in this particular dataset/model ran out of money before the end of the horizon, often during the worst historical periods (e.g. retiring right before a major crash).",
      NOT_ADVICE,
    ],
  },
  "percentile-bands": {
    title: "Percentile bands (fan chart)",
    body: [
      "Each line on this chart shows what your portfolio balance would be at that percentile, across all the simulated/historical runs, at each point in time.",
      "The p50 (median) line is the \"typical\" outcome. The p5 line shows roughly the 1-in-20 \"bad luck\" outcome — only 5% of runs ended up below it. The p95 line is the \"good luck\" outcome. The wider the gap between the bands, the more uncertain the outcome is.",
      NOT_ADVICE,
    ],
  },
  "sequence-risk": {
    title: "Sequence-of-returns risk",
    body: [
      "Two retirees can experience the exact same average return over 30 years and end up with very different outcomes — because the *order* the returns happen in matters enormously once you start withdrawing money.",
      "If a portfolio drops sharply in the first few years of retirement, you're forced to sell more shares at low prices to fund withdrawals, leaving fewer shares to participate in the eventual recovery. The same drop happening in year 25 instead of year 1 does much less damage, because the portfolio is no longer (or less) dependent on those shares.",
      "This chart colors each historical retirement-start date by its early-period return, so you can see the pattern directly: weak early returns (red) cluster toward worse outcomes, even when later returns were strong.",
      NOT_ADVICE,
    ],
  },
  "cape-ratio": {
    title: "CAPE ratio",
    body: [
      "CAPE stands for Cyclically-Adjusted Price-to-Earnings ratio (also called the Shiller P/E). It compares the current stock market price to the average of the last 10 years of inflation-adjusted earnings, smoothing out short-term swings in profits.",
      "A high CAPE means stocks are expensive relative to long-run earnings; a low CAPE means they're cheap. Historically, starting retirement when CAPE was high has correlated with lower sustainable withdrawal rates over the following decades — which is the relationship the CAPE-adjusted method uses.",
      NOT_ADVICE,
    ],
  },
};
