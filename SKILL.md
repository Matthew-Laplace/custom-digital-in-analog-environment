---
name: custom-digital-in-analog-environment
description: Plan, execute, and gate custom-digital placement and signal routing inside an analog design environment - Layout XL source/layout/physConfig establishment, PR-boundary placement, explicit M1 supply tracks, bounded route-feedback closure, strict via-array acceptance, and LUP-constrained tap insertion - while keeping OA writes, persistence, DRC, and LVS as separate evidence gates. Use when generating or correcting a standard-cell or custom-digital block in a mostly analog design by script; do not use it as a PDK rule deck or as a general OA-write authorization.
metadata:
  skill_type: "cadence-automation"
  skill_type_zh: "Cadence 自动化"
  skill_tags:
    - "skill-type/cadence-automation"
---

# Custom Digital In Analog Environment

This skill carries one bounded layout transaction inside an analog design
environment - custom digital placed and routed alongside analog blocks - from
artifact establishment through placement, supply tracks, routing, and route
acceptance.
It is the single owner of stage order, candidate selection, and the decision to
accept or reject a routed candidate.

It does not connect to Virtuoso by itself, and it does not define process
geometry. Every geometry-driving value must come from the currently bound PDK
and the user's confirmed inputs for the design in front of you.

## Reference Map

| Topic | Read |
| --- | --- |
| Ownership, leases, contract fields, evidence states | [bounded-operation-contract.md](references/bounded-operation-contract.md) |
| OA edit mechanics, Layout XL binding, SKILL generation patterns, geometry heuristics | [geometry-execution.md](references/geometry-execution.md) |
| Wire Assistant settings, Route APIs, via and push semantics | [wire-assistant-routing.md](references/wire-assistant-routing.md) |
| Pure offline placement/occupancy helpers | [local-layout-planning.md](references/local-layout-planning.md) |
| SKILL coding hygiene for generated layout scripts | [skil-coding-patterns.md](references/skil-coding-patterns.md) |

## Scope And Separation

- The root task is the only writer of object geometry. Any helper or subordinate
  process is a reader until the writer's lease is released.
- DRC, LVS, extraction, and signoff are separate verification flows with their
  own inputs, engines, and rule decks. This skill prepares a candidate for them
  and interprets their results; it never runs one as a side effect of routing,
  saving, or repairing.
- Saving OA, running a checker, repairing a violation, and relaxing a
  constraint are four independent authorizations.
- A broad statement such as "you may edit this layout" grants access to that
  view. It does not establish a design need for a tap, rail, strap, filler,
  candidate view, backup, or extra check. Derive each new structure from the
  confirmed contract, current PDK data, or a violation on the actual target.

## Freeze The Transaction

Select the requested stage first. A count, a saved-version question, or reading
an existing result does not need a full placement contract. For planning or an
authorized mutation, record only the fields that apply, and leave later
unrequested stages `not-run` instead of negotiating them:

- the confirmed bridge profile, process/PDK identity, and exact `lib/cell/view`;
- the requested outcome and the writable views or objects;
- the authoritative state: saved disk OA, a live unsaved cellview, or both;
- the validation budget: backup, candidate views, OA readback, DRC, LVS,
  extraction, or none;
- the finite candidate count, total read and mutation request counts, save
  count, and summary-output budget;
- the exact route-entry support level, retry budget, save/reject policy, and any
  hard via-array contract such as only `1x2` or `2x1` cuts;
- the per-stage net and object scope for Auto Route, internal repair,
  Optimization, via remaster, push, and save, each as a separate mutation;
- the live-marker policy: preserve the existing annotations, keep an external
  audit inventory only, or allow the native flow to clear and replace them;
- the tap contract: current process PDK, LUP or latch-up rule source, the
  confirmed maximum spacing and measurement convention, per-row and edge
  coverage, legal tap master and orientation, multi-height-row treatment, and
  whether a target DRC follow-up is authorized.

Add these when the corresponding stage is in scope:

