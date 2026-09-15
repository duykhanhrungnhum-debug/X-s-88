# Supabase

Xoso88 uses Supabase PostgreSQL as the primary persistent store.

## Migration

Apply migrations in chronological filename order with the Supabase CLI:

```bash
supabase db push
```

The initial migration creates:

- `lottery_provinces`
- `lottery_draws`
- `lottery_results`
- `source_fetches`
- `validation_events`

## Security model

Row Level Security is enabled on every application table.

The public website can read active provinces and only published/validated draws and their results. There are intentionally no public write policies.

Collector/backend writes must use a trusted server-side Supabase credential stored outside the repository (for example, GitHub Actions secrets or deployment secrets). Never commit a Supabase service-role key or other secret to Git.

## Verification status

This migration has been committed to GitHub, but it has **not** been executed against a real Supabase project yet because no Supabase project connection has been provided. Therefore Xoso88 does not claim that the remote database has been created or migrated.
