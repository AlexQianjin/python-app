import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { parseAsInteger, parseAsString, useQueryStates } from 'nuqs'
import {
  createUser,
  deleteUser,
  getUsers,
  updateUser,
  type User,
  type UserInput,
} from '../api/users-api'
import { UserForm } from '../components/UserForm'
import { UserTable } from '../components/UserTable'

export function UsersPage() {
  const queryClient = useQueryClient()
  const [{ page, search }, setUserQuery] = useQueryStates(
    {
      page: parseAsInteger.withDefault(1),
      search: parseAsString.withDefault(''),
    },
    { history: 'push', urlKeys: { page: 'userPage', search: 'userSearch' } },
  )
  const [searchInput, setSearchInput] = useState(search)
  const [formOpen, setFormOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)

  useEffect(() => setSearchInput(search), [search])

  const query = useQuery({
    queryKey: ['users', page, search],
    queryFn: () => getUsers(page, search),
    placeholderData: (previous) => previous,
  })

  const saveMutation = useMutation({
    mutationFn: (input: UserInput) =>
      selectedUser ? updateUser(selectedUser.id, input) : createUser(input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['users'] })
      setFormOpen(false)
      setSelectedUser(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  const openCreate = () => {
    saveMutation.reset()
    setSelectedUser(null)
    setFormOpen(true)
  }
  const openEdit = useCallback(
    (user: User) => {
      saveMutation.reset()
      setSelectedUser(user)
      setFormOpen(true)
    },
    [saveMutation],
  )
  const remove = useCallback(
    (user: User) => {
      if (window.confirm(`Delete “${user.name}”? This cannot be undone.`)) {
        deleteMutation.mutate(user.id)
      }
    },
    [deleteMutation],
  )

  function submitSearch(event: FormEvent) {
    event.preventDefault()
    void setUserQuery({ page: 1, search: searchInput.trim() })
  }

  const data = query.data
  return (
    <main className="page-content users-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Workspace</p>
          <h1>Users</h1>
          <p className="intro">Manage team members, roles, and account access.</p>
        </div>
        <button className="button primary" type="button" onClick={openCreate}>
          + Add user
        </button>
      </header>

      <section className="catalog-card">
        <div className="toolbar">
          <form className="search" role="search" onSubmit={submitSearch}>
            <span aria-hidden="true">⌕</span>
            <input
              aria-label="Search users"
              placeholder="Search name, email, or role"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
            />
            <button type="submit">Search</button>
          </form>
          <p>
            <strong>{data?.total.toLocaleString() ?? '—'}</strong> users
          </p>
        </div>

        {query.isError ? (
          <div className="state-panel error-state">
            <strong>Couldn’t load users</strong>
            <span>{query.error.message}</span>
            <button className="button secondary" type="button" onClick={() => query.refetch()}>
              Try again
            </button>
          </div>
        ) : !data ? (
          <div className="state-panel">Loading users…</div>
        ) : data.items.length === 0 ? (
          <div className="state-panel">No users match your search.</div>
        ) : (
          <UserTable users={data.items} onEdit={openEdit} onDelete={remove} />
        )}

        <footer className="pagination">
          <span>
            Page <strong>{data?.page ?? page}</strong> of <strong>{data?.pages || 1}</strong> · 20
            per page
          </span>
          <div>
            <button
              type="button"
              disabled={page <= 1 || query.isFetching}
              onClick={() => setUserQuery({ page: page - 1 })}
            >
              ← Previous
            </button>
            <button
              type="button"
              disabled={!data || page >= data.pages || query.isFetching}
              onClick={() => setUserQuery({ page: page + 1 })}
            >
              Next →
            </button>
          </div>
        </footer>
      </section>

      {deleteMutation.isError && (
        <div className="toast" role="alert">
          {deleteMutation.error.message}
        </div>
      )}
      {formOpen && (
        <UserForm
          user={selectedUser}
          isSaving={saveMutation.isPending}
          error={saveMutation.error?.message ?? null}
          onClose={() => setFormOpen(false)}
          onSubmit={(input) => saveMutation.mutate(input)}
        />
      )}
    </main>
  )
}
