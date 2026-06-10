# Monte Carlo vs. Historical: Baseline Comparison

`fire_sim.engine.compare` runs three baseline scenarios through all three
engines: the rolling-window historical simulator, lognormal Monte Carlo,
and block-bootstrap Monte Carlo (12-month blocks). Reproduce with:

```bash
python -m fire_sim.engine.compare
```

Results below: historical engine uses all 1,473 rolling 30-year windows in
the Shiller dataset; Monte Carlo runs use 50,000 paths, seed 42.

## Success rate

| Scenario | Historical | Lognormal MC | Block Bootstrap |
|---|---:|---:|---:|
| 60/40, 4%, 30yr | 96.9% | 97.6% | 92.2% |
| 100/0, 4%, 30yr | 97.9% | 95.5% | 89.3% |
| 60/40, 5%, 30yr | 75.6% | 86.6% | 78.7% |

## Ending balance percentiles (multiple of starting balance)

| Scenario | p5 (Hist / LN / BB) | p50 (Hist / LN / BB) | p95 (Hist / LN / BB) |
|---|---|---|---|
| 60/40, 4%, 30yr | 0.20 / 0.19 / 0.00 | 1.25 / 1.85 / 1.80 | 4.85 / 5.92 / 7.89 |
| 100/0, 4%, 30yr | 0.34 / 0.04 / 0.00 | 3.08 / 3.44 / 3.31 | 7.89 / 16.86 / 23.90 |
| 60/40, 5%, 30yr | 0.00 / 0.00 / 0.00 | 0.67 / 1.12 / 1.07 | 4.00 / 4.72 / 6.48 |

## Why they diverge

**Lognormal MC** draws i.i.d. monthly returns from a fitted joint normal
distribution (on log(1+r)), preserving the historical mean, variance, and
stock/bond correlation — but nothing else. It has no memory: a bad year is
never followed by a *correlated* recovery or a *correlated* continuation of
the bad regime, because each month is drawn independently.

This mostly shows up as **missing time diversification / mean reversion**.
Real markets exhibit valuation-driven mean reversion (the basis of the
upcoming CAPE-based withdrawal epic) — a decade like 1966-1982 of poor real
returns was, historically, partly "paid back" by the recovery that followed.
I.i.d. sampling can't reproduce that structure, so the *variance of
cumulative 30-year returns* is higher than history's. Two visible effects:

- For higher withdrawal rates (5% case), lognormal MC is **too optimistic**
  (86.6% vs. historical 75.6%) — without realistic multi-year drawdown
  persistence, fewer simulated retirements get caught in a sustained bad
  stretch.
- For 100% stocks, lognormal MC produces a **much worse 5th-percentile
  outcome** (0.04 vs. historical 0.34) and a **much better 95th
  percentile** (16.86 vs. 7.89) — i.i.d. compounding over 360 months
  produces more extreme cumulative outcomes in both directions than the
  historically-correlated path ever did.

**Block bootstrap** resamples real 12-month blocks, which preserves
within-year seasonality and stock/bond correlation — but randomly
recombining blocks **across years destroys longer-horizon structure**.
A real "1973-74 crash" block can be randomly followed by another
crash-like block drawn from a completely different decade, producing
back-to-back-bad-year sequences that never happened historically. This
is why block bootstrap consistently has the **lowest success rates and the
worst (often zero) 5th-percentile outcomes** across all three scenarios —
new "worse than ever happened" sequences become possible, and because
failure (balance hits zero) is an absorbing floor, those new failures
aren't offset by the new "better than ever happened" sequences that also
become possible (visible in block bootstrap's consistently highest p95).

## Takeaways

- The **historical engine remains the primary reference** — it reflects
  what actually happened, including real mean-reversion dynamics, and
  should be the default for headline numbers.
- **Lognormal MC** is a reasonable approximation near the historical
  baseline (60/40, 4%) but becomes systematically too optimistic as
  withdrawal rates rise — useful as an "if regimes don't persist" sensitivity
  check, not a primary estimate.
- **Block bootstrap** is systematically more conservative — useful as a
  "what if a worse sequence than any single historical one occurs" stress
  test.
- Neither Monte Carlo mode is a substitute for the historical engine; both
  are complementary sensitivity lenses. This divergence — particularly
  lognormal MC's blindness to valuation-driven mean reversion — is part of
  the motivation for the next epic, **CAPE-Based Dynamic Withdrawal**.