- **Vertical output order:** the exact electrical net list in required
  top-to-bottom order, plus the rule that resolves each net to its real output
  pin figure. Semantic chain labels, instance enumeration order, an old plan,
  or script constants are not a substitute.
- **Antenna-cell proximity:** every existing or separately authorized antenna
  cell's signal terminal and its protected sink input, resolved from
  authoritative connectivity rather than geometric proximity.
- **Multi-terminal nets:** the complete terminal set, driver and sink roles, and
  transformed pin-access figures, kept as one shared routing tree.
- **Signal-chain clustering:** the ordered stage list and interstage nets
  derived from authoritative connectivity, with every branch, side load, and
  fixed endpoint retained.
- **Orientation search:** the legal transform set per master per row, and for
  each allowed transform the transformed signal pin-access, PR-boundary, supply
  rail, well, and implant geometry.
- **New or regenerated design:** the exact source schematic, target layout,
  target `physConfig`, expected source-generated functional-instance manifest,
  and whether each helper family is flat physical-only, flat bindable, or one
  hierarchical instance.
- **Private dispatcher exception:** the exact expressions, their order, the
  one-shot and no-retry boundary, and whether the live result may be saved.

Honor an explicit no-backup or no-validation budget for that transaction and do
not silently add either. If it conflicts with a required safety gate, pause and
report the conflict instead of choosing for the user.

## Distinguish Live And Saved State

For a narrow version question, obtain only the evidence needed for the named
state plane:

- identify saved disk OA with the exact OA path plus the relevant save marker
  and file identity;
- query the modified or dirty flag only when equivalence with an open GUI
  cellview actually matters;
- if the live cellview is dirty, report that GUI memory may be newer than disk
  and do not claim the two are identical.

Do not expand a version confirmation into exporter development, candidate
discovery, backups, DRC, or LVS. A live dirty readback never proves that disk OA
changed.

## Execute In This Order

### 0. Establish The Layout XL Artifact Set

For a new standard-cell design, freeze the exact source schematic, target
layout, target `physConfig`, and technology attachment before the first write.
Treat layout creation, `physConfig` creation, source generation, config and
connectivity reference assignment, active Binder update, and cross-probing
verification as separate state transitions. A successful Layout XL launch or a
Generate All From Source return does not prove that the `physConfig` exists, was
saved, points to the correct source, or is active in the current Binder.

Classify the artifact state before mutation:

- if the authorized layout and `physConfig` are both absent, create the exact
  pair and generate the frozen functional manifest once;
- if the layout already contains exactly that manifest but the `physConfig` or
  the config and connectivity references are missing, complete only the missing
  configuration;
- if the artifact set and references are already correct, make no generation
  write;
- if objects are duplicated, mixed with an unknown partial generation, dirty,
  or inconsistent with the frozen manifest, stop and reconcile instead of
  regenerating.

Use only APIs or native commands whose behavior is confirmed for the installed
Virtuoso release. Do not automate private form fields, depend on the focused
window, or replay a generator after an ambiguous return. After the one allowed
generation, read back the exact instance names and masters, the source identity,
the `physConfig` identity, and the config and connectivity references in one
bounded postflight.

For every helper family, freeze one representation before creation: flat
physical-only, flat bindable with an authorized schematic counterpart, or one
hierarchical instance. Saving a `physConfig` does not convert between these
representations or fold flat instances into hierarchy.

Report `source-generated`, `physConfig-saved`, `config-refs-bound`,
`active-binder-updated`, and `cross-probe-checked` separately. If only the
active Binder is stale, perform the authorized binding update rather than
regenerating from source. Diagnose "unbound" or "scattered" against source,
config and connectivity references, active Binder, helper representation,
geometry, and live versus saved state, one at a time. Geometry-only changes do
not repair hierarchy, and a flat-to-hierarchical helper conversion is a
separate representation change with its own affected views.

### 1. Place From Real Boundaries

Resolve one current effective constraint set before search: value, source,
design and process scope, and whether each entry is a hard constraint or a soft
objective. Replace superseded values instead of combining incompatible older
preferences. Keep this in the existing task state or script parameters rather
than introducing a mandatory new configuration file. A user preference cannot
override PDK legality; report a real conflict instead of resolving it silently.

