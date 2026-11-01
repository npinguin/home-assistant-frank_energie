# Home Assistant Energy Basic — Frank Energie source handoff

**Scope:** Consume the already installed Frank Energie HA integration as a supplier data source. Frank does not own the home cost ledger, the capacity tariff, P1 measurements, local control, or site planning. This is an integration contract and acceptance checklist, not a new runtime API or a second GraphQL client.

## Native HA entity bindings

Resolve actual `entity_id` through the **current Home Assistant entity registry** (users may rename them). The stable Frank sensor description keys below are code identifiers, **not** literal HA entity IDs. Keep the existing config entry and entity unique IDs on upgrade.

| Frank description key | Meaning from the existing HA entity | HA Energy Basic usage |
|---|---|---|
| `elec_market` | Selected electricity market-price component, EUR/kWh | Market signal only; never a Belgian MODEL customer charge |
| `elec_markup` | Provider selected electricity total price slot, EUR/kWh | Supplier snapshot/comparison; not independently verified all-in invoice rate |
| `gas_market` | Selected gas market component in provider unit | Display/comparison only; verify unit before consumption-cost multiplication |
| `gas_markup` | Provider selected gas total price slot | Supplier snapshot; do not silently convert gas kWh to m³ |
| `finance_current_*`, `finance_previous_*` | Period-specific provider `MonthInsights`, enabled with **Monthly Finance** option | Reference/cross-check only, never netted as the home's billed total |
| Existing invoice, usage and month-summary entities | Provider reported records, not independent physical measurements | Reconciliation evidence with source cutoff and period attached |

The existing current electricity/gas price sensors have these additional attributes in the next qualified HACS TEST:

- `selected_price_origin`: `customer`, `public`, `cached_unverified`, `unavailable`, the same with `_partial` where full local-day interval evidence is missing, or `cached_or_unverified` before source observation.
- `selected_price_segment`: `electricity` or `gas`.
- `customer_billing_rate_verified: false`: never mistake a provider price slot or public fallback for a reconciled Belgian MODEL invoice tariff.
- `cost_scope: provider_price_not_reconciled_invoice`.

**Consumer behavior:** Use provider prices only as **indicative** until provider-specific contract provenance is independently accepted. A market component may be displayed as a market signal; do not optimize financial cost using a public fallback as if it were a customer invoice rate. Treat `unknown`, `unavailable`, partial/old periods and missing source fields as missing, never zero.

## Ownership and source precedence

1. Frank supplies authenticated customer data only for the selected delivery site, separate from anonymous public market data; its API and client are called only by the Frank HA integration.
2. Basic owns home-specific energy source bindings in `packages/energy/energy_00_sources.yaml`, P1 grid flows, quarter-hour peaks, local gas/electricity usage normalization and the household cost ledger. Do not create Frank requests inside Jinja, YAML, Python scripts or a second HA package.
3. Basic owns network/capacity, levies and VAT estimates with explicit Belgian locality, operator, tariff year, calculation provenance and completeness. This must **not** be added to Frank provider sensors.
4. Provider month actuals, forecasts, invoice payment totals and Basic calculated consumption-month costs are **separate** evidence. Do not sum whole invoices into already-calculated charges. An invoice can settle one month and collect an advance for another.
5. Home-specific execution stays with native controller domains; Frank provider-owned smart command surfaces must not be reused to control independently connected chargers/batteries.

## Checklist before switching Basic from a provisional price source

| Gate | Proof |
|---|---|
| HACS integration | Qualified TEST installed on existing config entry, retains entity/device registry identities and Recorder |
| Price source | A live refresh has shown customer/public/cached per segment on same selected BE site |
| Coverage | Full source timestamp coverage of electricity/gas over local 23/24/25-hour day, separately from tomorrow |
| Contract | Variable MODEL product metadata != market PT15M query preference; no spot-to-bill claim |
| Finance | `MonthInsights` available for period, raw null/zero truth, gas exclusion and latest meter cutoff explicit |
| Recorder | Current states/attributes and long-term histories observed after reload, restart and rollback |
| Security | No credentials, site IDs, EANs, bills or private price amounts in diagnostics/CI fixtures |

**Current evidence, 2026-11-01:** Installed v2026.11.1.6 HA diagnostics show 24 hourly electricity and 24 hourly gas slots covering the current local day; source calls after restored-cache startup have **not** been observed in that export. November `MonthInsights` fails at GraphQL; October excludes gas; yesterday gas usage and costs are not reported. Monthly finance is **not accepted** for automatic all-in cost calculation. Price source attribution in this new work requires a new HACS TEST installation and runtime proof.

**Rollout:** First upgrade the standalone Frank HACS integration; validate live price source attributes and actual HA states. Only then map its existing `entity_id`s as read-only inputs in Basic. Keep Basic's P1/capacity/financial accounting independent, with a strict quality guard on the provider signals. No Basic package or dashboard migration is implied by this document.
