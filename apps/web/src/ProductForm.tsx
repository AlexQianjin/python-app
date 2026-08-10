import { useState, type FormEvent } from 'react'
import type { Product, ProductInput } from './api'

const EMPTY_PRODUCT: ProductInput = {
  sku: '',
  name: '',
  description: '',
  category: '',
  price: '0.00',
  stock: 0,
  is_active: true,
}

type ProductFormProps = {
  product: Product | null
  isSaving: boolean
  error: string | null
  onClose: () => void
  onSubmit: (input: ProductInput) => void
}

export function ProductForm({ product, isSaving, error, onClose, onSubmit }: ProductFormProps) {
  const [form, setForm] = useState<ProductInput>(() => product ? {
      sku: product.sku,
      name: product.name,
      description: product.description,
      category: product.category,
      price: product.price,
      stock: product.stock,
      is_active: product.is_active,
    } : EMPTY_PRODUCT)

  function submit(event: FormEvent) {
    event.preventDefault()
    onSubmit(form)
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="product-form-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <p className="eyebrow">Catalog item</p>
            <h2 id="product-form-title">{product ? 'Edit product' : 'New product'}</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close">×</button>
        </div>
        <form onSubmit={submit}>
          <div className="form-grid">
            <label>
              SKU
              <input required maxLength={32} value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} />
            </label>
            <label>
              Category
              <input required maxLength={80} value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
            </label>
            <label className="span-two">
              Product name
              <input required maxLength={160} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </label>
            <label>
              Price
              <input required min="0" step="0.01" type="number" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
            </label>
            <label>
              Stock
              <input required min="0" step="1" type="number" value={form.stock} onChange={(e) => setForm({ ...form, stock: Number(e.target.value) })} />
            </label>
            <label className="span-two">
              Description
              <textarea maxLength={2000} rows={4} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </label>
            <label className="checkbox span-two">
              <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
              Active and available for sale
            </label>
          </div>
          {error && <p className="form-error" role="alert">{error}</p>}
          <div className="form-actions">
            <button className="button secondary" type="button" onClick={onClose}>Cancel</button>
            <button className="button primary" type="submit" disabled={isSaving}>
              {isSaving ? 'Saving…' : product ? 'Save changes' : 'Create product'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}
