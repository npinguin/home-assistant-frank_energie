# Frank Energie fork — single release train

**Current delivery track:** one consolidated draft PR **#18** from branch
`fix/be-price-provenance-truth` into `main`. The branch name is historical;
**do not create new work branches for follow-up fixes on this release train**.
Make targeted commits and tests on the same PR. Each issue retains its own
tracking and acceptance evidence.

**Source baseline:** immutable HACS TEST `v2026.10.31.2` at
`0c6a0bcb056a2e4a555cb5b06d982abbd57f23de`.
That **tag and ZIP are frozen**, including `v2026.10.31.1`.
**Main is not promoted** merely because a pre-release exists. The
next *stable* version is assigned only after full release acceptance. The
controlled next HACS **TEST** candidate is `v2026.11.1.1`; this is
versioned before live acceptance precisely to obtain new diagnostics.
The test release publisher is scoped to this single branch and exact-SHA
CI, HACS/Hassfest and immutable ZIP/checksum verification.

## HA device freshness after installing v2026.11.1.1

A follow-up live HA 2026.10.4 diagnostics export confirms the immutable
2026.11.1.1 test candidate is installed and its selected-site flags
(`electricity=true`, `gas=true`) and BE `MODEL` dataclass metadata are
correct. It was captured around 00:21 Europe/Brussels on 2026-11-01.

- All three coordinators have `last_update_success=true` and source
  GraphQL operations respond. This **does not establish** that an individual
  HA sensor has a current value, or that provider readings are recent.
- For 2026-11-01 the effective customer source contains **24 hourly
  electricity prices and 6 hourly gas prices**. `last_fetch_tomorrow=null`
  is expected around midnight; next-day prices are not due before the
  publication window.
- `MonthSummary`, `Invoices`, and `PeriodUsageAndCosts` objects exist,
  but the old diagnostics show only **object presence**, not actual usage
  segment values, invoice age or last meter reading age.
- Monthly finance remains opt-in OFF, so no monthly finance entities are
  registered. Do not create artificial monthly totals or enable unstable
  finance just to make the HA device appear populated.
- A source-code audit against HA Core 2026.10.4 confirms
  `CoordinatorEntity._handle_coordinator_update` writes state and the
  existing `FrankEnergieSensor.native_value` **already computes the current
  coordinator data**. Do not introduce a second manual refresh or rewrite
  this working contract merely because a user's device page shows no
  recent activity; HA's `last_changed` is not `last_reported`.
- **Real device defect:** the `meterType` sensor's per-segment extractor
  discarded all actual pinned-client `Connection` dataclasses, even though
  those source values exist. Fixed against `Connection.from_dict` fixtures
  in the same PR, retaining sensor identity.
- Added strictly sanitized evidence: age of the source last meter
  reading, per-segment usage item counts and reported-total presence,
  count/latest age of invoices, current price-slot presence, and actual
  HA entity availability and last-report recency grouped by whitelisted
  service names. No account IDs, values or provider-supplied arbitrary
  device names are exported.

**Next acceptance:** after a **standard-lifecycle** test candidate is
published from these changes, capture HA diagnostics and compare the
`ha_entity_state_summary.by_service`, `provider_data_freshness`,
`price_coverage.has_current_price` fields. Confirm individual price,
meter, cost and usage entity states and Recorder writes; only then
attribute absent values to upstream delay, sensor parsing or registry
configuration. Preserve `main`, published tags and all existing unique IDs
until verified.

## Governance correction — v2026.11.1.1 (2026-10-31)

**Published HACS prerelease**, immutable tag at
`dc4af1cd3f829c5072e6c6639e6b5d65f0ce930b`; the published
`frank_energie.zip` and `SHA256SUMS.txt` remain unchanged.

**Release governance exception:** this test candidate was published via a
temporary version-specific `publish-consolidated-hacs-test.yml` workflow
rather than the agreed shared release lifecycle. The independent Ruff job
encountered a GitHub checkout/network failure; the publisher used its own
blocking Ruff lint and format checks instead. Python 3.14/3.14.2,
Quality Scale, Link Check, HACS, Hassfest, deterministic ZIP creation and
checksum checks passed in that exact-source publisher. Thus **artifact
validation passed, standardized workflow compliance did not**. Do not
call this an accepted stable or fully standardized release.

