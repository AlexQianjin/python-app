import { Link, Outlet } from '@tanstack/react-router'

export function AppLayout() {
  return (
    <div className="app-frame">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">A</span>
          <span>Atlas</span>
        </div>
        <nav aria-label="Main navigation">
          <Link to="/" activeOptions={{ exact: true }} activeProps={{ className: 'active' }}>
            <span className="nav-icon" aria-hidden="true">⌂</span> Dashboard
          </Link>
          <Link to="/products" activeProps={{ className: 'active' }}>
            <span className="nav-icon" aria-hidden="true">□</span> Products
          </Link>
        </nav>
        <div className="sidebar-footer">
          <span className="user-avatar" aria-hidden="true">AQ</span>
          <div><strong>Alex Quinn</strong><span>Administrator</span></div>
        </div>
      </aside>
      <div className="main-column">
        <div className="mobile-bar">
          <div className="brand"><span className="brand-mark" aria-hidden="true">A</span><span>Atlas</span></div>
          <nav aria-label="Mobile navigation">
            <Link to="/" activeOptions={{ exact: true }} activeProps={{ className: 'active' }}>Dashboard</Link>
            <Link to="/products" activeProps={{ className: 'active' }}>Products</Link>
          </nav>
        </div>
        <Outlet />
      </div>
    </div>
  )
}
