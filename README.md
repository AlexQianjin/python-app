# React + FastAPI monorepo

A pnpm workspace containing a Vite React web app and a uv-managed FastAPI API,
backed by PostgreSQL and Redis.

## Stack

- `apps/web`: React, TypeScript, Vite
- `apps/api`: Python 3.12, FastAPI, SQLAlchemy, asyncpg, uv
- PostgreSQL 17 via Docker Compose
- Redis 8 for product read caching
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
docker compose up -d postgres redis
cd apps/api && python3 -m uv sync && python3 -m uv run alembic upgrade head && cd ../..
```

Set a private Better Auth secret in `apps/api/.env` (at least 32 characters).
The API app starts both FastAPI and the Better Auth gateway, and automatically
creates the Better Auth tables in the existing PostgreSQL database.

## Development

Run both applications from the repository root:

```sh
pnpm dev
```

The web app is available at <http://localhost:5173>. The API is available at
<http://localhost:8000>, with interactive documentation at
<http://localhost:8000/docs>.

Open the web app and create an account with email and password. Better Auth keeps
the browser session in a secure cookie and issues short-lived JWTs for calls to
FastAPI. All product and user routes require a valid authenticated user; health endpoints
remain public.

The Alembic migrations create the API database tables. On the first API startup,
an empty catalog is seeded with 1,000 deterministic mock products and an empty
user directory with 200 deterministic mock users. The Products screen loads 100
products per page, while the Users screen loads 20 users per page.

After changing a SQLAlchemy model, create and apply a migration from `apps/api`:

```sh
pnpm db:revision -- -m "describe the change"
pnpm db:migrate
```

If an older development database already has the `products` table from the
previous automatic setup, baseline it once with
`python3 -m uv run alembic stamp 20260813_01` instead of applying the initial
migration.

Product CRUD endpoints are available at `/api/products`:

- `GET /api/products?page=1&page_size=100&search=`
- `GET /api/products/{id}`
- `POST /api/products`
- `PUT /api/products/{id}`
- `DELETE /api/products/{id}`

Product lists, individual product reads, and the product summary use Redis with
a configurable TTL. Successful product writes invalidate all product cache
entries. If Redis is unavailable, requests fall back to PostgreSQL.

User CRUD endpoints are available at `/api/users`:

- `GET /api/users?page=1&page_size=20&search=`
- `GET /api/users/{id}`
- `POST /api/users`
- `PUT /api/users/{id}`
- `DELETE /api/users/{id}`

Authenticated shopping endpoints keep each user's cart and order history separate:

- `GET /api/cart`
- `POST /api/cart/items`
- `PUT /api/cart/items/{item_id}`
- `DELETE /api/cart/items/{item_id}`
- `DELETE /api/cart`
- `POST /api/orders` (checkout the current cart)
- `GET /api/orders?page=1&page_size=20`
- `GET /api/orders/{id}`

Checkout validates current availability, decrements stock, saves price and product
snapshots on the order, and clears the cart in one database transaction.

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
