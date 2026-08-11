import { betterAuth } from 'better-auth'
import { jwt } from 'better-auth/plugins'
import { Pool } from 'pg'

const secret = process.env.BETTER_AUTH_SECRET
if (!secret || secret.length < 32) {
  throw new Error('BETTER_AUTH_SECRET must contain at least 32 characters')
}

const baseURL = process.env.BETTER_AUTH_URL ?? 'http://localhost:5173'
const databaseURL = process.env.AUTH_DATABASE_URL
  ?? process.env.DATABASE_URL?.replace('postgresql+asyncpg://', 'postgresql://')
  ?? 'postgresql://postgres:postgres@localhost:5432/app'

export const pool = new Pool({ connectionString: databaseURL })

export const auth = betterAuth({
  appName: 'Atlas',
  baseURL,
  secret,
  database: pool,
  trustedOrigins: [baseURL],
  emailAndPassword: {
    enabled: true,
    minPasswordLength: 8,
    autoSignIn: true,
  },
  plugins: [
    jwt({
      jwks: {
        keyPairConfig: { alg: 'ES256' },
        rotationInterval: 60 * 60 * 24 * 30,
        gracePeriod: 60 * 60 * 24 * 30,
      },
      jwt: {
        issuer: baseURL,
        audience: baseURL,
        expirationTime: '15m',
        definePayload: ({ user }) => ({
          id: user.id,
          email: user.email,
          name: user.name,
        }),
      },
    }),
  ],
})