The ad hoc publisher and its release-specific test have been **removed
from the active PR #18 branch** after publication. They remain in the
immutable tagged commit for audit. No new release tag is created by this
reversion, and `main` is not merged.

For **future** test/stable releases, reuse a single reviewed version-neutral
release workflow and exactly the same mandatory checks for both. A
failed/unavailable central gate is a blocker requiring diagnosis/rerun;
do not create release-specific workflows or bypass central requirements.
Do not publish from `main` until runtime acceptance. PR #18 stays Draft
until actual BE HA installation, diagnostics, Recorder and rollback are
validated. New code changes after this tag require a new immutable
candidate version when next released.

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
7. **Promotion:** PR #18 is the only merge candidate. The controlled
   `v2026.11.1.1` prerelease may be published to gather real HA evidence
   once exact-SHA CI, HACS/Hassfest and packaging validation pass. Keep #18
   **Draft** and `main` unchanged until all live acceptance gates pass.
   For any *subsequent* test or stable release use a **new immutable version**.
   Document rollback, limitations and excluded functionality.

## Live BE diagnostics observed from installed 2026.10.31.2

Private HA 2026.10.4 diagnostics confirm **both** independent public
`marketPrices` and authenticated `customerMarketPrices` endpoints return
parseable source slots for current and next day. Today's customer source has
24 electricity and 24 gas records; tomorrow has 24 electricity and **6**
gas records. This is not automatically full next-day gas coverage: the
actual timestamp intervals and publication timing still need to be checked.
The selected effective streams carry 48 electricity and 30 gas records at
reported 60-minute resolution despite the independent public query
requesting 15-minute resolution.

The same export proves two implementation issues, fixed on this single
release PR with synthetic regression tests:

- **Wrong price-coordinator segment flags:** prices exist but
  `user_electricity_enabled` and `user_gas_enabled` are False because
  only the settings coordinator fetches UserSites. Price fallback now
  derives the flags from **the selected delivery site**, without
  cross-site inference.
- **Empty contract metadata:** the pinned client supplies
  `Connection` dataclasses, but the diagnostics extractor previously
  accepted only dictionaries. BE MODEL meter/contract metadata is now
  extracted from both representations while excluding identifiers.

Diagnostics now also exposes `has_active_today_prices` separately from
the legacy `has_cached_today` field, and effective
`price_coverage.*.slots_by_local_day` (bounded counts, not prices). A
successful API response or 6 slots does not establish full day coverage.

`MonthSummary`, `Invoices` and yesterday `PeriodUsageAndCosts` have
source response objects. `MonthInsights` is not called because monthly
finance remains opt-in disabled, **not because the endpoint was proven
unavailable**. One nonfatal `SmartHvacStatus` exception is observed;
no source evidence yet establishes its cause or that the user has an HVAC
product configured.

### Required next acceptance

- [ ] New diagnostics after the consolidated code is installed: selected
      site flags correct, electricity/gas MODEL contract segments populated,
      no private identifiers or monetary values in export.
- [ ] Verify timestamp coverage of customer gas prices for tomorrow, not
      only slot count. Confirm fallback provenance when one source fails.
- [ ] Confirm actual `has_active_today_prices`, daily counts and
      60-minute selected customer resolution on BE account.
- [ ] Only after explicit enablement and source-contract fix #11, inspect
      `MonthInsights` against real current/previous months and invoices.
- [ ] Confirm SmartHvacStatus is an optional unsupported endpoint or an
      actionable integration defect; do not infer from one exception.

## Working rule

**One active branch + one active release PR + separate GitHub issues.**
Fix the owning code and add a regression test before checking an issue off.
Keep acceptance and blockers in this file and the PR; never scatter release
readiness across independent PR comments. Do not rebase/rewrite a published
test-release tag. Do not call a draft candidate stable.
