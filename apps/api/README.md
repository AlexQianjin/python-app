# API

FastAPI application managed by [uv](https://docs.astral.sh/uv/).

From this directory, run `python3 -m uv sync`, then start the development
server with `python3 -m uv run fastapi dev app/main.py`.

Cross-cutting configuration, security, logging, database setup, and dependencies
live under `app`, while each feature owns its router, service, repository,
schemas, and models under `app/modules`.
