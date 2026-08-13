import { Link, Outlet } from '@tanstack/react-router'
import { LayoutDashboard, Package, UsersRound } from 'lucide-react'
import { AuthPage, authClient, clearApiToken } from '../features/auth'

export function AppLayout() {
  const { data: session, isPending, error, refetch } = authClient.useSession()

  if (isPending) {
    return (
      <main className="auth-page">
        <div className="auth-loading">Checking your session…</div>
      </main>
    )
  }

  if (!session) {
    return (
      <>
        {error && <div className="toast">{error.message}</div>}
        <AuthPage onAuthenticated={refetch} />
      </>
    )
  }

  const initials = session.user.name
    .split(/\s+/)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  async function signOut() {
    await authClient.signOut()
    clearApiToken()
    await refetch()
  }

  return (
    <div className="app-frame">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            A
          </span>
          <span>Atlas</span>
        </div>
        <nav aria-label="Main navigation">
          <Link to="/" activeOptions={{ exact: true }} activeProps={{ className: 'active' }}>
            <span className="nav-icon" aria-hidden="true">
              <LayoutDashboard size={19} strokeWidth={1.8} />
            </span>{' '}
            Dashboard
          </Link>
          <Link to="/products" activeProps={{ className: 'active' }}>
            <span className="nav-icon" aria-hidden="true">
              <Package size={19} strokeWidth={1.8} />
            </span>{' '}
            Products
          </Link>
          <Link to="/users" activeProps={{ className: 'active' }}>
            <span className="nav-icon" aria-hidden="true">
              <UsersRound size={19} strokeWidth={1.8} />
            </span>{' '}
            Users
          </Link>
        </nav>
        <div className="sidebar-footer">
          <span className="user-avatar" aria-hidden="true">
            {initials}
          </span>
          <div>
            <strong>{session.user.name}</strong>
            <span>{session.user.email}</span>
          </div>
          <button className="sign-out" type="button" onClick={signOut} aria-label="Sign out">
            ↪
          </button>
        </div>
      </aside>
      <div className="main-column">
        <div className="mobile-bar">
          <div className="brand">
            <span className="brand-mark" aria-hidden="true">
              A
            </span>
            <span>Atlas</span>
          </div>
          <nav aria-label="Mobile navigation">
            <Link to="/" activeOptions={{ exact: true }} activeProps={{ className: 'active' }}>
              Dashboard
            </Link>
            <Link to="/products" activeProps={{ className: 'active' }}>
              Products
            </Link>
            <Link to="/users" activeProps={{ className: 'active' }}>
              Users
            </Link>
            <button className="mobile-sign-out" type="button" onClick={signOut}>
              Sign out
            </button>
          </nav>
        </div>
        <Outlet />
      </div>
    </div>
  )
}
