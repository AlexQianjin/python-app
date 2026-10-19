# API

FastAPI application managed by [uv](https://docs.astral.sh/uv/).

From this directory, run `uv sync`, apply the database migrations
with `uv run alembic upgrade head`, then start the development server
with `uv run fastapi dev app/main.py`.

Create a migration after changing a SQLAlchemy model:

```sh
pnpm db:revision -- -m "describe the change"
pnpm db:migrate
```

For an existing database that already has the `products` table from the former
automatic setup, run `uv run alembic stamp 20260813_01` once to
baseline it.

Cross-cutting configuration, security, logging, database setup, and dependencies
live under `app`, while each feature owns its router, service, repository,
schemas, and models under `app/modules`.
