import { useMemo, useRef } from 'react'
import { createColumnHelper, tableFeatures, useTable } from '@tanstack/react-table'
import { useVirtualizer } from '@tanstack/react-virtual'
import type { Product } from '../api/products-api'

const features = tableFeatures({})
const columnHelper = createColumnHelper<typeof features, Product>()

type ProductTableProps = {
  products: Product[]
  onEdit: (product: Product) => void
  onDelete: (product: Product) => void
  onAddToCart: (product: Product) => void
}

export function ProductTable({ products, onEdit, onDelete, onAddToCart }: ProductTableProps) {
  const columns = useMemo(
    () =>
      columnHelper.columns([
        columnHelper.accessor('sku', { header: 'SKU' }),
        columnHelper.accessor('name', {
          header: 'Product',
          cell: (info) => (
            <div className="product-cell">
              <strong>{info.getValue()}</strong>
              <span>{info.row.original.category}</span>
            </div>
          ),
        }),
        columnHelper.accessor('price', {
          header: 'Price',
          cell: (info) =>
            new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
              Number(info.getValue()),
            ),
        }),
        columnHelper.accessor('stock', {
          header: 'Stock',
          cell: (info) => info.getValue().toLocaleString(),
        }),
        columnHelper.accessor('is_active', {
          header: 'Status',
          cell: (info) => (
            <span className={`badge ${info.getValue() ? 'active' : 'inactive'}`}>
              {info.getValue() ? 'Active' : 'Inactive'}
            </span>
          ),
        }),
        columnHelper.display({
          id: 'actions',
          header: 'Actions',
          cell: (info) => (
            <div className="row-actions">
              <button
                className="cart-link"
                type="button"
                disabled={!info.row.original.is_active || info.row.original.stock === 0}
                onClick={() => onAddToCart(info.row.original)}
              >
                Add to cart
              </button>
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
    [onAddToCart, onDelete, onEdit],
  )

  const table = useTable({ features, columns, data: products })
  const rows = table.getRowModel().rows
  const scrollRef = useRef<HTMLDivElement>(null)
  // TanStack Virtual intentionally returns imperative functions that React Compiler skips.
  // eslint-disable-next-line react-hooks/incompatible-library
  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 64,
    getItemKey: (index) => rows[index].id,
    overscan: 8,
  })

  return (
    <div className="table-shell" role="table" aria-rowcount={products.length + 1}>
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