Read each master's actual PR-boundary and transformed rail geometry, and place
only authorized instances and physical-only cells. Derive the placement lattice
and the origin test from the transformed PR-boundary, never from the instance or
master total bounding box. Internal master geometry at negative coordinates
does not by itself violate a PR-boundary origin contract.

For user-protected groups, preserve membership, each member's master and
orientation, and every member-to-member offset. Whole-group translation uses
one common displacement and does not authorize internal repacking, member
mirroring, or group rotation. Lock pin-to-net mappings whenever the schematic
is read-only.

When vertical output order is requested, keep the frozen ordered net list
separate from functional or semantic chain labels. After generating each
candidate, resolve every frozen net to its actual output pin figure, apply the
candidate instance transform, sort the figure centers by Y from high to low, and
assert that the resulting list matches the frozen list item for item. A missing
or ambiguous figure, or a center-Y tie that prevents a strict order, rejects the
candidate. Repeat the same assertion against the candidate's transformed output
pin figures immediately before an authorized save. Row indices, instance
origins, and plan summaries do not substitute for this check.

A master without a PR-boundary does not waive the output-order gate. Use the
real output pin figure plus a separately authorized equal-size footprint rule
for that named master only, and keep the exception local to that footprint
decision. Without such a rule, keep placement blocked rather than skipping the
assertion.

Build every placement search from one fresh, bounded, full-geometry preflight
that covers the placement question. Include the current placement as a
candidate, preserve its exact connectivity unless schematic writes are
separately authorized, and reject stale hard-coded counts, metrics,
coordinates, or window identifiers. Any user edit, source regeneration, binding
change, or referenced master update invalidates the frozen snapshot and every
derived count, coordinate, metric, and candidate assertion. Reuse an older
script only for its still-valid algorithm or a release-confirmed API shape,
never for its target, manifest, coordinates, or acceptance state.

A geometric objective such as half-perimeter wire length, rectilinear
minimum-spanning-tree length, congestion, or pin-access clearance proposes
candidates. It does not prove that a candidate is more routable or has shorter
routed metal.

#### Equivalent Inputs And Legal Mirroring

Escaping the minimum of a net's length is not a goal in itself; the goal is the
lowest whole-placement route cost for the complete affected net set.

Across processes, include legal left-right mirroring as an operator inside the
same joint placement search. For a fixed row's vertical sense, compare only the
horizontal-mirror alternatives allowed by the current master, library, site,
and PDK. Common pairs are `R0` and `MY` for an unflipped row and `MX` and `R180`
for a vertically flipped row, but derive and read back the actual legal set
instead of treating those examples as a rule. Apply every candidate transform
to each signal pin-access figure as well as to PR-boundary, rail, well, and
implant geometry.

Left-right mirroring is not an arbitrary 90-degree rotation and does not relax
metal spacing or preferred-direction rules. Preserve the instance master,
terminal-to-net mapping, and logical function. An equivalent-pin permutation is
a separate connectivity change that needs its own authorization. Reject a
mirror that breaks legal abutment, site alignment, supply-rail continuity, well
or implant continuity, tap coverage, or current PDK constraints.

#### Net Topology Preferences

Score a signal net with exactly three resolved terminals as one shared
rectilinear tree. Include candidates in which two pin-access regions are
brought close and the third is vertically aligned with their feasible branch
region, so a short local connection plus one shared trunk serves all three
terminals. Choose the close pair and branch location from the complete placement
objective and the actual transformed pin figures, not from instance names,
origins, enumeration order, or an assumed driver and sink pairing.

Use half-perimeter or rectilinear Steiner length only as a placement proxy, and
prefer comparable actual router length when it exists. Do not sum all three
pairwise distances, which counts shared segments more than once. Vertical
alignment here is a placement and topology preference; it does not force a
routing layer direction, an exact X equality when pin access or blockage makes
that illegal, or any special rule for nets with more than three terminals.

