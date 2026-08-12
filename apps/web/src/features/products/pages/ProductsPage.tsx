import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { parseAsInteger, parseAsString, useQueryStates } from 'nuqs'
import {
  createProduct,
  deleteProduct,
  getProducts,
  updateProduct,
  type Product,
  type ProductInput,
} from '../api/products-api'
import { ProductForm } from '../components/ProductForm'
import { ProductTable } from '../components/ProductTable'

export function ProductsPage() {
  const queryClient = useQueryClient()
  const [{ page, search }, setProductQuery] = useQueryStates(
    {
      page: parseAsInteger.withDefault(1),
      search: parseAsString.withDefault(''),
    },
    { history: 'push' },
  )
  const [searchInput, setSearchInput] = useState(search)
  const [formOpen, setFormOpen] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)

  useEffect(() => {
    setSearchInput(search)
  }, [search])

  const query = useQuery({
    queryKey: ['products', page, search],
    queryFn: () => getProducts(page, search),
    placeholderData: (previous) => previous,
  })

  const saveMutation = useMutation({
    mutationFn: (input: ProductInput) =>
      selectedProduct ? updateProduct(selectedProduct.id, input) : createProduct(input),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['products'] }),
        queryClient.invalidateQueries({ queryKey: ['product-summary'] }),
      ])
      setFormOpen(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteProduct,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['products'] }),
        queryClient.invalidateQueries({ queryKey: ['product-summary'] }),
      ])
    },
  })

  const openCreate = () => {
    saveMutation.reset()
    setSelectedProduct(null)
    setFormOpen(true)
  }
  const openEdit = useCallback(
    (product: Product) => {
      saveMutation.reset()
      setSelectedProduct(product)
      setFormOpen(true)
    },
    [saveMutation],
  )
  const remove = useCallback(
    (product: Product) => {
      if (window.confirm(`Delete “${product.name}”? This cannot be undone.`)) {
        deleteMutation.mutate(product.id)
      }
    },
    [deleteMutation],
  )

  function submitSearch(event: FormEvent) {
    event.preventDefault()
    void setProductQuery({ page: 1, search: searchInput.trim() })
  }

  const data = query.data
  return (
    <main className="page-content products-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Inventory</p>
          <h1>Products</h1>
          <p className="intro">Manage your product catalog, pricing, and availability.</p>
        </div>
        <button className="button primary" type="button" onClick={openCreate}>
          + Add product
        </button>
      </header>

      <section className="catalog-card">
        <div className="toolbar">
          <form className="search" role="search" onSubmit={submitSearch}>
            <span aria-hidden="true">⌕</span>
            <input
              aria-label="Search products"
              placeholder="Search name, SKU, or category"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
            <button type="submit">Search</button>
          </form>
          <p>
            <strong>{data?.total.toLocaleString() ?? '—'}</strong> products
          </p>
        </div>

        {query.isError ? (
          <div className="state-panel error-state">
            <strong>Couldn’t load products</strong>
            <span>{query.error.message}</span>
            <button className="button secondary" type="button" onClick={() => query.refetch()}>
              Try again
            </button>
          </div>
        ) : !data ? (
          <div className="state-panel">Loading products…</div>
        ) : data.items.length === 0 ? (
          <div className="state-panel">No products match your search.</div>
        ) : (
          <ProductTable products={data.items} onEdit={openEdit} onDelete={remove} />
        )}

        <footer className="pagination">
          <span>
            Page <strong>{data?.page ?? page}</strong> of <strong>{data?.pages || 1}</strong> · 100
            per page
          </span>
          <div>
            <button
              type="button"
              disabled={page <= 1 || query.isFetching}
              onClick={() => setProductQuery({ page: page - 1 })}
            >
              ← Previous
            </button>
            <button
              type="button"
              disabled={!data || page >= data.pages || query.isFetching}
              onClick={() => setProductQuery({ page: page + 1 })}
            >
              Next →
            </button>
          </div>
        </footer>
      </section>

      {deleteMutation.isError && (
        <div className="toast" role="alert">
          {deleteMutation.error.message}
        </div>
      )}
      {formOpen && (
        <ProductForm
          product={selectedProduct}
          isSaving={saveMutation.isPending}
          error={saveMutation.error?.message ?? null}
          onClose={() => setFormOpen(false)}
          onSubmit={(input) => saveMutation.mutate(input)}
        />
      )}
    </main>
  )
}
