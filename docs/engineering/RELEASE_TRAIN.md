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

## Branch-only cache corrections after v2026.11.1.1

The private Home Assistant 2026.10.4 diagnostics from installed
`v2026.11.1.1` show a successful BE `MODEL` account fetch and **24
electricity but only 6 gas customer price slots for 2026-11-01**.
That is valid *partial source evidence*, not proof of a complete gas
price day. Finance is still opt-in disabled.

The source audit found two deterministic tomorrow-cache defects:

- The date validator used `electricity or gas`. Because an empty
  `PriceData` object is truthy, gas-only caches could be rejected
  even when valid; nonempty electricity could hide stale gas dates.
  The validator now checks **all actual entries across both segments**.
- Once any tomorrow prices were cached, same-day retries stopped, even
  when a subscribed gas stream covered only part of the calendar day.
  The branch now checks actual UTC interval coverage against the
  selected local calendar day (including DST transitions) and retries
  incomplete subscribed segments at the existing coordinator cadence.
  Cached partial readings remain usable meanwhile. Repeated fetches
  do not spam a new `tomorrow_prices_available` event.

Synthetic tests cover gas-only, both-segment stale data, partial
six-hour gas, full-day caching, and 23/25-hour DST boundaries.
**These changes are after the immutable HACS TEST tag** and are not
present in the installed `v2026.11.1.1` build. They require new
exact-head CI, a later **new** versioned test candidate using the
standard release lifecycle, and real HA/Recorder acceptance.

Do not merge or mark issues #11/#15 and real HA entity-status
acceptance closed on the basis of these tests.

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


## 2026-11-01 — Belgian electricity + gas monthly cost truth

The authenticated BE `MODEL` contract already returns `monthSummary`,
`periodUsageAndCosts`, and `invoices`; **none of these being present proves
an amount, a fresh gas reading, or a final invoice reconciliation**. The
`monthInsights` endpoint is opt-in and must be exercised on a new candidate;
the installed immutable HACS TEST `v2026.11.1.1` still has the option OFF.

Branch work on PR #18 (not installed in HA yet):

- `MonthInsights` now offers **actual total through last meter reading**
  and **expected cost through last meter reading**, distinct from the projected
  full-month total, electricity and gas actual costs, expected breakdown,
  feed-in and volume in the vendor-reported unit.
- The pinned Python API client converts missing numeric fields to `0.0`.
  The existing bounded GraphQL observer captures **raw field status** (missing,
  null, zero, positive, negative) for each requested month. The financial
  snapshot now carries that same-period provenance. A parsed zero is valid only
  if the raw field was explicitly zero. Missing, null, malformed and parser-
  inconsistent fields are unavailable, not zero. No raw money, meters, site
  references, tokens or invoice identifiers are recorded in diagnostics.
- `finance_audit` reports each metric's quality without private amounts.
  `source_total_reconciliation` compares MonthInsights and MonthSummary
  **only if both source meter-reading cutoff dates match**; a match within
  five euro cents is **source agreement, not invoice reconciliation**.
  A disagreement or cutoff mismatch stays explicit. The API may update
  electricity and gas at different times, so same-cutoff evidence matters.
- The gas kWh and m³ readings stay separate (never converted without an
  actual conversion factor). Fixed costs are not invented from a tariff,
  and projected feed-in is not double-counted or given an inferred sign.
- Strings, English and Dutch translations have been added for the new
  total/cutoff sensors, retaining the existing service device and entity IDs.

**Important billing-model distinction:** a real Belgian Frank Energie
statement (checked privately, not copied into this public repository) confirms
that one invoice may combine a previous consumption month's settlement with
an advance for a later month. For example, an October-dated statement may
settle September consumption while charging a November advance. There is no
universal M+2 consumption settlement rule to assume. Invoice `TotalAmount`
is a **payment/settlement balance**, not a period's all-in energy cost.
Electricity and gas actual usage costs, fixed charges, feed-in, taxes,
capacity charges and net fees must be checked against the relevant detailed
settlement lines for the same consumption period. Do not store or reproduce
private invoice identifiers, locations, account numbers or meter identifiers.

### Still required to accept a reliable financial overview

1. Exact-head CI (Ruff/Flake8/pytest/quality/links) all green; then publish a
   controlled new HACS TEST version through the existing release lifecycle.
   Do not modify previous test tags, merge main or promote stable prematurely.
2. On a real BE account, enable monthly finance for the test candidate and
   capture **redacted** diagnostics with two MonthInsights source periods.
   Validate `source_field_presence_verified` and metric quality for
   electricity, gas, fixed and feed-in; confirm HA entity registration and
   actual states. A source missing cost breakdown means explicit unavailable.
