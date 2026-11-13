# Dependencies

`just setup-dependencies` installs the dependencies from `pnpm-lock.yaml` with `pnpm install --frozen-lockfile`, for `just setup` and CI alike.

The store: every worktree installs from one shared pnpm content store outside the worktree, pnpm's default store (`pnpm store path`, on Linux `~/.local/share/pnpm/store`), never a per-worktree one. No `store-dir` is set in `.npmrc` or on the install, so a second worktree adds links and metadata, not a second store. A `.pnpm-store` left in a worktree by an older setup can be removed once that worktree is re-linked: run `CI=true just setup-dependencies` there, check `storeDir` in `node_modules/.modules.yaml` names the shared store, then delete the `.pnpm-store`. `test/setup-shared-store.test.ts` drives this recipe offline in a scratch checkout.
