# React + FastAPI monorepo

A pnpm workspace containing a Vite React web app and a uv-managed FastAPI API,
backed by PostgreSQL.

## Stack

- `apps/web`: React, TypeScript, Vite
- `apps/api`: Python 3.12, FastAPI, SQLAlchemy, asyncpg, uv
- PostgreSQL 17 via Docker Compose
- pnpm workspace orchestration

## Prerequisites

- Node.js 20 or newer
- pnpm 10 or newer
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Docker with Docker Compose

## Setup

```sh
pnpm install
cp apps/api/.env.example apps/api/.env
docker compose up -d postgres
cd apps/api && python3 -m uv sync && cd ../..
```

## Development

Run both applications from the repository root:

```sh
pnpm dev
```

The web app is available at <http://localhost:5173>. The API is available at
<http://localhost:8000>, with interactive documentation at
<http://localhost:8000/docs>.

On the first API startup, the database tables are created and an empty catalog is
seeded with 1,000 deterministic mock products. The Products screen loads 100
products per page and virtualizes the visible table rows.

Product CRUD endpoints are available at `/api/products`:

- `GET /api/products?page=1&page_size=100&search=`
- `GET /api/products/{id}`
- `POST /api/products`
- `PUT /api/products/{id}`
- `DELETE /api/products/{id}`

You can also run either app independently:

```sh
pnpm dev:web
pnpm dev:api
```

## Checks

```sh
pnpm build
pnpm lint
pnpm test
```
