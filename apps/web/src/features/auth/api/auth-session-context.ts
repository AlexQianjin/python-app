import { createContext } from 'react'
import { authClient } from './auth-client'

export type AuthSession = ReturnType<typeof authClient.useSession>

export const AuthSessionContext = createContext<AuthSession | null>(null)
