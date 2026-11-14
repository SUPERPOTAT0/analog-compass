"""ASGI entrypoint for containers / Vercel Python / any ASGI host.

    uvicorn asgi:app --host 0.0.0.0 --port 8000
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from analog_compass.api.app import app  # noqa: E402

__all__ = ["app"]
