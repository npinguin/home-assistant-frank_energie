# Engineering task — Frank Energie financial source contract (BE, multi-site)

**Status:** implementation requested; documentation-only draft PR. No production logic changed by this PR.

**Base:** `fix/authenticated-public-prices-isolation` (`2026.10.21.2` test candidate). Keep existing open auth/public-price, reconfigure and enum PRs isolated; do not quietly cherry-pick unrelated changes.

## 1. Goal and decision

Extend **our existing HiDiHo01-derived `frank_energie` integration**, not another Home Assistant integration, with reliable, independently measured *electricity / gas / feed-in / fixed-cost* amounts for calendar months and historical periods. Keep the original Frank customer totals, invoices and price feeds.

Consumer contract: Home Assistant and downstream packages (including HA Energy Basic) can render **Previous | Current | Forecast** without mislabelling invoice periods, calculating fictitious components, or mixing supplier costs and local capacity-tariff estimates.

Priority: **correctness and source lineage > filling every card**. If upstream data does not exist, expose an explicit unavailable/quality reason. No inventing a gas amount, copying a daily amount into a monthly metric, or treating an upcoming invoice as a next-calendar-month forecast.

## 2. Confirmed starting point / defect

- In `custom_components/frank_energie/sensor.py`, `costs_electricity_this_month` exists but is **disabled by default** and currently uses the same `data[DATA_USAGE].electricity.costs_total` readout as `costs_electricity_yesterday`. Determine the exact period semantics of `DATA_USAGE`; do not merely enable/rename it as monthly without proof.
- Gas has a `costs_gas_yesterday` readout but no corresponding confirmed monthly gas cost sensor in this integration.
- Existing Frank account data exposes current actual/expected month *total*, invoices, annual costs, yesterday electricity usage/cost, while yesterday gas can be absent. A missing monthly electricity/gas split in downstream UX is not permission to compute `total - gas` from unrelated integration data.
- The independent Belgian Electricity/Gas Prices devices may be configured for a **different contract type** (Dynamisch vs user's Variabel), with different observed peak values; these are NOT invoice-authoritative data.
- A HomeWizard P1 meter is the independent physical reference for grid consumption and measured monthly 15-minute peak. Frank account cost data is the financial reference. Do not double-count any separate capacity tariff against a Frank total whose components are unverified.
- The existing public price queries and authenticated/multi-site work are intentionally separated in current fork PRs.

**Upstream reference (design inspiration only, not a migration or code-copy instruction):**
`archofthings/home-assistant-frank-energie` documents separate monthly electricity/gas/fixed cost readings and a delayed hourly statistics import. Confirm implementation and licensing before reusing code.

## 2a. Concrete implementation references — where to look first

The source of the design is the actively maintained [archofthings Frank Energie integration](https://github.com/archofthings/home-assistant-frank-energie), **not** a request to install a second integration or copy code verbatim. Read the license/project-history status first, and implement against the API contract of this fork.

1. **Data collection, timing and late availability:** [`custom_components/frank_energie/usage.py`](https://github.com/archofthings/home-assistant-frank-energie/blob/main/custom_components/frank_energie/usage.py) — `UsageCoordinator`, `UsageData.daily`, `UsageData.monthly`; inspect which Frank endpoints return `MonthInsights`, and why gas can lag electricity. Reuse the **data semantics**, not necessarily this coordinator structure.
2. **Monthly sensor model:** [`custom_components/frank_energie/sensor.py` — `MONTHLY_USAGE_SENSOR_TYPES`](https://github.com/archofthings/home-assistant-frank-energie/blob/main/custom_components/frank_energie/sensor.py#L743-L835). In particular, `elec_usage_month` / `elec_costs_month` (`electricityDifference.actualUsage/actualCosts`), `gas_usage_month` / `gas_costs_month` (`gasDifference.actualUsage/actualCosts`), `feed_in_month`, `fixed_costs_month` and `fixed_costs_month_until_now`. Check `_monthly_value`, `_monthly_attrs`, `last_meter_reading` and `_monthly_last_reset`. These are **examples to inspect**, not validated for every BE account.
3. **Optional sensor groups:** [`custom_components/frank_energie/const.py`](https://github.com/archofthings/home-assistant-frank-energie/blob/main/custom_components/frank_energie/const.py#L65-L91) lists `SENSOR_GROUP_MONTHLY_USAGE`, `SENSOR_GROUP_DAILY_USAGE`, `SENSOR_GROUP_ENERGY_STATISTICS`; [`config_flow.py`](https://github.com/archofthings/home-assistant-frank-energie/blob/main/custom_components/frank_energie/config_flow.py) handles options and login-only groups. Follow stable HA entity registration/unique ID policy in our fork.
4. **Recorder/HA Energy integration:** [`custom_components/frank_energie/energy_statistics.py`](https://github.com/archofthings/home-assistant-frank-energie/blob/main/custom_components/frank_energie/energy_statistics.py) demonstrates `async_add_external_statistics`, gap/backfill and statistics IDs. Ensure no double counting with P1 and no re-interpretation of existing Recorder statistic IDs.
5. **Functional documentation and user reporting:** [README — Costs / Monthly usage / Energy dashboard statistics](https://github.com/archofthings/home-assistant-frank-energie#features) and its [wiki](https://github.com/archofthings/home-assistant-frank-energie/wiki). Their troubleshooting explains that Frank's expected, actual, daily, monthly and invoice endpoints may publish different days; gas is sometimes published later.
6. **Our source to correct first:** [`custom_components/frank_energie/sensor.py` in our fork](https://github.com/npinguin/home-assistant-frank_energie/blob/fix/authenticated-public-prices-isolation/custom_components/frank_energie/sensor.py) — compare `costs_electricity_yesterday`, disabled `costs_electricity_this_month` and `costs_gas_yesterday`; all current `costs_total` fields need period verification before labeling.

**Required comparison artefact from engineer:** one table comparing archofthings' `MonthInsights` access, this fork's `DATA_USAGE` / `DATA_MONTH_SUMMARY` models and the installed `python-frank-energie` library: field paths, actual sample semantics (redacted), periods, timezone, units, `None` behavior, HA sensor and Recorder reset strategy. Any missing upstream Python-client API should become a separate tested issue/change, not a guessed field mapping.

**Licensing/attribution:** check the upstream project's license situation and related dependency licenses before copying any implementation; prefer a clean independent implementation and acknowledge conceptual inspiration in the PR.

## 3. Engineer: execute in this order

### A. Verify actual API semantics before implementing

1. Inspect `python-frank-energie==2026.9.20`, `monthSummary`, `Usage`, invoices and any account usage history endpoint. Determine whether `costs_total` is a single day, month-to-date, year-to-date or another interval. Check timestamp, timezone, last meter-read date, currency, gas unit, taxes, feed-in sign and fixed costs.
2. Build **sanitized test fixtures** covering Belgium electricity+gas account, including a valid month with both streams, gas delayed, first-of-month without a new summary, an incomplete day, no account data and multiple delivery sites. Never commit raw diagnostic ZIP, credentials, names, street addresses, EAN/site IDs, tokens or private invoice details.
3. Produce a compact API-to-HA entity mapping: *API endpoint.field → period → unit → refresh lag → quality → destination entity*. Identify which missing data requires an **independent change to the Python client** and which can be done entirely in this repo.
4. If the authenticated API does not expose true monthly data, prefer a clearly qualified Recorder/statistics-based estimate as a **separately named derived value**, not an `actual` entity.

### B. Implement optional financial entity family

Use stable identifiers and correct HA units/classes; keep existing entity/unique IDs intact. Names below describe **required semantics**; reuse existing stable IDs only when historically identical:

| Capability | Expected source / semantics | Notes |
| --- | --- | --- |
| Electricity month-to-date usage / cost | Frank electricity monthly `actualUsage` / `actualCosts` | kWh, EUR; explicit last-meter-reading timestamp |
| Gas month-to-date usage / cost | Frank gas monthly `actualUsage` / `actualCosts` | m³ and EUR; only when data exists; NEVER zero-fill delayed gas |
| Feed-in month-to-date kWh / revenue | Frank monthly feed-in `actualUsage` / `actualCosts` | define income sign unambiguously |
| Fixed monthly costs | Frank monthly fixed cost component (if independently exposed) | don't subtract from totals as an inferred split |
| Previous completed calendar month | Frank confirmed monthly data or separately qualified historical statistics | not an invoice proxy |
| Current month expected final / run-rate | Frank *expected* metric or qualified estimate, with source/period | distinguish expected until-now vs expected month end |
| Year-to-date actual / year expected | existing official Frank year sensors | do not mistake expected annual cost for invoiced YTD |
| Historical usage/cost statistics | opt-in, source-backed, with period and revisions | must coexist with P1 and avoid duplicate Energy flows |
| Last meter-reading timestamp / status | source freshness and completeness | user-friendly, stable provenance attributes |

Keep **invoice_previous/current/upcoming** as separate *billing period* metrics. Include period start/end and invoice status where API supports it; never call them Previous/Next *calendar month* without a matching interval.

For each sensor:
- Valid numeric or `None` (unavailable), never generic `float(0)` on missing data;
- `device_class`, `state_class`, unit and reset/recording semantics matched to HA requirements;
- `period_start`, `period_end`, `last_meter_reading`, `source`, `completeness` / quality attrs as supported;
- per-entry/per-site stable unique IDs; reconfigure same account/site cannot silently inherit another site's counters;
- documented delayed meter publication (gas may lag electricity).

Default **optional sensor group**: `Monthly usage and costs`, plus separate opt-in `Energy dashboard statistics`. Avoid creating dozens of unwanted entities by default, but make missing capabilities discoverable/configurable from the HA options flow.

### C. Correct the existing alias/semantics defect

- If `costs_electricity_this_month` is an incorrect alias to daily `costs_total`, fix its period/source or deprecate with compatibility guidance; ensure existing saved entity registry IDs and Recorder histories are not silently reinterpreted.
- Investigate whether gas yesterday is missing due to Frank publication lag vs a coordinator/model bug. Never implement `unavailable → 0 EUR`.
- A single unavailable authenticated API endpoint may not make unrelated public price sensors unavailable. Preserve authenticated/public request isolation.
- Any changes to `python-frank-energie` should be versioned, tested and released independently; do not point integration to unversioned forks.

### D. Capacity tariff: expose but do not fabricate

Belgian capacity-tariff requirements depend on the **physical monthly peak, rolling billing peak, DSO-specific tariff and tax treatment**. If Frank's API provides a real billed capacity component, expose it with its exact period and provenance. Otherwise leave capacity `unavailable` at this integration layer and let HA Energy Basic combine P1/Fluvius inputs with a verified local rate.

Never sum an *estimated* capacity charge into Frank `actual_monthly_cost` unless invoice inclusion/overlap is explicitly established. No additional electricity/gas tariff provider is a requirement for this PR.

### E. Documentation and consumer contract

- Document grouped options, sensor names, financial units, period/timezone rules, invoice vs calendar-month distinction, when values arrive, and first-of-month / DST / delayed gas behavior.
- Provide mapping examples for a consumer's three cards: **Previous | Current | Forecast** with rows Electricity, Gas, Capacity and Total. Unknown stays unknown.
- Spell out which fields are **authoritative Frank invoice/actual**, **Frank expected**, **HA-derived estimate**, **physical metering**, or **external tariff reference**.
- Update English, Dutch, Belgian Dutch and French translations where relevant. No raw technical mapping or private account information in user-facing dashboards.

## 4. Mandatory regression matrix

- API data: both electricity and gas populated; electricity only; no gas contract; gas late by one/two days; partial month; last meter reading stale.
- Periods: first day of new month, end of month, year boundary, Europe/Brussels DST change (23/25h), late corrections and API restart.
- Data: zero usage (valid zero) vs missing/unavailable, negative market prices, positive feed-in revenue, fixed fees, tax amounts, different currencies/units when upstream returns them.
- Semantics: `yesterday` and `this_month` **must not be aliases**; test independent values in fixtures; compare split components against provider totals *only when periods and inclusion match*. No implicit sum otherwise.
- Integration: Home Assistant entity registration and `state_class` validation; Recorder/long-term statistics continuity; entity IDs/unique IDs remain stable for existing sensors.
- Accounts/sites: public-only, authenticated, multiple users, multiple delivery sites, reconfigure, reauth/token refresh, no cross-site leakage.
- Reliability/privacy: partial API outage preserves prices; no credentials / IDs in logs or diagnostics; fixtures are scrubbed; no secret dump in PR.
- Existing fork fixes: keep public-price/auth GraphQL isolation, enum fixes and reconfigure lifecycle independent; targeted regressions where affected.

## 5. Definition of done / acceptance gates

- [ ] Engineer supplies **API field-level evidence** for every new `actual` sensor and its time interval.
- [ ] Monthly electricity and gas split is independently correct and traceable; old totals/invoices unchanged.
- [ ] Source completeness/freshness is visible; delayed gas does not produce invented values.
- [ ] No historical statistics or entity ID drift; any necessary migration has tested rollback.
- [ ] Multi-user/multi-site and public price behavior unchanged.
- [ ] Python tests + real HA registration/Recorder tests; Ruff; Validate matrix; HACS; Hassfest; Quality Scale; Link Check all PASS on **the same head commit**.
- [ ] Live BE acceptance with sanitized comparison to Frank account for **one complete month** and a day when gas is delayed; optionally validate a second account/site.
- [ ] Release notes, support diagnostics and downstream HA Energy Basic mapping guidance complete.
- [ ] Draft PR remains unmerged and no prerelease is published until implementation, CI and live financial acceptance are complete.

## 6. Requested deliverables (engineer)

1. Short source/period mapping with evidence and any API/client limitation.
2. Implementation PR commits (or a dedicated linked implementation PR if this planning PR stays docs-only).
3. Tests + sanitized fixtures, with the observed validation results.
4. Migration/compatibility note for existing HiDiHo01-derived sensor histories.
5. Screenshot or compact entity-state proof for an authenticated Belgian electricity+gas installation, redacted.

**Non-goals:** no new Frank integration, no second writer/optimizer for SolarEdge, no redesign of unrelated Mobility/Energy packages, no manually fabricated historical costs, no automatic migration to `archofthings`, no secrets in GitHub.
