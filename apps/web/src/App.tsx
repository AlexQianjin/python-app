import { useQuery } from '@tanstack/react-query'

type HealthResponse = {
  status: string
  database: string
}

async function getHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/health')
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json() as Promise<HealthResponse>
}

function App() {
  const { data: health, error } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
  })

  return (
    <main>
      <section className="card">
        <p className="eyebrow">pnpm monorepo</p>
        <h1>React + FastAPI</h1>
        <p className="intro">
          A TypeScript web app backed by Python and PostgreSQL.
        </p>
        <div className="status" aria-live="polite">
          <span className={`dot ${health ? 'online' : ''}`} />
          {health
            ? `API ${health.status} · database ${health.database}`
            : error
              ? `API unavailable · ${error.message}`
              : 'Checking API…'}
        </div>
      </section>
    </main>
  )
}

export default App
