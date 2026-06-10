"""FastAPI application factory for the fire-sim API."""
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from fire_sim.api.limiter import DEFAULT_RATE_LIMIT, limiter
from fire_sim.api.routes import router

DESCRIPTION = """
Self-hosted Safe Withdrawal Rate (SWR) / retirement simulation engine.

Combines a historical rolling-window simulator (Trinity Study / cFIREsim
style, over the Shiller dataset back to 1871), a vectorized Monte Carlo
simulator (lognormal or block-bootstrap), a CAPE-based dynamic withdrawal
model, and sequence-of-returns risk analysis behind a single API.

No accounts, no persistence - every endpoint is a stateless function of its
request body.
"""


def create_app(rate_limit: str = DEFAULT_RATE_LIMIT) -> FastAPI:
    app_limiter = limiter if rate_limit == DEFAULT_RATE_LIMIT else Limiter(
        key_func=get_remote_address, default_limits=[rate_limit]
    )

    app = FastAPI(
        title="fire-sim API",
        description=DESCRIPTION,
        version="0.1.0",
        license_info={"name": "MIT", "url": "https://github.com/kogent-tech/fire-sim/blob/main/LICENSE"},
    )

    app.state.limiter = app_limiter

    @app.exception_handler(RateLimitExceeded)
    def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        # Must be sync: SlowAPIMiddleware.dispatch calls handlers synchronously
        # and falls back to slowapi's default (unstructured) handler for coroutines.
        return JSONResponse(
            status_code=429, content={"error": {"type": "RateLimitExceeded", "message": str(exc.detail)}}
        )

    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": {"type": "ValueError", "message": str(exc)}})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = jsonable_encoder(exc.errors(), exclude={"input", "url"})
        return JSONResponse(status_code=422, content={"error": {"type": "ValidationError", "message": errors}})

    app.include_router(router)
    return app


app = create_app()