Treat an authoritative linear signal chain as one placement cluster: keep
consecutive stages in chain order whenever legal, minimize each transformed
driver-output-pin to successor-input-pin distance, and minimize the cluster's
routed span. A chain may run left to right, right to left, or serpentine across
rows; when a row transition is needed, put the two consecutive stages at the
nearest legal cross-row positions. Derive the chain from current connectivity.
Side inputs do not erase a chain, but fanout, reconvergence, shared loads, and
fixed terminals stay in the complete objective, and an interstage net with no
unique successor must not be silently classified as part of one linear chain.

#### Occupancy And Filler

Unless the current transaction explicitly enables multi-height physical cells,
restrict automatic occupancy fill to masters whose transformed PR-boundary spans
exactly one standard-cell row. Authorization from an earlier layout or task does
not carry forward.

Within the confirmed single-height master set, use a decoupling-capacitor-first
policy and require exact integer-site occupancy with no overlap, fractional
site, or unfilled remainder. When a legal decoupling-capacitor-only exact cover
exists, first minimize the number of instances; on a tie, prefer the
lexicographically larger width sequence so larger cells win.

Under that policy, confirmed legal filler may close only a residual gap smaller
than the smallest applicable legal decoupling capacitor. Do not replace
otherwise usable cells with filler merely to reduce the instance count. If no
applicable master exists or no legal exact cover can be formed, report the
conflict and the feasible options instead of silently switching the whole gap
to filler. An explicit current choice to use all filler overrides that
preference, not the single-height, integer-site, or exact-occupancy
requirements. Neither policy permits overflowing the gap, moving functional
instances, changing the row envelope, substituting tap or antenna cells, or
enabling multi-height cells automatically.

When the current transaction explicitly re-enables multi-height cells and
selects an aligned two-column internal-tap wrapper, keep edge taps and internal
taps as separate placement sets. Preserve the required edge taps, put every
non-edge tap on exactly two legal X columns, and keep each column vertically
aligned across all rows it serves. Select any flanking wrapper from the current
library and read back its master, height, legal transforms, and required
placement; no wrapper from a previous project is a default.

Solve the complete affected-row occupancy in integer sites before writing. If a
full row cannot accommodate the tap columns and their wrappers, move only
authorized functional instances as part of that complete solve, and never
accept overlap, fractional-site placement, or an unplanned hole. Create a
layout-only wrapper with the physical-only flag at instance creation, since the
flag is not a writable property afterwards. Add schematic counterparts only for
non-physical-only taps, and only in a separately authorized helper schematic.
When the solve widens the block, recompute the common M1 rail extent and any
authorized edge well completion together with the new envelope.

### 2. Establish Explicit M1 Supply Tracks

After placement, inventory the expected VDD and VSS rail role for every row,
including any intentionally shared row boundary. Identify each intended
horizontal rail using all of: row and transformed master-rail geometry; supply
net identity and power-domain ownership; layer, purpose, orientation, bounding
box, and physical overlap with the cell rails; and figure role, including
whether it is a rail body, pin figure, vertical strap, via landing, existing
route, or unrelated local supply geometry.

For an origin-aligned digital array, align the transformed cell PR-boundary
envelope's lower-left to the origin and every cell to its origin-referenced
legal site and row lattice. Do not substitute the instance origin or the total
geometry bounding box. This contract does not require every physical figure to
have nonnegative coordinates: legal master overhang, well completion, or rail
geometry may extend outside the envelope. A separate routing-margin constraint
must be confirmed independently; do not translate the array away from its
PR-boundary origin to hide overhang.

Use one common X start and one common X end for the power and ground tracks in
the same planned track set, so their lengths are uniform. Size that common
length from the actual signal-routing footprint rather than only the placed-row
width. When congestion or pin access needs more area, expand the envelope
consistently in both length and vertical allocation. Recompute the shared
envelope for the whole set instead of stretching individual rails to unrelated
lengths.

