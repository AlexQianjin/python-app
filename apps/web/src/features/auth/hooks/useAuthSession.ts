import { useContext } from 'react'
import { AuthSessionContext } from '../api/auth-session-context'

export function useAuthSession() {
  const session = useContext(AuthSessionContext)

  if (!session) {
    throw new Error('useAuthSession must be used within AuthSessionProvider')
  }

  return session
}
