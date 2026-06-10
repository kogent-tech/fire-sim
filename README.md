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
| Frontend | React/Astro + Recharts |
| Containerization | Docker / docker-compose |

## Development

### Backend / simulation engine + API

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                 # run engine + API tests
uvicorn fire_sim.api.main:app --reload # http://127.0.0.1:8000, docs at /docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # http://127.0.0.1:4321, proxies to PUBLIC_API_BASE_URL (defaults to http://127.0.0.1:8000 in dev)
npm run build  # static build to frontend/dist/
```

### Docker (self-hosting)

**Quick start (pre-built images):**

```bash
curl -O https://raw.githubusercontent.com/kogent-tech/fire-sim/main/docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d
```

**Build from source** (for development or customization):

```bash
docker compose up -d --build
```

Either way, open `http://localhost:8080`. The frontend container serves the
built static site and reverse-proxies `/api` to the backend container — no
extra configuration needed.

Tested on Debian 12 (bookworm) with Docker 29 + Compose v5 — recommended
base OS for self-hosting.

## License

MIT — see [LICENSE](LICENSE).
