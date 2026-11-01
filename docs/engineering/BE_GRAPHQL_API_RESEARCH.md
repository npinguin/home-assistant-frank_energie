# Belgian Frank GraphQL API research — verified scope and probe gates (2026-11-01)

**Status: discovery / controlled test; not a released or accepted API extension.** Continue in Draft PR #18 without editing immutable HACS TEST `v2026.11.1.7`.

## Evidence hierarchy

- Real target HA OS 2026.10.4 diagnostics, Frank `v2026.11.1.7`, Python client pin `python-frank-energie==2026.9.20`. Observed at 2026-11-01 13:08 UTC: account authentication and site selection work; account `MarketPrices` for Nov 1 returned 24h electricity+gas; Nov 2 returned 24h electricity+6h gas; public market returns 96 electricity quarters and no gas. Price selection = customer; this is not proof of a verified invoice rate.
- Account `MonthInsights(2026-11)` returned a GraphQL error with `monthInsights:null`; `MonthInsights(2026-10)` returned a model with `gasExcluded:true`/null gasDifference. Previous-day `PeriodUsageAndCosts` returned electricity/feed-in usage but no gas and no cost totals. No raw messages or account data are needed in CI.
- Upstream Python client `v2026.9.20` is the installed release, not the 41 commits newer `main`. Inspect **pinned tag** when establishing current API behavior. Upstream `main` contains later auth handling; do not update the pin without full tests.
- Upstream query `MonthInsights($date:String!,$siteReference:String!)` already exists. An error from the API is different from missing fields being coerced to `0.0` in `MonthInsights.from_dict`.
- Other existing client methods include `meter_readings` (a query that still needs schema/response validation), `period_usage_and_costs`, `month_summary`, `invoices`, `user_prices`, `contract_price_resolution_state`, smart service endpoints. Availability of a method does **not** establish support for this Belgian MODEL account.
- Official Frank Energie Belgium 'Export van factuurdata' webpage documents a CSV to audit **settled** invoice price components and notes that final costs may not be available until M+2. Its column explanations refer to Dutch contracts: independently verify availability/fields for this Belgian account before writing a parser or asserting period comparability.

## Official Belgian contract semantics — essential guardrail

Frank Energie's Belgian help pages explicitly distinguish **variable** and **dynamic** electricity contracts:

- Variable: consumption is settled at a monthly/periodically calculated price under the contract formula. Moving consumption to a cheap market quarter does not itself reduce the supplier's energy unit price. Smart services may deliver a **separate bonus** that appears on the invoice. [Frank: variabel energiecontract](https://www.frankenergie.be/nl/slimme-diensten/variabel-energiecontract).
- Dynamic: actual hourly/quarter-hour usage and prices can influence settlement. A digital meter plus a valid communicated measurement regime is required. [Frank: slimme meter and variable versus dynamic](https://klantenservice.frankenergie.be/hc/nl-be/articles/19669514031634-Heb-ik-een-slimme-meter-nodig-en-hoe-kom-ik-daaraan).
- The currently inspected account reports `MODEL`/variable, electricity `SMR3` and gas `SMR1`. These metadata are strong context but do **not** establish the exact contractual billing formula. Verify contract documents and app instead of inferring a dynamic invoice from PT15M market prices.
- HA Energy Basic must not calculate claimed arbitrage savings for a variable contract from today's public/selected spot intervals. Separate `market_signal`, `contract_monthly_rate`, and `smart_service_bonus` (only when a source reports it) as different economic quantities. Frank is provider facts; Basic owns settlement and actual home kWh.

## Prioritized experiments (safe and bounded)

| Priority | Question | Test | Accept / reject |
|---|---|---|---|
| P0 | Why does current `MonthInsights` fail? | On normal scheduled request, collect **only** allowlisted GraphQL error category, safe known root and count; distinguish schema validation, non-null violation, upstream unavailable, missing meter read, unknown. Never retain raw error body or credentials. | Add typed provider state, never mask a query failure as €0. No extra requests initially. |
| P0 | Is current-month insight legitimately unpublished? | Compare month changeover to subsequent ordinary polls, previous-month success and reading publication dates. If necessary use a single opt-in read-only probe after provider release. | Evidence-based period status; do not backfill an unsupported month. |
| P0 | Why is gas usage absent despite gas contract and gas prices? | Compare selected gas meter code (`SMR1`), reported last reading, `PeriodUsageAndCosts.gas` presence, and documented account UI data. `meter_readings` is an **unverified API experiment**, not an approved solution. | Do not invent m³/kWh or costs; Basic P1/local meters own household truth. |
| P1 | Is tomorrow 6h gas a publication window or permanent source limit? | Track slot-count/interval coverage on existing 5-minute cadence, until complete or cutoff, including DST; signal partial forecast. | Daily aggregates must not silently represent six hours as a full day. |
| P1 | Can official historical invoice components be reconciled? | **If supported in the user's BE app**, export a redacted settled month CSV and compare per-unit purchase price/markup, amounts, billing period and actual `MonthInsights`. | Evidence-only cross-check; no generic financial engine in Frank. |
| P2 | Other provider features? | Enumerate GraphQL operations exposed in pinned client and app capability, then one feature at a time with typed model, opt-in, privacy, tests and ownership. | No speculative entities, unbounded polling or bypassing account/region restrictions. |

## Implementation/ownership

- New safe diagnostics on Draft PR: `diagnostic_trace.py` recognizes a small, explicit GraphQL error code/message allowlist and whitelisted response roots. Unknown errors are classified `unclassified`; no request body, message, arbitrary extension value, siteReference, credentials or monetary value is stored.
- Future **upstream** client change should retain numeric `None` in `MonthInsights` rather than silently coercing it to zero, with a versioned typed response contract. Historical HA finance adapter must keep `unknown` when unverified.
- Frank adapter owns provider GraphQL, site account, customer/public market streams and provider finance facts. HA Energy Basic owns home P1, gas-meter truth, Flemish grid tariff, cost ledger and household UX. RHI Energy owns generic planning. Avoid framework duplication.
- Do not use broad introspection against private customer endpoints or mobile-app credentials outside the customer's authorized sessions. No automatic high-frequency probes, guessed endpoint calls or auth bypass. Coordinate upstream API schema changes with maintainers where possible.

## Release gate

Await CI of the exact Draft PR source. These diagnostics changes **do not alter immutable v2026.11.1.7**. To see new error categories on target HA, publish a new versioned prerelease after clean tests, then collect **new** diagnostics. Do not claim API bug solved until live evidence identifies it. Stable requires customer invoice/contract truth and HA upgrade/Recorder checks.
