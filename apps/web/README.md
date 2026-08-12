# Web app

The React source uses a feature-based structure:

```text
src/
├── app/                 # Application shell and route composition
│   ├── AppLayout.tsx
│   └── router.tsx
├── features/            # Code grouped by product capability
│   ├── auth/            # Authentication API and components
│   ├── dashboard/       # Dashboard pages
│   └── products/        # Product API, components, and pages
├── shared/              # Reusable UI and utilities
│   ├── components/ui/   # shadcn/ui components
│   └── lib/             # Shared helpers such as `cn`
├── index.css            # Global styles
└── main.tsx             # Application entry point and providers
```

Each feature exposes its public API through an `index.ts` file. Code outside a
feature should import from that public entry point; implementation details stay
inside the feature folder. Within a feature, files are grouped by role (`api`,
`components`, and `pages`) when that role is present.

## UI and form tooling

- Tailwind CSS is integrated through the official Vite plugin.
- shadcn/ui is configured in `components.json`; add components with
  `pnpm --filter web exec shadcn add <component>`.
- Zustand, Zod, React Hook Form, and the Zod resolver are available to features.

## Code quality

- `pnpm --filter web lint` checks the app with Oxlint.
- `pnpm --filter web lint:fix` applies safe lint fixes.
- `pnpm --filter web format` formats supported files with Oxfmt.
- `pnpm --filter web format:check` verifies formatting without changing files.
