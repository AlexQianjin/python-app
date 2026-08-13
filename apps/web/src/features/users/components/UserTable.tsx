import { useMemo, useRef } from 'react'
import { createColumnHelper, tableFeatures, useTable } from '@tanstack/react-table'
import { useVirtualizer } from '@tanstack/react-virtual'
import type { User } from '../api/users-api'

const features = tableFeatures({})
const columnHelper = createColumnHelper<typeof features, User>()

type UserTableProps = {
  users: User[]
  onEdit: (user: User) => void
  onDelete: (user: User) => void
}

export function UserTable({ users, onEdit, onDelete }: UserTableProps) {
  const columns = useMemo(
    () =>
      columnHelper.columns([
        columnHelper.accessor('name', {
          header: 'User',
          cell: (info) => {
            const user = info.row.original
            const initials = user.name
              .split(/\s+/)
              .map((part) => part[0])
              .join('')
              .slice(0, 2)
              .toUpperCase()
            return (
              <div className="managed-user-cell">
                <span className="managed-user-avatar" aria-hidden="true">
                  {initials}
                </span>
                <div>
                  <strong>{user.name}</strong>
                  <span>{user.email}</span>
                </div>
              </div>
            )
          },
        }),
        columnHelper.accessor('role', {
          header: 'Role',
          cell: (info) => <span className="role-label">{info.getValue()}</span>,
        }),
        columnHelper.accessor('is_active', {
          header: 'Status',
          cell: (info) => (
            <span className={`badge ${info.getValue() ? 'active' : 'inactive'}`}>
              {info.getValue() ? 'Active' : 'Inactive'}
            </span>
          ),
        }),
        columnHelper.accessor('created_at', {
          header: 'Added',
          cell: (info) =>
            new Intl.DateTimeFormat('en-US', { dateStyle: 'medium' }).format(
              new Date(info.getValue()),
            ),
        }),
        columnHelper.display({
          id: 'actions',
          header: 'Actions',
          cell: (info) => (
            <div className="row-actions">
              <button type="button" onClick={() => onEdit(info.row.original)}>
                Edit
              </button>
              <button
                className="danger-link"
                type="button"
                onClick={() => onDelete(info.row.original)}
              >
                Delete
              </button>
            </div>
          ),
        }),
      ]),
    [onDelete, onEdit],
  )

  const table = useTable({ features, columns, data: users })
  const rows = table.getRowModel().rows
  const scrollRef = useRef<HTMLDivElement>(null)
  // eslint-disable-next-line react-hooks/incompatible-library
  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 68,
    getItemKey: (index) => rows[index].id,
    overscan: 8,
  })

  return (
    <div className="table-shell user-table" role="table" aria-rowcount={users.length + 1}>
      <div className="table-header" role="rowgroup">
        {table.getHeaderGroups().map((headerGroup) => (
          <div className="table-grid" role="row" key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <div role="columnheader" key={header.id}>
                {header.isPlaceholder ? null : <table.FlexRender header={header} />}
              </div>
            ))}
          </div>
        ))}
      </div>
      <div className="table-scroll" ref={scrollRef} role="rowgroup">
        <div className="virtual-space" style={{ height: virtualizer.getTotalSize() }}>
          {virtualizer.getVirtualItems().map((virtualRow) => {
            const row = rows[virtualRow.index]
            return (
              <div
                className="table-grid table-row"
                role="row"
                aria-rowindex={virtualRow.index + 2}
                key={row.id}
                data-index={virtualRow.index}
                ref={virtualizer.measureElement}
                style={{ transform: `translateY(${virtualRow.start}px)` }}
              >
                {row.getAllCells().map((cell) => (
                  <div role="cell" key={cell.id}>
                    <table.FlexRender cell={cell} />
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
