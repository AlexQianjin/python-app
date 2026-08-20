import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { createOrder, getCart, getOrders, removeCartItem, updateCartItem } from '../api/orders-api'

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
const dateTime = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
})

export function OrdersPage() {
  const queryClient = useQueryClient()
  const cartQuery = useQuery({ queryKey: ['cart'], queryFn: getCart })
  const ordersQuery = useQuery({ queryKey: ['orders'], queryFn: () => getOrders() })

  const refreshCart = async () => queryClient.invalidateQueries({ queryKey: ['cart'] })
  const quantityMutation = useMutation({
    mutationFn: ({ id, quantity }: { id: number; quantity: number }) =>
      updateCartItem(id, quantity),
    onSuccess: refreshCart,
  })
  const removeMutation = useMutation({
    mutationFn: removeCartItem,
    onSuccess: refreshCart,
  })
  const checkoutMutation = useMutation({
    mutationFn: createOrder,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['cart'] }),
        queryClient.invalidateQueries({ queryKey: ['orders'] }),
        queryClient.invalidateQueries({ queryKey: ['products'] }),
        queryClient.invalidateQueries({ queryKey: ['product-summary'] }),
      ])
    },
  })

  const error =
    cartQuery.error ??
    ordersQuery.error ??
    quantityMutation.error ??
    removeMutation.error ??
    checkoutMutation.error
  const cart = cartQuery.data
  const busy = quantityMutation.isPending || removeMutation.isPending || checkoutMutation.isPending

  return (
    <main className="page-content orders-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Shopping</p>
          <h1>Cart & orders</h1>
          <p className="intro">Review the products you want and keep track of submitted orders.</p>
        </div>
        <Link className="button secondary link-button" to="/products">
          ← Continue shopping
        </Link>
      </header>

      {error && (
        <div className="commerce-error" role="alert">
          {error.message}
        </div>
      )}

      <section className="commerce-card cart-card">
        <div className="commerce-heading">
          <div>
            <h2>Shopping cart</h2>
            <p>
              {cart
                ? `${cart.total_quantity} item${cart.total_quantity === 1 ? '' : 's'}`
                : 'Loading…'}
            </p>
          </div>
          {cart && cart.items.length > 0 && (
            <strong className="cart-total">{currency.format(Number(cart.subtotal))}</strong>
          )}
        </div>

        {!cart ? (
          <div className="commerce-empty">Loading your cart…</div>
        ) : cart.items.length === 0 ? (
          <div className="commerce-empty">
            <strong>Your cart is empty</strong>
            <span>Add something from the product catalog to create an order.</span>
            <Link className="button primary link-button" to="/products">
              Browse products
            </Link>
          </div>
        ) : (
          <>
            <div className="cart-items">
              {cart.items.map((item) => (
                <article className="cart-item" key={item.id}>
                  <div className="product-avatar" aria-hidden="true">
                    {item.product.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="cart-product">
                    <strong>{item.product.name}</strong>
                    <span>
                      {item.product.sku} · {currency.format(Number(item.product.price))} each
                    </span>
                  </div>
                  <label className="quantity-control">
                    <span>Qty</span>
                    <select
                      aria-label={`Quantity for ${item.product.name}`}
                      value={item.quantity}
                      disabled={busy}
                      onChange={(event) =>
                        quantityMutation.mutate({
                          id: item.id,
                          quantity: Number(event.target.value),
                        })
                      }
                    >
                      {Array.from(
                        { length: Math.min(item.product.stock, 99) },
                        (_, index) => index + 1,
                      ).map((quantity) => (
                        <option key={quantity} value={quantity}>
                          {quantity}
                        </option>
                      ))}
                    </select>
                  </label>
                  <strong className="line-total">{currency.format(Number(item.line_total))}</strong>
                  <button
                    className="remove-item"
                    type="button"
                    disabled={busy}
                    onClick={() => removeMutation.mutate(item.id)}
                  >
                    Remove
                  </button>
                </article>
              ))}
            </div>
            <div className="checkout-bar">
              <div>
                <span>Order total</span>
                <strong>{currency.format(Number(cart.subtotal))}</strong>
              </div>
              <button
                className="button primary"
                type="button"
                disabled={busy}
                onClick={() => checkoutMutation.mutate()}
              >
                {checkoutMutation.isPending ? 'Creating order…' : 'Create order'}
              </button>
            </div>
          </>
        )}
      </section>

      <section className="commerce-card order-history">
        <div className="commerce-heading">
          <div>
            <h2>Order list</h2>
            <p>{ordersQuery.data ? `${ordersQuery.data.total} submitted orders` : 'Loading…'}</p>
          </div>
        </div>
        {!ordersQuery.data ? (
          <div className="commerce-empty">Loading orders…</div>
        ) : ordersQuery.data.items.length === 0 ? (
          <div className="commerce-empty compact">
            <strong>No orders yet</strong>
            <span>Your completed carts will appear here.</span>
          </div>
        ) : (
          <div className="order-list">
            {ordersQuery.data.items.map((order) => (
              <details className="order-row" key={order.id}>
                <summary>
                  <div>
                    <strong>Order #{order.id}</strong>
                    <span>{dateTime.format(new Date(order.created_at))}</span>
                  </div>
                  <span className="order-status">{order.status}</span>
                  <span>{order.items.reduce((sum, item) => sum + item.quantity, 0)} items</span>
                  <strong>{currency.format(Number(order.total))}</strong>
                </summary>
                <div className="order-lines">
                  {order.items.map((item) => (
                    <div key={item.id}>
                      <span>
                        {item.product_name} <small>{item.sku}</small>
                      </span>
                      <span>
                        {item.quantity} × {currency.format(Number(item.unit_price))}
                      </span>
                      <strong>{currency.format(Number(item.line_total))}</strong>
                    </div>
                  ))}
                </div>
              </details>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}
