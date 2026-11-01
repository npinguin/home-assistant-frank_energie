# ADR — Supplier integration boundaries and energy-cost ownership

**Status:** Accepted as an architecture boundary (2026-11-01)
**Applies to:** Frank Energie HACS integration / HA Energy Basic / RHI Energy
**Scope:** Engineering responsibility, source authority, integration changes.
**Implementation:** This ADR does not change runtime entities, published releases
or financial calculation behavior.

## Decision

**Frank Energie is a supplier adapter, not a generic Belgian energy-cost,
metering, scheduling or home automation framework.** It owns provider
communication and faithful Home Assistant representation of provider facts.
An optional provider-supported smart command is still provider functionality;
local control of home devices and optimization across devices is not.

**HA Energy Basic** owns the real HA Wessels installation: local measurement,
Fluvius/P1 meter evidence, load and energy flows, Belgian capacity-peak
calculation, source reconciliation and one understandable site-level costs view.
It may use Frank Energie as one of several input sources. It must not modify
or reimplement the provider's private GraphQL client.

**RHI Energy** owns reusable, supplier-neutral energy capabilities: normalized
metering, planning, optimization, policies, cost allocation, financial model,
history and UX for different homes. Proven, installation-specific Basic logic
can be extracted into RHI Energy without building a second generic
framework inside Basic.

**Belgian Electricity Prices** is a separately maintained reference and an
optional independently installed comparator; it is *not* an API dependency,
embedded tariff engine, source of private Frank customer prices or system of
record. Its tariff-card/DSO/capacity handling can inform Basic/RHI designs,
subject to independent verification of the exact date, region and contract.

## Ownership by capability

| Capability | Owner | Contract / constraint |
|---|---|---|
| Frank login, tokens, delivery-site selection, GraphQL, polling, redacted diagnostics | Frank Energie integration / pinned python client | Maintain upstream-shaped provider behavior, no new generic abstraction |
| Supplier-published spot/customer price slots, contract identifiers, actual/expected monthly records, provider invoices and supplier smart capabilities | Frank Energie | Preserve source provenance, site, timestamp, unit, null vs zero and effective period; provider data is not automatically all-in |
| Simple, source-local presentation (current/tomorrow prices, min/max/avg and compatibility events) | Frank Energie | Read-only provider facts or directly derived prices, not optimization or a certified invoice rate |
| Market-hour rank / cheapest X hour binary entities shipped in TEST v2026.11.1.6 | **Frank: compatibility only**; long-term reusable logic: RHI Energy | Read-only market component, clearly *not* customer MODEL billing; **freeze further extension in Frank**. Do not delete unique IDs or break Recorder; migrate consumers before eventual deprecation |
| P1 import/injection, real quarter-hour peaks, Fluvius exports, historical month peaks, meter completeness | HA Energy Basic for Wessels; generic metering in RHI | Meter evidence is neither supplied nor guaranteed by Frank |
| Regulated Flemish capacity tariff and local network/levy/tax overlays | HA Energy Basic / RHI Energy cost model | Separate monthly charge, DSO/year-specific tariffs, min/rolling-window and estimation status; **never inject into Frank price sensors** |
| Household monthly bill, all-in financial total, invoice cross-check, forecasts, source arbitration | HA Energy Basic initially; RHI Energy generically | Explicit source-of-truth precedence, no double counting of invoice-inclusive fees; estimated, measured, reported, invoiced and reconciled are different statuses |
| Device-independent cheapest-window selection, schedules, battery/EV/heat-pump coordination, load curtailment and objectives | RHI Energy | Consumes standardized capabilities; does not assume a spot-market rank equals a customer savings signal |
| Home-specific wiring, P1 mapping, local dashboards, quick practical interventions | HA Energy Basic | Site-specific, simple implementation; avoid a second reusable framework |
| Supplier-owned smart charging/trading commands exposed by the Frank API | Frank Energie adapter | Only commands that the provider's own API supports, under that provider's account; no independent controller |

## Central costs without two billing engines

1. Preserve immutable provider evidence from Frank Energie separately from
   local measurements and public/regulatory tariff inputs.
2. In Basic/RHI, make a period-scoped **cost ledger** with separate components:
   energy import, feed-in credit, distribution, transport, capacity charge,
   levies/VAT, subscription/fixed fees, and adjustments.
3. Every component must carry `source`, `period`, `unit`, `coverage`,
   `calculation_version` where derived, and a status such as
   `reported`, `measured`, `estimated`, `invoiced`, `reconciled` or
   `unavailable`. Incomplete means unknown, **never a synthetic zero**.
4. An official supplier invoice is a separate reconciliation evidence row;
   never add a complete invoice total to already calculated line items.
   If a supplier-reported amount already includes capacity or another fee,
   the corresponding calculated fee is a comparison, **not** another charge.
5. For capacity-peak impact, compare the existing monthly P1 quarter-hour
   peak against the predicted incremental peak. A momentary power maximum
   is not an official quarter-hour peak. Missing months must be marked
   incomplete or sourced explicitly from Fluvius.

## Pull-request review gate: no Frankensteins

Reject a change to the Frank integration when any of these is true:

- It reads a local Home Assistant P1 sensor or other unrelated hardware.
- It scrapes Fluvius, parses third-party tariff PDFs or owns regulator tariffs.
- It computes household totals, capacity costs, arbitrary taxes/fees or
  multi-provider estimates from assumptions.
- It introduces a generalized load scheduler, energy policy, household
  optimizer, source arbitration engine or multi-vendor orchestration.
- It presents a public spot-market signal as the authenticated Belgian
  MODEL customer charge, or inserts guessed VAT/margins into source facts.
- It duplicates a feature already owned by Basic or RHI Energy, instead
  of exposing clean provider data.
- It changes existing stable entity identifiers, Recorder semantics or
  the published HACS ZIP without an explicit compatibility plan.

For acceptable Frank changes, demand an actual provider or HA-adapter
need, read-only or provider-owned semantics, source/period evidence, no
unnecessary API polling, privacy, tests and unchanged entity identity.

## Migration rule and release boundary

v2026.11.1.6 is already an **immutable published TEST** prerelease.
Do not retroactively remove its market-hour entities or rewrite its
checksum/tag. Their presence is a bounded compatibility exception, **not
permission** to add battery-load scheduling or a broad new price engine.
A later separately versioned release may deprecate/redirect those derived
signals only after Basic/RHI equivalents are tested and consumers migrate.
Keep the current PR in Draft until live Belgian and Recorder acceptance.
