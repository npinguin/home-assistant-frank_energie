# Frank Energie fork — single release train

**Current delivery track:** one consolidated draft PR **#18** from branch
`fix/be-price-provenance-truth` into `main`. The branch name is historical;
**do not create new work branches for follow-up fixes on this release train**.
Make targeted commits and tests on the same PR. Each issue retains its own
tracking and acceptance evidence.

**Source baseline:** immutable HACS TEST `v2026.10.31.2` at
`0c6a0bcb056a2e4a555cb5b06d982abbd57f23de`.
That **tag and ZIP are frozen**, including `v2026.10.31.1`.
**Main is not promoted** merely because a pre-release exists. The next
release version is assigned only after release acceptance.

## Consolidation ledger — no lost fixes

| Historical PR | Change | Delivery in consolidated PR #18 | Legacy PR policy |
|---|---|---|---|
| #1 | Anonymous public price requests on authenticated accounts | Included via prior integrated test baseline #13/#17 | Superseded; preserve history |
| #4 | Anonymous-to-login reconfiguration | Included via baseline #13/#17 | Superseded; preserve history |
| #5 | BE MODEL/SMR enums and HA setup repairs | Included via baseline #13/#17 | Superseded; preserve history |
| #7 | Opt-in monthly finance | Included via #13/#17, **source zero issue #11 still open** | Superseded implementation; do not declare finance accepted |
| #13 | Published HACS TEST v2026.10.31.1 | Included in v2026.10.31.2 and #18 ancestry | Historical immutable candidate |
| #14 | BE contract & privacy diagnostic repairs | Included via v2026.10.31.2 ancestry | Superseded implementation |
| #16 | Real GraphQL source-observation diagnostics | Included via v2026.10.31.2 ancestry | Superseded implementation |
| #17 | Published HACS TEST v2026.10.31.2 | Exact frozen ancestor of #18 | Historical immutable candidate |
| #12 | CI event labeler and obsolete Pages workflow removal | Files/tests copied into #18 (Ruff workflow already identical) | Superseded implementation |
| #18 | Correct price source/cache provenance, release consolidation | **Single active release PR** | Remain Draft until all gates green |

The original PRs and immutable tags remain as audit evidence. **Do not merge
historical branches separately** after #18 is promoted; doing so can reintroduce
older code and create release drift. Reopen only after a concrete omitted
delta is proven against the full file tree.

## Single source of release truth

- **Implemented but not live accepted:** BE variable `MODEL` contract
  identification, HACS diagnostics and public/customer price source separation,
  opt-in monthly finance, anonymous-to-authenticated reconfiguration.
- **Outstanding blocking evidence:** 
  - #11 — upstream `python-frank-energie` `MonthInsights` parser maps
    absent/null numeric fields to `0.0`. The HA integration conservatively
    withholds zero. Do not claim correct monthly costs or publish finance as
    stable until a pinned, versioned source fix or formally validated
    equivalent source contract is available.
  - #15 — validate real Belgian `MODEL` variable tariff independently
    from public spot-price data, price provenance, gas readings and
    source/provider publication lag in HA.
  - #2/#3 — actual HA BE entity/contract and preserved config-entry migration
    acceptance, not just synthetic tests.
  - #6 — actual HACS prerelease install/update/rollback path including
    ZIP availability, registry preservation and prior-download behavior.
  - #9/#10 — CI cleanup consolidated; confirm event behavior and exact-head
    workflow checks after merge candidate.
- **Scope boundary:** a public spot feed may inform planning as a market
  signal, but is not the invoice rate of a Belgian variable `MODEL` contract.
  The provider's gas meter codes are not proof of meter hardware semantics.
  Unknown costs or delayed readings must remain unavailable, not zero.
- **No entity-ID reuse, Recorder backfill, fictitious capacity tariff,
  hidden second integration, or undocumented new API polling.**

## Release gate (all required, evidence linked in PR #18)

1. **Code:** exact-head Python 3.14 and 3.14.2 pytest/Flake8; Ruff
   lint/format; Quality Scale and Link Check. No red checks.
2. **HA packaging:** HACS, Hassfest, manifest dependency pin, ZIP structure,
   checksums and version/source SHA traceability. No tag overwrites.
3. **Configuration lifecycle:** anonymous setup, login, reload, site choice,
   stable config-entry ID, device/entity registry/unique IDs, restart, recovery.
4. **Pricing:** authenticated and anonymous source isolation, actual raw and
   parsed price slots, today/tomorrow, unavailable/cache behavior, variable
   contract versus public market semantics.
5. **Finance:** current/previous month rollover and caching, zero versus
   missing, separate gas units, import/feed-in signs, invoice comparison and
   no spurious historical statistics. Existing monthly feature stays opt-in OFF
   until independently accepted.
6. **Live Home Assistant:** actual BE installation checks including diagnostics
   privacy, actual provider source evidence, HA Recorder, HACS install/update
   and rollback. Synthetic green tests are not runtime proof.
7. **Promotion:** PR #18 is the only merge candidate. Freeze its exact
   accepted commit, choose a **new version**, publish immutable signed-off
   test/stable assets as appropriate, and update `main` only after gates.
   Document rollback, limitations and what was deliberately excluded.

## Working rule

**One active branch + one active release PR + separate GitHub issues.**
Fix the owning code and add a regression test before checking an issue off.
Keep acceptance and blockers in this file and the PR; never scatter release
readiness across independent PR comments. Do not rebase/rewrite a published
test-release tag. Do not call a draft candidate stable.
