import { ReactNode } from 'react'
import { authClient } from '../api/auth-client'
import { AuthSessionContext } from '../api/auth-session-context'

export function AuthSessionProvider({ children }: { children: ReactNode }) {
  const session = authClient.useSession()

  return <AuthSessionContext.Provider value={session}>{children}</AuthSessionContext.Provider>
}