The two exposed horizontal M1 rails at the outside vertical boundaries of a
standard-cell array must both be ground: the lower rail of the bottom row and
the upper rail of the top row. Resolve the exact ground net name from the frozen
power domain rather than hard-coding a name from another design. Before routing
or an authorized save, assert that both outside rails exist, span the common
track extent, own the expected ground net, and physically contact the
corresponding cell rails. This applies to the two outside boundary rails only;
it does not reclassify every M1 figure in the top or bottom row as ground.

Create a new explicit track or extend only the designated horizontal rail. Net
ownership alone is not a selection rule. Never iterate over every drawing-layer
rectangle on a power net and stretch all matches to the row width.

Treat pin text, pin figures, labels, vertical straps, existing routes, local
jumpers, via landings, other power geometry, and power-domain boundaries as a
protected set unless the exact object is authorized. Before writing, list the
selected rail figures with their old and proposed bounding boxes. If the
selected count or role differs from the frozen expected rail set, stop before
mutation.

The completed track must be bound to the intended supply net and physically
touch or overlap every corresponding cell rail. A label, a common net name, or
a later virtual-connect setting in the checker is not physical continuity.

### 3. Close Placement With Route Feedback

Use a bounded route-feedback loop only when the user authorized the resulting
route mutations and a finite candidate count. Run routability checks with the
frozen power exclusions, marker policy, layer policy, and error limit. Treat
their annotations and reports as candidate evidence, not as a placement
acceptance certificate.

For each authorized candidate or mutation stage, batch deterministic object
changes into one guarded OA request. Freeze the total request count before
dispatch; do not query, mutate, or save one instance, net, route, or via at a
time.

Before dispatch, determine whether the selected native flow invokes a
routability check with annotation clearing, or any equivalent operation. An
external inventory preserves audit evidence, not the live marker objects. If
the user requires existing live markers to remain and the flow will clear them,
stop before routing and ask the user to choose another entry or relax that
requirement. Do not restore stale markers after geometry changes unless that
exact restoration is separately authorized.

Rank offline candidates before invoking the expensive router, but accept a new
placement as better only from comparable actual-router evidence. Compare the
same net scope, route settings, detailed-check level, error classes, and via
policy. Never attribute an error change to placement, via maximization, or a pin
swap when the checker configuration also changed.

### 4. Route Signals Only

Run signal routing only after the real M1 supply tracks exist, with an explicit
exclusion list for all power and ground nets. Record routed and excluded nets,
remaining errors, opens, and shorts. Router completion does not prove supply
continuity, DRC, LVS, antenna, electromigration, or signoff.

Separate implementation provenance from invocation support. A log that sources
a vendor-installed Tcl file proves a native implementation branch, not that the
initiating callback is documented, public, supported, or authorized. Do not
interpret "use the Virtuoso script" as permission to call private dispatcher
functions, directly source internal flow files, or use an installed-only
undocumented symbol. Prefer a documented Route API with equivalent semantics. A
private dispatcher is an exception only when the current user explicitly
confirms the exact profile, cellview, expressions, order, one-shot scope, and
save boundary. Rebind the exact target immediately before each call, do not
retry an ambiguous return, and never directly source internal Tcl files. If
those conditions are absent, stop and present the supported foreground path or
a separately authorized controlled evaluation rather than substituting a
custom metal generator.

Treat every stage's actual net scope as a write boundary. A statement that
power and ground will not be routed during automatic routing does not prove
that a later optimization excludes them. If a stage authorized for selected
signal nets expands at runtime to all design nets, stop the sequence unless
that exact expanded scope was confirmed; after a completed expansion, require
the changed-net identities and a protected-object readback before making any
preservation claim.

A bridge evaluation does not necessarily echo the literal initiating expression
into the vendor log. Prove a controlled dispatch with all three of: the external
exact call record, a unique begin and end marker emitted by the same bounded
wrapper, and the bounded native log interval between those markers. Never append
or synthesize a callback line to make the log look like a foreground transcript.

If any route or mutation dispatch times out, is aborted, loses transport, or
returns ambiguously, mark the outcome unknown, invalidate the lease, stop all
later stages, and perform at most one bounded reconciliation. Do not retry,
optimize, remaster, save, discard, or restore the uncertain candidate first.

