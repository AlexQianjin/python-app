import { clearApiToken, getApiToken } from '../../auth'

export type Product = {
  id: number
  sku: string
  name: string
  description: string
  category: string
  price: string
  stock: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export type ProductInput = Pick<
  Product,
  'sku' | 'name' | 'description' | 'category' | 'price' | 'stock' | 'is_active'
>

export type ProductPage = {
  items: Product[]
  total: number
  page: number
  page_size: number
  pages: number
}

export type ProductSummary = {
  total_products: number
  active_products: number
  total_stock: number
  inventory_value: string
  low_stock_count: number
  categories: Array<{ name: string; product_count: number; stock: number }>
  low_stock_products: Product[]
  recently_updated: Product[]
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const token = await getApiToken()
  const response = await fetch(url, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })
  if (response.status === 401) clearApiToken()
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new Error(payload?.detail ?? `Request failed (${response.status})`)
  }
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>)
}

export function getProducts(page: number, search: string): Promise<ProductPage> {
  const params = new URLSearchParams({ page: String(page), page_size: '100' })
  if (search) params.set('search', search)
  return request(`/api/products?${params}`)
}

export function getProductSummary(): Promise<ProductSummary> {
  return request('/api/products/summary')
}

export function createProduct(input: ProductInput): Promise<Product> {
  return request('/api/products', { method: 'POST', body: JSON.stringify(input) })
}

export function updateProduct(id: number, input: ProductInput): Promise<Product> {
  return request(`/api/products/${id}`, { method: 'PUT', body: JSON.stringify(input) })
}

export function deleteProduct(id: number): Promise<void> {
  return request(`/api/products/${id}`, { method: 'DELETE' })
}
