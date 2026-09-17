# Xoso88 Operations Checkpoint

This file is the persistent handoff/checkpoint for collector verification. Do not restart a resolved stage unless new evidence reopens it.

## Current stage

**Stage: trusted write authentication**

The collector has already passed URL normalization and the Supabase REST connectivity probe. The current blocker is the credential stored in GitHub Actions.

## Verified evidence

- Repository: `duykhanhrungnhum-debug/X-s-88`, branch `main`.
- Supabase project: `mwdlwvychuolybbfvyem`.
- GitHub Actions run `35197193078` / job `105123111349` passed the Supabase REST probe and then failed at `source_fetches` INSERT with PostgreSQL error `42501` because the active request did not satisfy RLS.
- GitHub Actions run `35197556172` / job `105124284049` used commit `63aa3fbd467e7cc01bdd9f37a891c82c6e0d94ca` and classified `SUPABASE_SERVICE_ROLE_KEY` as a **publishable key** (`sb_publishable_...`). The workflow stopped before any database write.
- Direct database inspection shows RLS is enabled on all five Xoso88 tables and `relforcerowsecurity` is false. The intended elevated `service_role` role has INSERT grants; the public `anon` role also has table-level INSERT grants, but no INSERT RLS policy is intended for internal tables.
- Database row counts were zero at the last direct inspection.
- Supabase documentation currently distinguishes publishable keys (low privilege, RLS-controlled) from secret keys (elevated, server-side, bypass RLS). Legacy `service_role` is the older equivalent of a secret key and is being deprecated by the end of 2026.

## Resolved stages — do not loop back

1. Supabase URL containing `/rest/v1/` caused malformed client paths/PGRST125. Fixed by normalizing the URL before `create_client()`.
2. Collector fetch failure status `error` was invalid for the database enum. Fixed to `failed`.
3. Province code normalization now removes Vietnamese diacritics before generating stable ASCII keys.
4. REST probe now accepts either project-root URL or a URL ending in `/rest/v1`.

## Exact next action

Replace the GitHub Actions secret named `SUPABASE_SERVICE_ROLE_KEY` with an **elevated server-side Supabase credential** from the project's API Keys settings:

- preferred current format: `sb_secret_...`
- legacy accepted format: JWT with `role=service_role`

Do **not** use `sb_publishable_...` for the collector. Do not add an RLS INSERT policy merely to make the collector work; that would turn the public credential into a data-writing credential.

After the secret is corrected, rerun the collector for `2026-09-15` and verify in order:

`credential -> REST probe -> Minh Ngoc fetch -> parse -> validation -> source_fetches -> provinces -> draws -> results -> validation_events -> Edge Function -> website`

Only mark the stage complete after the corresponding runtime evidence is present.