3. Require source cutoff comparison: `matched_within_5_cents` (when dates
   coincide), or resolve `provider_totals_disagree`; dates that differ mean
   comparison is deferred. Check the freshness of the gas meter specifically.
4. Compare the available period-specific **settlement lines** (not the
   invoice payment total) with the actual consumption-month totals. Verify which Belgian
   network, capacity, fixed, levy and VAT components are included. A normal
   installment payment is not proof of consumption-month cost. Do not label
   forecast or vendor month-insight totals as `invoiced` until reconciled.
5. Validate month rollover (including year boundary), partial data, signed
   feed-in, zeros, gas excluded, failed APIs, HACS reload and rollback. Recorder
   / historical entity behavior is still **unverified** in a live instance.

**Release gate: BLOCKED.** Synthetic tests establish source-contract behavior
but the account's raw MonthInsights fields, source total agreement, meter
freshness and Belgian M+2 invoice reconciliation are not yet proven. Finance
remains opt-in; the installed version and existing releases are untouched.

## 2026-11-01 — current-day runtime gap / controlled HACS TEST 2026.11.1.2

Re-reviewed the **actual latest installed HA 2026.10.4** diagnostic export for
HACS `2026.11.1.1` at approximately 00:21 Europe/Brussels on 1 November.
The selected BE MODEL site has both subscriptions enabled; 24 customer
electricity hours and **only six gas price hours** for 2026-11-01. Gas
`last_meter_reading_reported=false` is absent contract metadata, not evidence
of a zero meter reading. Finance remains opt-in OFF, and HA states/Recorder
are not evidenced in that export. Earlier 2026.10.31.2 diagnostics had
incorrect false subscription flags and empty contract segments, now corrected.

A source-code/root-cause review identified a second coverage bug after the
already patched tomorrow cache: today's price fetch ran once per local day
regardless of subscribed gas gaps. This would freeze the six-hour gas source
until next midnight. The single PR #18 now retries **incomplete today** at
the existing cadence, preserves the better previous current-day segment
on a shorter API response, and avoids invalidating hourly MODEL customer
data simply because the public query preference is PT15M. Regression tests
use real timestamped PriceData on selected-site and DST-aware paths.

CI governance is no longer version-specific: obsolete
`publish-integrated-hacs-test.yml` and
`publish-graphql-hacs-test.yml` were removed from the active branch.
`publish-qualified-hacs-test.yml` consumes
`docs/candidates/TEST_RELEASE_CANDIDATE.json` and requires all central
exact-commit CI checks plus HACS/Hassfest before an immutable TEST tag.
It does not merge `main`, alter earlier tags, or authorize a stable release.
See `docs/candidates/2026.11.1.2.md` for the exact live HA acceptance evidence.

**Release promotion remains BLOCKED by real HA/Recorder, source finance
reconciliation, and HACS rollback evidence.** Do not interpret a successful
synthetic test or published test ZIP as stable acceptance.


### HACS TEST 2026.11.1.3 — midnight automatic recovery (2026-11-01)

After installing v2026.11.1.2, real HA diagnostics showed 129/144 entities
unavailable, site segments false, missing electricity/gas prices and finance
data, while all three coordinators claimed success. The in-app Refresh Prices
button subsequently populated real electricity all-in and market rates;
HA's empty Activity panel is *not* a GraphQL request trace.

**Root failure:** the aligned timer only pushed cached sensor states outside
13:00-15:00 local, missing the opportunity to heal a stale/empty coordinator
after the provider's 00:00-01:00 UTC maintenance window. Authenticated
UserSites unavailable was also accepted as a successful empty settings
update; automatic API JWT rotation did not persist renewed credentials.

**Corrections:** hourly recovery for missing selected-site metadata, wholly
missing finance sources, and missing/stale/incomplete today prices; no
requests during documented UTC maintenance; privacy-safe scheduler
outcomes in the diagnostics trace; fail closed on missing authenticated
UserSites rather than reporting a false successful contract empty state;
persist successful automatic token rotations without making duplicate
config writes; runtime health and warnings in diagnostics. Do not confuse
price-button success with validation of gas/finance sources.

**Release gates:** existing exact-SHA CI, Ruff, HACS, Hassfest, deterministic
ZIP/checksum and immutable prerelease workflow; test actual new-day recovery,
HACS install/reload, gas/price coverage, monthly finance and HA Recorder
separately before stable. PR remains Draft; main untouched.


### 2026-11-01 — refresh source truth, tariff clock and calendar-month correction

Source-only changes on the same draft PR #18 after the installed immutable
HACS TEST v2026.11.1.3. These changes are **not installed or accepted** on the
target Home Assistant instance; do not infer a new published version.

