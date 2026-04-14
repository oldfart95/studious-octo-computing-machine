from __future__ import annotations

import uvicorn

from .api import app
from .settings import ensure_directories, load_config


def run() -> None:
    config = load_config()
    ensure_directories(config)
    uvicorn.run(app, host=config.backend.host, port=config.backend.port)


if __name__ == "__main__":
    run()
