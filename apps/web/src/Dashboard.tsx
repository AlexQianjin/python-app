import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { getProductSummary, type Product } from './api'

const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})
const compactNumber = new Intl.NumberFormat('en-US', { notation: 'compact' })

function ProductRow({ product, lowStock = false }: { product: Product; lowStock?: boolean }) {
  return (
    <div className="activity-row">
      <div className="product-avatar" aria-hidden="true">{product.name.charAt(0).toUpperCase()}</div>
      <div className="activity-product">
        <strong>{product.name}</strong>
        <span>{product.sku} · {product.category}</span>
      </div>
      {lowStock ? (
        <span className={`stock-pill ${product.stock === 0 ? 'out' : ''}`}>
          {product.stock === 0 ? 'Out of stock' : `${product.stock} left`}
        </span>
      ) : (
        <span className="activity-date">
          {new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(new Date(product.updated_at))}
        </span>
      )}
    </div>
  )
}

export function Dashboard() {
  const query = useQuery({
    queryKey: ['product-summary'],
    queryFn: getProductSummary,
  })

  if (query.isError) {
    return (
      <main className="page-content">
        <div className="state-panel dashboard-state">
          <strong>Couldn’t load the dashboard</strong>
          <span>{query.error.message}</span>
          <button className="button secondary" type="button" onClick={() => query.refetch()}>Try again</button>
        </div>
      </main>
    )
  }

  if (!query.data) {
    return <main className="page-content"><div className="state-panel dashboard-state">Loading dashboard…</div></main>
  }

  const data = query.data
  const activeRate = data.total_products ? Math.round((data.active_products / data.total_products) * 100) : 0
  const maxCategoryStock = Math.max(...data.categories.map((category) => category.stock), 1)

  return (
    <main className="page-content">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">Overview</p>
          <h1>Good morning</h1>
          <p className="intro">Here’s what’s happening with your catalog today.</p>
        </div>
        <Link className="button primary link-button" to="/products">View products <span aria-hidden="true">→</span></Link>
      </header>

      <section className="metric-grid" aria-label="Catalog summary">
        <article className="metric-card">
          <span className="metric-icon blue" aria-hidden="true">P</span>
          <div><p>Total products</p><strong>{data.total_products.toLocaleString()}</strong><small>{activeRate}% currently active</small></div>
        </article>
        <article className="metric-card">
          <span className="metric-icon green" aria-hidden="true">$</span>
          <div><p>Inventory value</p><strong>{currency.format(Number(data.inventory_value))}</strong><small>Across all stock on hand</small></div>
        </article>
        <article className="metric-card">
          <span className="metric-icon purple" aria-hidden="true">#</span>
          <div><p>Units in stock</p><strong>{compactNumber.format(data.total_stock)}</strong><small>Available inventory units</small></div>
        </article>
        <article className="metric-card warning-card">
          <span className="metric-icon amber" aria-hidden="true">!</span>
          <div><p>Low stock</p><strong>{data.low_stock_count.toLocaleString()}</strong><small>Products with 25 units or less</small></div>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="dashboard-card category-card">
          <div className="card-heading">
            <div><h2>Stock by category</h2><p>Current units across your catalog</p></div>
            <span>{data.categories.length} categories</span>
          </div>
          <div className="category-bars">
            {data.categories.slice(0, 6).map((category) => (
              <div className="category-bar" key={category.name}>
                <div><span>{category.name}</span><strong>{category.stock.toLocaleString()}</strong></div>
                <div className="bar-track"><span style={{ width: `${Math.max((category.stock / maxCategoryStock) * 100, 3)}%` }} /></div>
                <small>{category.product_count} products</small>
              </div>
            ))}
          </div>
        </article>

        <article className="dashboard-card">
          <div className="card-heading">
            <div><h2>Low stock</h2><p>Items that may need attention</p></div>
            <Link to="/products">View all</Link>
          </div>
          <div className="activity-list">
            {data.low_stock_products.length ? data.low_stock_products.map((product) => (
              <ProductRow key={product.id} product={product} lowStock />
            )) : <div className="empty-list">Everything is well stocked.</div>}
          </div>
        </article>
      </section>

      <section className="dashboard-card recent-card">
        <div className="card-heading">
          <div><h2>Recently updated</h2><p>The latest changes across your products</p></div>
          <Link to="/products">Open catalog</Link>
        </div>
        <div className="activity-list recent-list">
          {data.recently_updated.map((product) => <ProductRow key={product.id} product={product} />)}
        </div>
      </section>
    </main>
  )
}
