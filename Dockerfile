FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY fire_sim ./fire_sim
COPY data ./data

# Editable install: keeps fire_sim importable from /app so the engine's
# Path(__file__)-relative lookups under data/ continue to resolve.
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "fire_sim.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
