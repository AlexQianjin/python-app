import { request, type Product } from '../../products/api/products-api'

export type CartItem = {
  id: number
  product: Product
  quantity: number
  line_total: string
}

export type Cart = {
  items: CartItem[]
  total_quantity: number
  subtotal: string
}

export type OrderItem = {
  id: number
  product_id: number | null
  sku: string
  product_name: string
  unit_price: string
  quantity: number
  line_total: string
}

export type Order = {
  id: number
  status: string
  total: string
  created_at: string
  items: OrderItem[]
}

export type OrderPage = {
  items: Order[]
  total: number
  page: number
  page_size: number
  pages: number
}

export function getCart(): Promise<Cart> {
  return request('/api/cart')
}

export function addToCart(productId: number, quantity = 1): Promise<Cart> {
  return request('/api/cart/items', {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, quantity }),
  })
}

export function updateCartItem(itemId: number, quantity: number): Promise<Cart> {
  return request(`/api/cart/items/${itemId}`, {
    method: 'PUT',
    body: JSON.stringify({ quantity }),
  })
}

export function removeCartItem(itemId: number): Promise<void> {
  return request(`/api/cart/items/${itemId}`, { method: 'DELETE' })
}

export function createOrder(): Promise<Order> {
  return request('/api/orders', { method: 'POST' })
}

export function getOrders(page = 1): Promise<OrderPage> {
  return request(`/api/orders?page=${page}&page_size=20`)
}
