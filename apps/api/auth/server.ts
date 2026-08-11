import { serve } from '@hono/node-server'
import { getMigrations } from 'better-auth/db/migration'
import { Hono } from 'hono'
import { auth, pool } from './auth.js'

const port = Number(process.env.AUTH_SERVER_PORT ?? 8001)
const app = new Hono()

app.get('/health', (context) => context.json({ status: 'ok' }))
app.on(['GET', 'POST'], '/api/auth/*', (context) => auth.handler(context.req.raw))

const { runMigrations } = await getMigrations(auth.options)
await runMigrations()

const server = serve({ fetch: app.fetch, port }, (info) => {
  console.log(`Better Auth listening on http://localhost:${info.port}`)
})

async function shutdown() {
  server.close()
  await pool.end()
}

process.once('SIGINT', shutdown)
process.once('SIGTERM', shutdown)
