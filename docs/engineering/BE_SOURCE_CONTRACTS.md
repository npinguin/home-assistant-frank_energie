# Belgian provider contract and engineering invariants

This file is the short, version-neutral contract for Belgian support. The
implementation remains a Home Assistant **supplier integration**, not a second
energy optimizer, billing engine, or hardware controller. Historical release
and runtime evidence belongs in `docs/engineering/RELEASE_TRAIN.md`.

## Source authority

| Source | Permitted meaning | Must not be inferred |
|---|---|---|
| Anonymous `marketPrices` / `countryPrices` | Public market signal for a country, time interval and requested resolution | Customer tariff, supplier invoice rate, or actual paid amount |
| Authenticated `customerMarketPrices` | Provider-returned customer slots for the **selected** delivery site, subject to actual source coverage and contract | Correct meter type, every hour of the day, all-in settled energy cost |
| `UserSites` and contract metadata | Selected-site supply segments and provider's contract identifiers | That a `MODEL` code has Dutch modelcontract billing rules, or that `SMR1/SMR3` encodes dynamic pricing |
| `MonthSummary` | Provider's reported monthly summary and its meter-reading cutoff | Invoice reconciliation, completed current calendar month, or current gas data |
| `MonthInsights` | Period-scoped actual and expected components, only when source fields and units are verified | Missing/null amounts as zero, expected as actual, or final network/capacity charges |
| `PeriodUsageAndCosts` | Provider-published usage/cost intervals, with their actual reporting date | A full month or complete gas series from a successful request alone |
| `Invoices` | Payment/settlement document metadata | Consumption-period all-in costs from a gross invoice amount |
| Smart device operations | Provider-owned optional smart-service data and commands | Direct EV charger/battery control outside the relevant owner |

## Non-negotiable runtime rules

1. **Site isolation:** Authenticated data is read for the configured delivery
   site only. The first site in an API response is not the selected site.
2. **Source isolation:** Anonymous requests never inherit account credentials.
   Customer-to-public fallback is explicitly diagnostic evidence, **not**
   proof that a displayed market price is a customer billing rate.
3. **Intervals:** Compare UTC source interval *coverage*, not slot count.
   Clip intervals at the local calendar-day boundary, deduplicate overlaps
   and cover the true 23/25-hour DST day. Do not infer 15-minute customer
   billing from a 15-minute public query preference.
4. **Completeness:** A successful HTTP/GraphQL call means a request completed;
   it does not mean every subscribed electricity/gas interval was published.
   Incomplete customer days are retryable; a shorter response does not erase
   better still-dated cached coverage.
5. **Provenance:** Distinguish fresh customer, fresh public, mixed and cached
   selection; no cache-only refresh may appear as a fresh supplier response.
   The business-time slot clock may update HA states without a provider call.
6. **Accounting:** `unavailable != unknown != 0`. Preserve actual, projected,
   feed-in sign, gas unit, reported gas exclusion, cutoff and month.
   Zero requires raw source evidence when the pinned parser erases presence.
7. **Privacy:** No site references, meter/EAN IDs, account numbers, tokens,
   addresses, invoice amounts or arbitrary supplier strings in diagnostics or
   public regression fixtures. Bounded source timing and quality only.
8. **Compatibility:** Existing Home Assistant entity and device unique IDs
   and Recorder history must not be reinterpreted or reassigned.
9. **Dependencies:** The vendor Python client stays version pinned.
   Contract changes require a pinned client version, explicit tests and
   reproducible packaging; no silent local API forks.
10. **Release qualification:** One PR, exact-head CI, HACS/Hassfest, immutable
    candidate ZIP and real Belgian HA/Recorder/reload/rollback acceptance.
    Static tests alone cannot authorize a stable release.

## Current important limitations

- Aggregate selection provenance is available in diagnostics, but generic
  price sensors may still display a public market fallback. Until source
  provenance is made unambiguous at the consumer/entity boundary, treat these
  as **market signals**, not certified `MODEL` invoice tariffs.
- Monthly finance is opt-in and not accepted for general use. Real BE
  `MonthInsights` raw-field presence, delayed gas, signed feed-in and
  consumption-period settlement lines still need account-side validation.
- No historical Home Assistant statistics backfill or energy dashboard import
  is authorized until units, intervals, completeness and revisions are proven.
- Smart charging/battery actuation is outside this BE tariff/finance closure.

## Test ownership

| Contract | Primary automated coverage | Required live gate |
|---|---|---|
| Source/public isolation and MODEL distinction | `test_public_price_auth_isolation.py`, `test_price_provenance.py` | Selected BE contract and public/customer evidence |
| Local timestamp coverage and cache | `test_price_coverage.py`, `test_price_cache.py`, `test_midnight_recovery.py` | Prices/gas after midnight, source gaps, DST rollover |
| Month cutoffs and zero/null truth | `test_finance.py`, `test_finance_coordinator.py`, `test_month_boundary_costs.py` | Current/previous month, gas and settlement lines |
| Provider request truth/diagnostic privacy | `test_diagnostic_trace.py`, `test_diagnostics.py` | HA diagnostics and sensor update timestamps |
| HA lifecycle and release integrity | `test_init.py`, `test_release_train_governance.py` | HACS install, reload, Recorder and rollback |

Update the source contract and its tests together when changing semantics.
Do not create a new framework or generic abstraction for a single supplier.
