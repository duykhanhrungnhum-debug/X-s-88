# Xoso88 Operations Checkpoint

This file is the persistent handoff/checkpoint for the production collector and website. Do not restart a resolved stage unless new evidence reopens it.

## Current stage

**Stage: production hardening and SEO expansion**

The end-to-end path is working:

`Minh Ngoc public result page -> parser -> validation -> Supabase -> public REST read -> GitHub Pages`

The website displays real published results. The current work is no longer basic connectivity; it is reliability, history navigation, province landing pages, SEO, and future ad-readiness.

## Verified evidence

- Repository: `duykhanhrungnhum-debug/X-s-88`, branch `main`.
- Supabase project: `mwdlwvychuolybbfvyem`.
- GitHub Pages production URL: `https://duykhanhrungnhum-debug.github.io/X-s-88/`.
- Pages deployment run `35539146729` / job `106153504110` completed **success**.
  - static province-page build: success
  - GitHub Pages deployment: success
  - public results API check: success
  - deployed homepage check: success
  - deployed Tây Ninh province-page + sitemap check: success
- Latest workflow validation run `35539247016` / job `106153774178` completed **success** with **40 passed**.
- Collector validation run `35539247062` / job `106153774494` completed **success** after the polling-window change:
  - server credential diagnostic: success
  - Supabase REST probe: success
  - three regions processed sequentially: success
- Live-source parser smoke run `35538144760` completed **success** after exact province/prize-cardinality checks were added.
- Recent-data repair run `35538154308` completed **success** after deleting and recollecting 17-20 September 2026 with the corrected parser.
- Direct database verification after repair found no Central/South prize rows with invalid number cardinality for 17-20 September 2026.
- Province codes are now canonical ASCII slugs, including `da-nang`, `dak-nong`, `dong-nai`, `da-lat`, and `tp-hcm`.

## Production website behavior

- Main page defaults to the latest date with verified data for the selected region.
- Region/date state is shareable through URL query parameters.
- Recent verified dates are shown as quick history controls.
- Each result card links to a permanent province history URL under `/tinh/<province-slug>/`.
- Each result card exposes the original public source URL for manual comparison.
- Province landing pages are statically generated at deploy time for all configured provinces.
- `/tinh/` provides a province directory.
- `robots.txt`, canonical metadata, Open Graph metadata, JSON-LD and the generated sitemap are present.
- The browser reads only rows allowed by public RLS rules; write credentials remain server-side.

## Collector safeguards

1. Source request spacing is at least five seconds between regions in the GitHub workflow.
2. Scheduled runs use the Vietnam calendar date, not the runner's UTC date.
3. Daily parsing filters to provinces scheduled for that weekday.
4. Repeated province/prize widgets on the source page are deduplicated so historical/sidebar numbers are not merged into the current draw.
5. Source-date mismatch is treated as a normal "not published yet" state during scheduled collection.
6. The regular polling schedule is limited to **16:00-20:59 Vietnam time** (`09:00-13:59 UTC`) at ten-minute intervals; manual dispatch remains available for backfills.

## Resolved stages — do not loop back

1. Supabase URL normalization / malformed REST path issue.
2. Invalid collector fetch-status enum.
3. Missing elevated write authentication and RLS confusion.
4. Collector field mismatch (`PrizeRow.prize_name` vs `PrizeRow.prize`).
5. Browser-to-Edge-Function connectivity loop.
6. GitHub Pages deployment uncertainty.
7. Province metadata mapping mismatch in the frontend.
8. Parser contamination from unrelated province widgets.
9. Repeated historical province/prize rows being appended to current results.
10. UTC date drift for scheduled GitHub runners.
11. Broken Vietnamese slugging for `Đ/đ` and punctuation.

## Next development priorities

1. Preserve the currently verified collector and public-results path; do not rewrite it without evidence of a new failure.
2. Continue expanding useful long-term history while keeping stable province URLs.
3. Add performance and layout improvements without breaking mobile result readability.
4. Keep the static GitHub Pages architecture compatible with future advertising scripts and a custom domain.
5. Continue to treat a stage as complete only when CI/runtime evidence exists.
