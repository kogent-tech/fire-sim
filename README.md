# fire-sim

A self-hosted, open-source Safe Withdrawal Rate (SWR) / retirement Monte
Carlo simulation engine. Combines historical simulation (Trinity Study /
cFIREsim style rolling windows) with Monte Carlo simulation and CAPE-based
dynamic withdrawal strategies (ERN methodology), exposed via a stateless API
and a web frontend.

**Status:** pre-alpha — core simulation engine in development.

## Why

cFIREsim and FIRECalc are closed-source and not self-hostable or API-driven.
Portfolio Visualizer's Monte Carlo tooling is paid for the useful bits.
Nothing currently combines historical sim + Monte Carlo + CAPE-based dynamic
withdrawal in one open, API-first, self-hostable tool.

## Architecture

```
Frontend (React/Astro)  ->  FastAPI backend (/simulate)  ->  Compute engine (numpy/pandas)
                                                                |
                                                          Shiller dataset (1871-present)
```

- **Two simulation methods, not one** — pure Monte Carlo underestimates
  sequence risk (ignores autocorrelation); historical sim has only ~150
  years of overlapping, non-independent samples. Showing where they diverge
  is itself a useful output.
- **Stateless by default** — no user accounts/DB for the public tool;
  scenarios are URL params or POST bodies.
- **No AI dependency** — pure quant/stats, free to self-host with zero API
  keys.

## Stack

| Component | Tool |
|---|---|
| Compute | Python + numpy/pandas/scipy |
| API | FastAPI |
| Historical data | Shiller dataset (Yale, public) |
| Frontend | React/Astro + Recharts or visx |
| Containerization | Docker / docker-compose |

## Development

Setup instructions will be added as the core engine takes shape.

## License

MIT — see [LICENSE](LICENSE).
