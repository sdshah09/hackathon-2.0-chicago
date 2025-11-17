"""Entrypoint for running the FastAPI server."""

import sys
from pathlib import Path

# Add project root to path so imports work when running from backend/
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)