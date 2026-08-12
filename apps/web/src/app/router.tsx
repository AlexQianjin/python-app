import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router'
import { AppLayout } from './AppLayout'
import { DashboardPage } from '../features/dashboard'
import { ProductsPage } from '../features/products'

const rootRoute = createRootRoute({
  component: AppLayout,
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

const routeTree = rootRoute.addChildren([indexRoute, productsRoute])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
