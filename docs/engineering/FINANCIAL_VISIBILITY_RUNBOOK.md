# Financial visibility — engineering runbook and lessons learned

**Scope:** This is the permanent starting point for engineers continuing the Belgian electricity + gas cost visibility objective in the Frank Energie fork and HA Energy Basic. Read [BE_SOURCE_CONTRACTS.md](BE_SOURCE_CONTRACTS.md), [HA_ENERGY_BASIC_SOURCE_CONTRACT.md](HA_ENERGY_BASIC_SOURCE_CONTRACT.md), and [RELEASE_TRAIN.md](RELEASE_TRAIN.md) for architectural contracts and release governance.

## Product definition of done

Show a reliable month-by-month household electricity + gas cost view with electricity import, gas, export/injection credit, supplier fixed costs, network/distribution/transport, capacity tariff, levies, VAT, corrections, one net total, and period-matched invoice reconciliation. Each component must indicate **actual provider amount**, **provider forecast**, **locally calculated estimate**, **not applicable**, or **unavailable**, along with period, unit, cutoff and source. Distinguish consumption month from invoice settlement and payment advances.

**Ownership:** Frank integration is exclusively an authenticated supplier-source adapter; HA Energy Basic owns P1/gas-meter consumption, Belgian DSO/capacity tariffs and the **home cost ledger**; RHI Energy owns generic planning. Never create another Frank GraphQL client in Basic, and never treat a public spot price as the actual Belgian MODEL/variable customer invoice rate. Do not silently double count invoice amounts, capacity or tax.

## Observed evidence: installed HACS TEST v2026.11.1.8, BE, 2026-11-01 14:44 CET

The authenticated selected Belgian site has both electricity and gas contracted; `monthly_finance_enabled=true`.

| API/evidence | Verified | Still missing or disproved |
| --- | --- | --- |
| `MonthInsights` 2026-11 | GraphQL error (unclassified), `monthInsights:null` | Any current-month financial source amount |
| `MonthInsights` 2026-10 | Actual electricity cost/kWh, signed feed-in cost/kWh; expected electricity/fixed/feed-in; source expected gas present | `gasExcluded=true` and `gasDifference:null` mean actual gas is not available, so all-energy actual/expected total must not be labeled complete |
| `PeriodUsageAndCosts` 2026-10-31 | Electricity and feed-in usage totals present | No gas section; no cost totals or detailed intervals |
| `MonthSummary` | Object present; last meter reading October 30 | A complete November month, monthly gas, or period-matched reconciliation |
| `Invoices` | Six invoice records present | Directly usable full calendar-month cost; advances/settlement periods unverified |
| Customer source price slots | Nov 1: 24 electricity + 24 gas hours; Nov 2: 24 electricity + only 6 gas hours | Complete future gas day or verified hourly billing under BE MODEL |
| HA entity status | 193 registered; Costs 20 available / 25 unavailable / 1 unknown / 6 disabled | Functional completeness of the cost view |

**Privacy:** No raw account diagnostics, prices, bill totals, EAN, meter/site IDs, tokens, names, addresses or invoice identifiers may enter GitHub test fixtures, PR text or logs. This document includes status evidence only.

## Source to household ledger mapping

| Component | Allowed Frank source | Required validation / other owner |
| --- | --- | --- |
| Electricity actual €/kWh/kWh | `MonthInsights.electricityDifference.actualCosts/actualUsage` for named month | Verify same meter cutoff, period, unit and portal amount |
| Gas actual €/unit, usage | `MonthInsights.gasDifference.actualCosts/actualUsage` only if `gasExcluded=false` and raw fields valid | Investigate gas meter history / publication. If source never returns, Basic may separately estimate from physical gas usage + independently verified variable-contract formula, never call it Frank actual |
| Injection credit | `MonthInsights.feedInDifference.actualCosts` | Preserve provider sign and compare invoice |
| Fixed supplier charges | `MonthInsights.expectedCostsFixed` is a forecast | Find actual settlement line before calling fixed fees actual |
| Actual provider total | `MonthInsights.actualCostsUntilLastMeterReading` | Must have contracted components and same cutoff as `MonthSummary`; not a complete household all-in invoice |
| Forecast supplier total | `MonthInsights.expectedCosts` | Forecast may precede first meter reading in month; distinguish it from actual |
| Grid, network, capacity, levies, VAT | No independently verified separate Frank fields in pinned client | HA Energy Basic owns verified DSO/year/local tariff model, P1 grid imports/peak, gas source, inclusion flags |
| Invoice and advances | `Invoices` | Reconcile document charge lines by consumption period, corrections, settlement and advances; never add gross payment atop consumption charges |
| Historical day usage | `PeriodUsageAndCosts`, existing integration requests yesterday | Confirm source history and gas publish delay before any Recorder backfill or new API polling |

