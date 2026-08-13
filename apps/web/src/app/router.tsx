import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router'
import { NuqsAdapter } from 'nuqs/adapters/tanstack-router'
import { AppLayout } from './AppLayout'
import { DashboardPage } from '../features/dashboard'
import { ProductsPage } from '../features/products'
import { UsersPage } from '../features/users'

const rootRoute = createRootRoute({
  component: () => (
    <NuqsAdapter>
      <AppLayout />
    </NuqsAdapter>
  ),
  notFoundComponent: () => <main>Page not found</main>,
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: DashboardPage,
})

const productsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/products',
  component: ProductsPage,
})

const usersRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/users',
  component: UsersPage,
})

const routeTree = rootRoute.addChildren([indexRoute, productsRoute, usersRoute])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
