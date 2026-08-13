import { clearApiToken, getApiToken } from '../../auth'

export type UserRole = 'admin' | 'manager' | 'member'

export type User = {
  id: number
  name: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export type UserInput = Pick<User, 'name' | 'email' | 'role' | 'is_active'>

export type UserPage = {
  items: User[]
  total: number
  page: number
  page_size: number
  pages: number
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const token = await getApiToken()
  const response = await fetch(url, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })
  if (response.status === 401) clearApiToken()
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new Error(payload?.detail ?? `Request failed (${response.status})`)
  }
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>)
}

export function getUsers(page: number, search: string): Promise<UserPage> {
  const params = new URLSearchParams({ page: String(page), page_size: '20' })
  if (search) params.set('search', search)
  return request(`/api/users?${params}`)
}

export function createUser(input: UserInput): Promise<User> {
  return request('/api/users', { method: 'POST', body: JSON.stringify(input) })
}

export function updateUser(id: number, input: UserInput): Promise<User> {
  return request(`/api/users/${id}`, { method: 'PUT', body: JSON.stringify(input) })
}

export function deleteUser(id: number): Promise<void> {
  return request(`/api/users/${id}`, { method: 'DELETE' })
}
