import { FormEvent, useState } from 'react'
import { authClient, clearApiToken } from './auth-client'

type AuthMode = 'sign-in' | 'sign-up'

export function AuthPage({ onAuthenticated }: { onAuthenticated: () => Promise<void> }) {
  const [mode, setMode] = useState<AuthMode>('sign-in')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)

    const result = mode === 'sign-up'
      ? await authClient.signUp.email({ name, email, password })
      : await authClient.signIn.email({ email, password })

    if (result.error) {
      setError(result.error.message ?? 'Authentication failed')
      setIsSubmitting(false)
      return
    }

    clearApiToken()
    await onAuthenticated()
    setIsSubmitting(false)
  }

  function switchMode() {
    setMode((current) => current === 'sign-in' ? 'sign-up' : 'sign-in')
    setError(null)
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <div className="auth-brand">
          <span className="brand-mark" aria-hidden="true">A</span>
          <span>Atlas</span>
        </div>
        <p className="eyebrow">Inventory workspace</p>
        <h1 id="auth-title">{mode === 'sign-in' ? 'Welcome back' : 'Create your account'}</h1>
        <p className="auth-intro">
          {mode === 'sign-in'
            ? 'Sign in to manage your catalog and inventory.'
            : 'Set up your secure Atlas account in a few seconds.'}
        </p>
        <form className="auth-form" onSubmit={submit}>
          {mode === 'sign-up' && (
            <label>
              Name
              <input
                autoComplete="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                required
              />
            </label>
          )}
          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete={mode === 'sign-in' ? 'current-password' : 'new-password'}
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            {mode === 'sign-up' && <small>Use at least 8 characters.</small>}
          </label>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="button primary auth-submit" disabled={isSubmitting}>
            {isSubmitting ? 'Please wait…' : mode === 'sign-in' ? 'Sign in' : 'Create account'}
          </button>
        </form>
        <p className="auth-switch">
          {mode === 'sign-in' ? 'New to Atlas?' : 'Already have an account?'}{' '}
          <button type="button" onClick={switchMode}>
            {mode === 'sign-in' ? 'Create an account' : 'Sign in'}
          </button>
        </p>
      </section>
    </main>
  )
}
