# React + FastAPI monorepo

A pnpm workspace containing a Vite React web app and a uv-managed FastAPI API,
backed by PostgreSQL and Redis.

## Stack

- `apps/web`: React, TypeScript, Vite
- `apps/api`: Python 3.12, FastAPI, SQLAlchemy, asyncpg, uv
- PostgreSQL hosted by Supabase
- Redis 8 for product read caching
- Qdrant for multilingual hybrid document search
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
docker compose up -d redis qdrant
# Set DATABASE_URL in apps/api/.env before running migrations.
cd apps/api && uv sync && uv run alembic upgrade head && cd ../..
```

Set a private Better Auth secret in `apps/api/.env` (at least 32 characters).
The API app starts both FastAPI and the Better Auth gateway, and automatically
creates the Better Auth tables in the existing PostgreSQL database.

## Supabase database

Copy the **Session pooler** URI (port 5432) from the Supabase project's Connect
panel into `DATABASE_URL` in `apps/api/.env`, and append `?sslmode=require`.
Use the database password, with reserved characters percent-encoded. A direct
connection also works if your network supports the project's IP address family.
Avoid the transaction pooler (port 6543) for this setup.

Leave `AUTH_DATABASE_URL` empty (or remove it) so Better Auth uses the same
database. Remove any old localhost override. FastAPI, Alembic, Better Auth, and
AI chat checkpoints all use this database. Keep credentials out of Git.
Better Auth remains the application's authentication provider.

For a fresh database, run the setup migrations above and start the app; Better
Auth creates its own tables at startup. Use a dedicated Supabase project for
this app. Tables are backend-only: disable the Supabase Data API if unused, or
restrict its exposed schemas and table access before storing application data.

To preserve existing Docker data, stop the API, authentication server, and worker
before exporting. Keep the existing container and volume until the migration is
verified. Export only the app's `public` schema, including Better Auth and AI
checkpoint tables, and restore it into an empty destination `public` schema with
PostgreSQL tools of the same or newer major version as the source:

```sh
# Save the backup outside Git; it contains private application data.
docker compose exec -T postgres pg_dump -U postgres -d app \
  --schema=public --format=custom --no-owner --no-acl > /tmp/app-postgres.dump
# Set PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD and PGSSLMODE=require
# from the Supabase Session pooler URI in your shell (do not commit them).
# Supabase already owns public; exclude its schema creation/comment entries.
pg_restore --list /tmp/app-postgres.dump > /tmp/app-postgres.list
# Edit the list to remove the SCHEMA - public and COMMENT - SCHEMA public lines.
pg_restore --use-list=/tmp/app-postgres.list --no-owner --no-acl \
  --exit-on-error --single-transaction --dbname=postgres /tmp/app-postgres.dump
cd apps/api && uv run alembic upgrade head
```

Do not apply Alembic migrations to an empty target before restoring this full
backup: it already includes the schema and Alembic version. Check source/target
row counts and verify login, products, orders, and chat before switching traffic.
Redis caches may contain old database results; clear the product cache or use a
new Redis database index at cutover. Upload files and Qdrant remain on their
existing storage. Protect and delete the temporary backup when no longer needed.

The old PostgreSQL service is retained behind the `local-db` profile for rollback
or local development (`docker compose --profile local-db up -d postgres`).
Its existing volume is preserved; the default Compose startup runs Redis and Qdrant.

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
`uv run alembic stamp 20260813_01` instead of applying the initial
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

## AI Chat

The AI Chat page supports PDF, DOCX, TXT, and Markdown uploads (20 MB per file),
document-grounded answers with source links, and streamed progress. Uploads are
saved under `apps/api/data/uploads` in development. The API queues each file in
PostgreSQL, and the worker indexes it in Qdrant using the open-source BGE-M3
model for dense and learned sparse retrieval, plus Qdrant's BM25 for keyword
retrieval. Hybrid search fuses all three rankings with reciprocal rank fusion.
The first indexing run downloads BGE-M3 and may take some time.

Set `AI_MODEL_API_KEY` and `AI_MODEL` in `apps/api/.env` for a chat model. An
OpenAI-compatible endpoint can be selected with `AI_MODEL_BASE_URL`. Set
`AI_MEMORY_ENABLED=true` to enable Mem0 user memory. The worker starts with
`pnpm dev`; when running FastAPI alone, start it separately with
`pnpm --filter api start:worker`. Apply the latest Alembic migration before use.

Uploaded documents stay private to the authenticated user. Document originals,
Qdrant data, and PostgreSQL data all need durable volumes and backups in a
production deployment. The local `apps/api/data/uploads` directory is ignored
by Git.

To compare retrieval methods on your indexed files, create a JSONL file with
one case per line, for example:

```json
{"user_id":"user-id","query":"What is the return policy?","document_ids":["document-id"],"relevant_document_ids":["document-id"]}
```

Run `cd apps/api && uv run python -m app.modules.ai.evaluate cases.jsonl`.
It reports recall, reciprocal rank, and mean latency for dense, learned sparse,
BM25, and hybrid search. Use real labeled questions before changing fusion or
reranking. Upgrading an existing installation to this version queues ready
documents for reindexing in the new `ai_documents_v2` collection after the
database migration; wait for the worker to mark them ready again before search.
