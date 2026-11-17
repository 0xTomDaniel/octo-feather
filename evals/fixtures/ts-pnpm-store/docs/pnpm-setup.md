# Dependencies

`just setup-dependencies` installs the dependencies from `pnpm-lock.yaml` with `pnpm install --frozen-lockfile`, for `just setup` and CI alike.

The store: each worktree installs into its own `.pnpm-store` (`store-dir=.pnpm-store` in `.npmrc`), so worktrees never share installed files.
