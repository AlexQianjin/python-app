import {
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router'
import App from './App'
import { AppLayout } from './AppLayout'
import { Dashboard } from './Dashboard'

const rootRoute = createRootRoute({
  component: AppLayout,
  notFoundComponent: () => <main>Page not found</main>,
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: Dashboard,
})

const productsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/products',
  component: App,
})

const routeTree = rootRoute.addChildren([indexRoute, productsRoute])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