#### Route Acceptance Vector

Treat router acceptance as this ordered state vector:

1. `command-completed` - the exact initiating request returned;
2. `connectivity-closed` - attempted signal nets have the required completion,
   opens, and shorts result after the final connectivity-changing mutation;
3. `detailed-geometry-closed` - after the final route, repair, optimization, cut
   maximization, or via remaster, a comparable final detailed-error and unroute
   check is explicitly zero;
4. `via-contract-closed` - every routed via satisfies the confirmed cut-array
   and layer policy;
5. `saved-readback-closed` - an authorized save was independently reopened or
   read back from disk OA.

A completion percentage, zero opens and shorts, an API return of true, sourced
flow names, or route and via counts close only their own layer. A missing,
stale, or nonzero final detailed-error result fails the geometry gate, and a
later route summary cannot erase it. Optimization, repair, cut maximization, and
via remaster are later geometry mutations, not a final detailed check. If the
authorized budget does not include a comparable post-mutation check, report the
route as rejected; the missing gate does not authorize running another checker.

Every later route, repair, optimization, push, or remaster invalidates any
earlier acceptance evidence it can affect. After the final mutation, re-
establish connectivity, then the same configured detailed-error and unroute
gate, then the effective via-array contract from OA readback.

Keep router operation counts and live OA totals separate. When a route summary
reports newly created routes, compare it with before and after OA route-container
counts instead of presenting the live total as the router delta.

#### Strict Via-Array Gate

Treat double-cut preferences, cut maximization, max-rule parameter selection,
and double-cut-only remastering as requests, not as guarantees. The router may
leave single-cut vias when space, enclosure, valid-via constraints, route
status, or its insertion mode prevents replacement.

Inventory every routed via after the final geometry mutation. Resolve the cut
rows and cut columns from the instance override when present, and from the
via-definition defaults otherwise. Require the exact allowed arrays, for example
one-by-two or two-by-one; do not weaken that to "two or more cuts" unless the
user did. Report the effective-array histogram and the remaining violations by
via definition, net, coordinate, and route role. A native table that labels a
via as a two-cut via does not replace this readback.

Classify direct pin access only when terminal and net ownership match, the via
bounding box overlaps the transformed master pin figure, and that pin figure
lies on one of the via definition's metal layers. Keep these facts separate:
direct pin access versus route stack or channel; dimensional template fit;
complete site legality under enclosure and surrounding geometry; and the
proposed remedy such as offset, push, reroute, placement change, or manual
replacement.

A fitting bounding box is only a necessary dimensional screen. Do not infer
that a push or a placement change is required, or that the site is DRC legal.
When a native log says the run was done without push, do not infer that a
displayed push limit was used. Pushing vias can move routes and create new
violations, so enabling it is a separate geometry mutation that requires
explicit authorization and a repeated final route acceptance check.

### 5. Confirm LUP Tap Spacing, Then Use Target DRC

Before tap placement, reuse the current task's confirmed tap contract and the
still-applicable process latch-up or well-tap rule evidence. Ask only about
missing, conflicting, or invalidated values rather than re-asking for values
that have not changed. Recheck the actual geometric spacing after any change
that affects tap coverage:

- whether the rule limits tap-to-tap pitch, edge-to-edge distance, or the
  maximum distance from any protected well or substrate point to a tap;
- the numeric limit, edge-to-first-and-last-tap coverage, affected wells and
  power domains, legal tap master and orientation, and whether each row or
  multi-height well segment must be served independently;
- the exact rule deck or document revision when it is available.

Do not infer these inputs from another process, library, test cell, or task. In
particular, no spacing value is a global constant. When the user confirms a
per-design spacing, record it as a task-local maximum. Unless the rule wording
requires an exact pitch, interpret a stated spacing as an actual distance no
greater than that value. Snap every tap to legal integer sites and remeasure the
effective distances after wrapper insertion, row resizing, or placement
optimization; never round a planned pitch upward past the confirmed limit.

