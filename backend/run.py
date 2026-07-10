"""Launch ResellPro backend server."""

import os
from pathlib import Path

from dotenv import load_dotenv

root = Path(os.environ.get("RESELLPRO_ROOT", Path(__file__).resolve().parent.parent))
load_dotenv(root / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8420"))
    host = os.environ.get("HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