- **Provider refresh:** the price coordinator's dynamic
  `DataUpdateCoordinator.update_interval` is the only routine price polling
  mechanism. It retains its existing conditional publication/retry cadence,
  including the 13:00–15:00 local publication window. The aligned quarter-hour
  clock no longer issues duplicate routine price API requests.
- **Business time:** the aligned clock advances local tariff slots, cached
  midnight price promotion and lowest-price events independently of provider
  network requests. It publishes only on the real source interval (PT15M,
  PT60M or the shortest valid interval when electricity/gas differ); it does
  not manufacture Activity events.
- **Startup truth:** valid disk-cached prices receive a positive fallback
  polling interval and are published through the supported coordinator API;
  a cache hit is not a reason to leave the coordinator without polling.
- **Fetch truth:** `last_fetch_today` is never moved forward when the price
  provider returns no usable data and the integration falls back to the old
  cache. The next provider retry remains eligible.
- **Recovery truth:** scheduler outcomes use `refresh_ok` only after
  coordinator success **and** the expected source data is present. An
  incomplete recovery is explicitly `refresh_incomplete`, even if the
  request itself returned normally. The diagnostic outcome is privacy-safe.
- **Finance period truth:** all seven legacy MonthSummary cost sensors,
  including the real total "actual cost until last meter reading" and the
  three explicitly labeled "this month", require a last-meter-reading date
  in the current local calendar month. Previous-month readings are
  `unavailable`, **not** fabricated November costs; actual current-month
  zero remains valid. Previous-month data belongs to explicit, period-keyed
  MonthInsights, not an unlabeled legacy monthly cost. Invoice payment/advance
  metadata is no longer attached to monthly forecasts.
  Bounded diagnostics now report whether the meter-reading period matches the
  current local month (`true`, `false` or unknown), without including the
  private meter-reading date or any monetary amount.
- **Regression tests:** diskcache startup liveness, 15/60-minute source
  transitions, mixed electricity/gas resolution, no extra provider API calls
  from the aligned clock, empty-source retry eligibility, real-vs-false recovery,
  rollover dates/UTC-local boundaries and explicit zero.

### Service-device refresh controls (TEST candidate, not released)

- Existing functional devices receive a refresh button for each present
  source group: Prices, Gasprices (when applicable), Costs, Usage, User and
  available Batteries, Chargers, Vehicles and Solar Systems.
  Prices keeps its existing `refresh_prices` unique key. Battery Sessions
  keeps its existing dedicated button.
- Costs and Usage correctly share the Statistics coordinator; Prices and Gas
  Prices share the price coordinator. Buttons therefore request refresh of
  the real source rather than inventing independent provider polling.
- A new diagnostic **Refresh interval** sensor per service shows the live
  coordinator `update_interval` in **minutes**. This can change dynamically
  (especially during tomorrow-price publication). A missing interval reports
  unavailable; it is not interpreted as a zero-minute timer.
- Both the button and interval sensor expose **last API request**,
  **last successful API response**, **latest API outcome** and **next estimated
  refresh** as privacy-safe attributes. The estimate is explicit: internal
  Home Assistant scheduling, provider maintenance (00–01 UTC), optional
  endpoint caching and manual refreshes can shift the real deadline.
  An HTTP/GraphQL success does **not** prove complete supplier readings.
- Price slot state changes (15/60 minute boundaries) are explicitly separate
  from network API polling. Cached price fetch timestamps are exposed as
  source provenance, not passed off as current API requests.
- Service timing also appears in diagnostics under
  `coordinator_evidence.refresh_schedule`. The diagnostic event window
  is limited to the most recent 96 requests since restart; missing evidence
  becomes `null`, never a fabricated timestamp.
- Diagnostic interval sensors are registered with
  `update_before_add=False` to avoid triggering any additional provider
  requests just to display the timer. Tests cover dynamic intervals,
  missing evidence, present/absent services and manual source routing.
- This remains a **TEST branch implementation** until the exact-head CI and
  real HA device/Recorder/reload verification pass. No stable release or
  main-branch promotion is implied.

**Remaining work:** pass exact-head Python 3.14/3.14.2 pytest, Flake8, Ruff,
Quality Scale and Link Check. Confirm full HA/HACS/Hassfest release gates,
new-day recovery and source coverage (both electricity and gas), authenticated
MonthInsights field-level truth, actual entity states, Recorder history,
reload/rollback, and period-specific invoice component reconciliation. Monthly
finance stays opt-in and unaccepted. This PR stays **Draft**, `main` remains
untouched, and prior TEST tags remain immutable.
