import { createRootRoute, createRoute, createRouter, Outlet } from '@tanstack/react-router'
import { NuqsAdapter } from 'nuqs/adapters/tanstack-router'
import { AppLayout } from './AppLayout'
import { AuthSessionProvider, SignInPage } from '../features/auth'
import { DashboardPage } from '../features/dashboard'
import { ProductsPage } from '../features/products'
import { UsersPage } from '../features/users'
import { OrdersPage } from '../features/orders'

const rootRoute = createRootRoute({
  component: () => (
    <NuqsAdapter>
      <AuthSessionProvider>
        <Outlet />
      </AuthSessionProvider>
    </NuqsAdapter>
  ),
  notFoundComponent: () => <main>Page not found</main>,
})

const authenticatedRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: 'authenticated',
  component: AppLayout,
})

const indexRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/',
  component: DashboardPage,
})

const productsRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/products',
  component: ProductsPage,
})

const usersRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/users',
  component: UsersPage,
})

const ordersRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/orders',
  component: OrdersPage,
})

const signInRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/signin',
  validateSearch: (search: Record<string, unknown>) => ({
    redirect: typeof search.redirect === 'string' ? search.redirect : undefined,
  }),
  component: SignInPage,
})

const routeTree = rootRoute.addChildren([
  signInRoute,
  authenticatedRoute.addChildren([indexRoute, productsRoute, ordersRoute, usersRoute]),
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
