"""Vercel Python entrypoint: serves the Analog Compass API under /api on the same origin as the website."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi import FastAPI  # noqa: E402

from analog_compass.api.app import app as core_app  # noqa: E402

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/api", core_app)