For each affected row, derive a finite tap count and coordinates from the actual
transformed PR-boundary and well span under the confirmed measurement
convention. Include the two edge intervals when the rule covers them; a simple
floor of row width divided by pitch is not sufficient. If the measurement
convention, edge treatment, row coverage, or multi-height behavior remains
unclear, stop before tap insertion and ask rather than choosing a convenient
interpretation.

A confirmed latch-up contract is a valid design basis for inserting taps even
when DRC is outside the current budget. Tap insertion, layout save, DRC, and any
DRC-driven repair remain separate authorizations. When DRC is authorized, run
and parse the target layout's own process-confirmed deck, and use substrate,
well, tap-connection, and maximum-distance violations to validate or correct the
implemented count and coordinates. Report a rule-constrained placement with DRC
omitted as constrained but not checked, and never call it clean. If neither a
confirmed current rule contract nor target-layout DRC evidence exists, keep the
tap decision blocked.

Never hard-code one tap at the right edge of every row, and never transfer a tap
conclusion from a different layout.

### 6. Interpret LVS Without Hiding Geometry

Use only the current process deck and runset, with its confirmed virtual-connect
policy. Virtual connect changes how the comparison is interpreted; it cannot
replace M1 rail contact, a top-level supply connection, extraction continuity,
or separation between power domains. Report whether virtual connect was
disabled, merely configured, or proven active, and name the affected nets.

## Mutation And Completion Gates

Apply the minimum selected OA change in one bounded transaction per authorized
stage or isolated candidate. Stop after any error and inspect the possible
partial state before another write. Report exactly which objects changed and
which protected objects were untouched.

Read back each protected class affected by the operation or required by its
declared protection set: instance name, master, position, orientation, and
PR-boundary placement; terminal-to-net mapping; supply rails; labels; markers;
route containers; and vias. Establish the scope from the actual native effects,
including neighboring geometry, hierarchy, shared rails, changed nets, and
annotation clearing, not only from the requested object name. Reuse unaffected
evidence only while its identity and validity conditions hold; when the effects
or the reader's coverage are unknown, retain the broader checks.

Matching totals, samples, and limited bounding boxes do not replace the required
per-class comparisons. Whenever persistence is claimed, verify the saved disk
OA identity; a live dirty readback cannot prove that disk OA changed.

Do not save a candidate that fails connectivity, detailed geometry, or a hard
via contract. Keep it explicitly live and unsaved, preserve the last accepted
disk OA identity, and ask whether to discard it, authorize a bounded repair or
push pass, or relax the contract. Do not start DRC or LVS on that rejected
candidate and do not silently promote it to the new baseline.

Route-quality states:

- `planned` - contract and proposed object set only;
- `connectivity-closed` - the required completion, opens, and shorts result is
  proven after the final connectivity-changing mutation, while later gates
  remain open;
- `route-rejected` - a required connectivity, detailed geometry, or via gate is
  missing, stale, or failed;
- `route-gated` - connectivity, detailed geometry, and the via contract have
  each passed after the final geometry mutation.

Persistence and verification states:

- `live-unsaved-candidate` - geometry exists only in a dirty open cellview, and
  no disk persistence is claimed;
- `saved-unverified` - the save succeeded but the authorized budget excluded a
  post-write readback;
- `oa-readback-checked` - the saved target and selected geometry were reopened
  or independently read back;
- `drc-checked` - the named target and confirmed deck produced parsed DRC
  results;
- `lvs-checked` - the named source and layout pair and confirmed deck produced a
  parsed LVS result.

A result can legitimately be both route-gated and live-unsaved-candidate. Report
route quality and persistence as separate dimensions.

## Reporting

Report the exact target, lease identity, mutation-request count, changed and
protected object classes, save and readback state, backup path when one was
created, the exact commands or Route APIs run, the preset identity when used,
the bounded route-log path, routed and excluded nets, remaining router errors,
and DRC or LVS summary paths when those were run. List backups, candidate views,
exporter or tool development, DRC, LVS, extraction, GUI inspection, and
post-write checks as run or not run only when they are relevant to the current
completion claim. Do not expand a narrow count or version answer into an
unrelated stage checklist.
