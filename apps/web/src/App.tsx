import { useEffect, useState } from 'react'

type HealthResponse = {
  status: string
  database: string
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    const checkHealth = () => {
      fetch('/api/health')
        .then((response) => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`)
          return response.json() as Promise<HealthResponse>
        })
        .then((response) => {
          if (!active) return
          setHealth(response)
          setError(null)
        })
        .catch((reason: unknown) => {
          if (!active) return
          setHealth(null)
          setError(reason instanceof Error ? reason.message : 'Unknown error')
        })
    }

    checkHealth()

    return () => {
      active = false
    }
  }, [])

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
              ? `API unavailable · ${error}`
              : 'Checking API…'}
        </div>
      </section>
    </main>
  )
}

export default App
