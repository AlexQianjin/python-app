import { useEffect, useRef } from 'react'
import { useNavigate, useSearch } from '@tanstack/react-router'
import { AuthPage } from '../components/AuthPage'
import { useAuthSession } from '../hooks/useAuthSession'

function onAuthenticated() {
  return Promise.resolve()
}

export function SignInPage() {
  const navigate = useNavigate()
  const { redirect } = useSearch({ from: '/signin' })
  const { data: session, isPending, error } = useAuthSession()
  const destination = isSafeRedirect(redirect) ? redirect : '/'
  const isReturning = useRef(false)

  useEffect(() => {
    if (session && !isReturning.current) {
      isReturning.current = true
      void navigate({ href: destination, replace: true })
    }

    if (!session) {
      isReturning.current = false
    }
  }, [destination, navigate, session])

  if (isPending) {
    return (
      <main className="auth-page">
        <div className="auth-loading">Checking your session…</div>
      </main>
    )
  }

  if (session) {
    return (
      <main className="auth-page">
        <div className="auth-loading">Returning to your page…</div>
      </main>
    )
  }

  return (
    <>
      {error && <div className="toast">{error.message}</div>}
      <AuthPage onAuthenticated={onAuthenticated} />
    </>
  )
}

function isSafeRedirect(redirect: string | undefined): redirect is string {
  return (
    redirect !== undefined &&
    redirect.startsWith('/') &&
    !redirect.startsWith('//') &&
    !/^\/signin(?:[/?#]|$)/.test(redirect)
  )
}
