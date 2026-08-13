import { useState, type FormEvent } from 'react'
import type { User, UserInput, UserRole } from '../api/users-api'

const EMPTY_USER: UserInput = {
  name: '',
  email: '',
  role: 'member',
  is_active: true,
}

type UserFormProps = {
  user: User | null
  isSaving: boolean
  error: string | null
  onClose: () => void
  onSubmit: (input: UserInput) => void
}

export function UserForm({ user, isSaving, error, onClose, onSubmit }: UserFormProps) {
  const [form, setForm] = useState<UserInput>(() =>
    user
      ? { name: user.name, email: user.email, role: user.role, is_active: user.is_active }
      : EMPTY_USER,
  )

  function submit(event: FormEvent) {
    event.preventDefault()
    onSubmit({ ...form, name: form.name.trim(), email: form.email.trim().toLowerCase() })
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="user-form-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <p className="eyebrow">Team member</p>
            <h2 id="user-form-title">{user ? 'Edit user' : 'New user'}</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <form onSubmit={submit}>
          <div className="form-grid">
            <label className="span-two">
              Full name
              <input
                required
                maxLength={160}
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
              />
            </label>
            <label>
              Email address
              <input
                required
                type="email"
                maxLength={320}
                value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })}
              />
            </label>
            <label>
              Role
              <select
                value={form.role}
                onChange={(event) => setForm({ ...form, role: event.target.value as UserRole })}
              >
                <option value="member">Member</option>
                <option value="manager">Manager</option>
                <option value="admin">Admin</option>
              </select>
            </label>
            <label className="checkbox span-two">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
              />
              Active user with access to the workspace
            </label>
          </div>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <div className="form-actions">
            <button className="button secondary" type="button" onClick={onClose}>
              Cancel
            </button>
            <button className="button primary" type="submit" disabled={isSaving}>
              {isSaving ? 'Saving…' : user ? 'Save changes' : 'Create user'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}