## Engineering order

1. Read this file and the source contracts. Pin `python-frank-energie==2026.9.20` unless separately versioned/tested.
2. Validate exact selected site contract for both segments and fetch existing customer data. Do not conflate public `PT15M` query resolution with billing.
3. Compare GraphQL `MonthInsights` current and previous months; verify *raw presence* of all required finance fields because pinned client converts missing/null numeric values to 0. Keep all data strictly period-scoped.
4. Investigate actual gas publication: `gasExcluded`, `gasDifference`, meter-reading dates, gas `PeriodUsageAndCosts`, gas units and publication lag. Expected gas cost alone does not prove actual gas.
5. Reconcile the exact same meter cutoff across `MonthInsights` and `MonthSummary`. Inspect invoice settlement and supplier fee coverage separately. A provider success or object present is not a billing result.
6. Publish quality/status in HA and diagnostics for each current/previous period; an unavailable required component must prevent a purportedly complete combined total. Do not hide partial results: display individually labeled electricity cost or a derived Basic estimate.
7. Extend Basic ledger with physical meter data and independently verified tariffs; do not invent an invoice rate from market-price graphs. Present provider and derived values separately.
8. Validate a **closed calendar month** against real bill lines, plus first-of-month, delayed gas, 23/25-hour DST, period corrections, multi-site, reload, Recorder, rollback and source privacy.

## Lessons learned — never regress

1. **A successful GraphQL request is not complete data.** GraphQL can report `monthInsights:null` with errors; yesterday's successful usage request can omit gas entirely.
2. **Missing is not zero.** Pinned client may parse missing/null to 0. Retain raw field presence, sign and original units; do not publish fake zero gas costs.
3. **Actual, forecast and invoice are different scopes.** Realized amounts need a meter cutoff. Month forecasts can exist without the first current-month reading. Invoices often span other periods and advances.
4. **BE MODEL is variable, not automatically hourly dynamic.** Never value electricity/gas consumption with public spot-market prices without the actual contract formula.
5. **A complete provider result does not mean a complete home bill.** Capacity, distribution, transport, taxes and supplier fixed components may require independent Basic-side accounting.
6. **Gas lags and can be explicitly excluded.** Expected gas fields may exist while `gasDifference` is null; expected ≠ actual.
7. **Historical provider evidence should survive short outages.** Preserve previous-month last known successful data for the same selected site/period, keep retrieved_at honest, retry failed refreshes, and never leak it across sites.
8. **Time coverage beats slot counts.** Tomorrow gas may have six rather than 24 hours; averages/min/max must require actual whole local-day interval coverage, including DST.
9. **Protect HA history.** Do not reuse existing unique IDs for different semantic periods or create unvalidated Recorder statistics/backfill.
10. **Single governed release train.** Stay on draft PR #18, exact-head CI, qualified immutable HACS TEST, live BE source and entity/Recorder proof before stable promotion.

## Open blockers and acceptance evidence

- [ ] Provider returns actual monthly gas cost/usage, or Basic has a **separately labeled and verified** local gas cost estimate.
- [ ] November `MonthInsights` null/error explained or documented as a provider-side publication limitation, not silently hidden.
- [ ] Electricity, gas, injection, supplier fixed, grid/capacity, levies and VAT all accounted for in a single *qualified* household view, with missing-state logic.
- [ ] Closed month verified against provider portal and the appropriate invoice settlement lines, no duplicate advances.
- [ ] Source quality/status visible in HA and diagnostics; actual vs expected vs derived unambiguous.
- [ ] Real BE HA reload, entity identity, Recorder, HACS install/rollback, privacy and selected-site isolation confirmed.
- [ ] Exact-head Python 3.14/3.14.2 tests, Ruff, Flake8, HACS/Hassfest, Quality Scale, Link Check green. Do not treat CI alone as live acceptance.

## Start here next time

Open this runbook, then `FRANK_FINANCE_MONTHLY_COSTS_TASK.md`, `BE_SOURCE_CONTRACTS.md`, `HA_ENERGY_BASIC_SOURCE_CONTRACT.md` and `RELEASE_TRAIN.md`. Tests: `test_finance.py`, `test_finance_coordinator.py`, `test_month_boundary_costs.py`, `test_diagnostics.py`, `test_price_coverage.py` and the specific updated finance/gas coverage regression tests. The unsolved product gap is **provider gas-financial data plus household-ledger reconciliation**, not a lack of additional price sensors.
