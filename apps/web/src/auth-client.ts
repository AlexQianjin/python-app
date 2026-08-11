import { jwtClient } from 'better-auth/client/plugins'
import { createAuthClient } from 'better-auth/react'

export const authClient = createAuthClient({
  plugins: [jwtClient()],
})

let cachedToken: { value: string; expiresAt: number } | null = null

function tokenExpiration(token: string): number {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))) as {
      exp?: number
    }
    return (payload.exp ?? 0) * 1000
  } catch {
    return 0
  }
}

export function clearApiToken() {
  cachedToken = null
}

export async function getApiToken(): Promise<string> {
  if (cachedToken && cachedToken.expiresAt > Date.now() + 30_000) {
    return cachedToken.value
  }

  const { data, error } = await authClient.token()
  if (error || !data?.token) {
    clearApiToken()
    throw new Error(error?.message ?? 'Your session has expired. Please sign in again.')
  }

  cachedToken = { value: data.token, expiresAt: tokenExpiration(data.token) }
  return data.token
}
