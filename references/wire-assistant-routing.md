# Wire Assistant And Route API Notes

These notes describe the tool layer of the IC618 Virtuoso Interconnect
Assistant (Wire Assistant) and the Route APIs behind it. They are not a PDK
rule deck, not a reusable preset, and not authorization to run or delete
routing. All values below are documented behavior or generic requirements, not
design-specific measured results. Before any live use, re-establish the
release, the target `library/cell/view`, the process rules, and the current
save/dirty state.

## Route API Map

The dynamic Route menu is implemented by compiled private callbacks. For
automation, prefer the documented `rte*` functions below where their semantics
match the task. Do not use `_ia*` or `_rtePopup*` callbacks by default.

| Route action | Counterpart | Geometry effect | Return semantics |
|---|---|---|---|
| Check routing prerequisites | `rteCheckDataForRouting` | No route geometry; may create markers and an XML report | `t` means no errors were found. This is the only reviewed check whose `t` carries that meaning. |
| Routability check | `rteCheckRoutability` | No route geometry; creates violation annotations | `t` means the check ran to completion, not that violations are zero. |
| Automatic routing | `rteAutoRoutes` (installed-only symbol) | Would create route geometry if used | Build-local and unverified: absent from released reference material, with no documented return contract. |
| Search and repair | `rteSearchAndRepair` | Modifies route geometry to repair same-net and different-net spacing; may attempt to close opens | `t` means the call completed; the result is not closed by the return value. |
| Fix violations | `rteFixViolations` | Modifies route geometry for selected violation classes; may move wires and vias | `t` means the call completed; verify the exact keyword signature first. |
| Optimization | `rteOptimizeRoute` | Refinement routing that can reduce vias and straighten wires; modifies geometry | `t` means the call completed; it does not prove a clean detailed result. |
| Delete routing | `rteDeleteRoutedNets` | Destructively deletes routed paths; `?keepPower` defaults to `nil` | Requires an explicit target, a backup, and explicit deletion authorization. |
| Antenna check | `rteCheckAntenna` | No route geometry; evaluates process antenna conditions | `t` means the check ran to completion, not zero violations. |
| Antenna fix | `rteFixAntenna` | Inserts jumpers and/or diodes and may push wires; modifies geometry | `t` means the call completed; validate the resulting geometry separately. |

Rule for reading return values: unless a function's version-local documentation
says otherwise, treat `t` from a mutating API as "the call completed"; only
`rteCheckDataForRouting` means "no errors found".

Reference material lives under the IC618 installation, for example the Finder
file `<cadence_install>/IC618/doc/finder/SKILL/Custom_Layout/sklayoutref.fnd`,
`<cadence_install>/IC618/doc/sklayoutref/vsr.html`, and the context file
`<cadence_install>/IC618/tools/dfII/etc/context/64bit/rte.aux`. Finder offsets
vary by release; look up each function name in the local build.

## Undocumented And Private Symbols

Two symbols are easy to reach and should be avoided as automation entry
points:

- `rteAutoRoutes` appears in the installed context file but is absent from the
  installed Finder and HTML reference documentation. Its behavior, support
  status, and return contract are unverified. Treat it as build-local until a
  separately authorized controlled test proves otherwise.
- `_iaAutomaticExecuteCmd` is a private UI dispatcher inside the compiled
  Interconnect Assistant. It is not a supported automation API, and a
  bridge-level call may execute it without leaving a literal expression in the
  tool log.

Do not source the internal `ia/tcl` flow files directly. Their layout differs
by release and by installation. A generic view of the Auto Route branch is:

```text
<cadence_install>/IC618/share/cdssetup/dfII/ia/tcl/autoRoute/flow.tcl
  .../device/flow.tcl -> .../device/MST/flow.tcl -> .../MST/normal/flow.tcl
  .../commonUtils/final.tcl
```

These scripts depend on Interconnect Assistant state, environment values,
selection sets, and private procedures; readable installed implementation is
not a supported automation contract.

Exception condition: a private dispatcher or undocumented symbol may be used
only when the user confirms, for that exact call, the profile, cellview,
expression or expressions, order, per-stage net or object scope, one-shot
scope, and save/no-save boundary. When no documented API reproduces a requested
flow, stop and present the supported foreground action instead.

## Power Routing And Scheme Functions

Signal Auto Route normally omits power and ground nets. Power routing is a
separate, geometry-changing family:

- `rtePowerRouteBlockRing`
- `rtePowerRouteCellRow`
- `rtePowerRouteCoreRing`
- `rtePowerRoutePadRing`
- `rtePowerRoutePinToTrunk`
- `rtePowerRouteStripes`
- `rtePowerRouteTrimStripes`
- `rtePowerRouteViaInsertion`
- `rtePowerRouteTieShield`

These functions create or modify rings, rails, trunks, stripes, vias, or
shield ties. A `t` return does not prove automatic save, DRC/LVS, EM/IR,
antenna cleanliness, or connectivity closure.

The matching scheme constructors are `rteCreateBlockRingScheme`,
`rteCreateCellRowsScheme`, `rteCreateCoreRingScheme`,
`rteCreatePadRingScheme`, `rteCreatePinToTrunkScheme`,
`rteCreateStripesScheme`, and `rteCreateViasScheme`. Creating a scheme changes
configuration state only; it does not route or save layout geometry.

## Presets

The documented preset APIs are:

- `vsrLoadPreset(fileName ?directory ... ?execMode ... ?path ...)`
- `vsrSavePreset(presetLabel fileName ?directory ... ?path ...)`

`vsrLoadPreset` applies settings to the Wire Assistant and VSR Options forms;
it neither executes routing nor mutates layout geometry. `vsrSavePreset` writes
a `.preset` file for later reuse; it does not save the layout. Use an explicit
path and read the form or environment values back after loading.

## Double-Cut And Push Semantics

IC618 documents `layout useDoubleCutVias` as an instruction to attempt double
cuts **if space allows**. It is not a hard all-via constraint. The same
preference-versus-guarantee distinction applies elsewhere:

- `wireViaParamCalcMode=minRulesAndViaDef` resolves to cut maximization with
  `useMaxRule`. It selects the source of legal via parameters; it does not
  force every via to have two cuts.
- `remaster_via -double_cut_only true` restricts remaster candidates to double
  cuts. It does not promise that every selected single-cut via can be
  replaced.
- A printed `Push limit` is not evidence that push ran. The command must
  contain `on_wire_push` or `off_wire_push`, or an equivalent documented push
  option, for push to be enabled.
- In the Optimization flow, push is enabled only when the interactive push
  settings allow it (`layout drdEditMode` not `off`, `layout drdEditPushEnabled`
  true); only then does the flow add `on_wire_push` and, when off-wire
  insertion is allowed, `off_wire_push`. `-push_limit` bounds how many routes
  may move; it does not enable push.

Push, offset, reroute, route deletion, and placement movement are distinct
geometry mutations; never enable or infer one from a double-cut preference, and
rerun the same detailed geometry gate after the final mutation.

For a strict `1x2` or `2x1` contract, inventory every routed via after the last
route mutation. Resolve `cutRows` and `cutColumns` per via from OA: use the
instance override when it exists, otherwise the viaDef defaults, and require
the exact allowed pair. A cut count of two or more, a via bounding-box size,
`useDoubleCutVias=t`, or a successful remaster return is not a substitute for
that readback.

## Direct Pin Access Classification

Classify a via as direct pin access only when all three conditions agree:

1. the terminal and the net ownership match the intended connection;
2. the via overlaps the transformed master pin figure;
3. the pin figure layer is one of the viaDef metal layers.

Keep direct pin access, route stack or channel, dimensional template fit, site
legality, and remedy choice as separate facts. A fitting bounding box is only a
necessary screen; it does not prove enclosure, neighboring-route spacing, stack
legality, DRC cleanliness, or that a push or placement change is required.

## Route Acceptance Evidence Layers

Route acceptance is layered, and each layer requires its own evidence:

1. **command-completed** — the API returned `t`, or the flow printed a summary
   line. Nothing about the geometry is yet proven.
2. **connectivity-closed** — the router reported the attempted nets as
   connected, with zero reported opens and shorts for the exact attempted net
   scope.
3. **detailed-geometry-closed** — the final detailed pass reports zero
   remaining errors and zero unroutes at the frozen check level.
4. **via-contract-closed** — the OA-effective `cutRows`/`cutColumns` inventory
   satisfies the required rule for every routed via.
5. **saved-readback-closed** — the saved view, reopened and re-read, still
   shows the accepted connectivity, geometry, and via contract.

`Completion=100%`, zero reported opens/shorts, and an API `t` each close only
their own layer. Any later route, repair, optimization, push, or remaster
operation invalidates the earlier acceptance evidence for connectivity,
detailed geometry, and the via contract; the checks must be repeated against
the final candidate before the route is reported as accepted. If a required
check is outside the authorized budget, report `route-rejected` instead of
running it merely to complete the audit.

## Marker Lifecycle

Interconnect Assistant marker objects are live annotations, not files. If the
user requires existing live markers to be preserved, and the native flow that
would run is known to invoke `-clear_annotations`, reject the dispatch before
it starts.

An exported marker inventory is audit evidence only; it does not preserve the
objects. After geometry changes, do not restore old markers unless restoration
is separately authorized, because their coordinates and violations may be
stale. Keep these annotations distinct from any log sentinels.

## Count Semantics

The following counts are different quantities and must not be compared or
combined without an explicit mapping:

- **design nets** — every net visible to the design database or current flow;
- **attempted nets** — the subset the router tried to connect;
- **router `Routes`** — the operation summary's route count, not an OA object
  total;
- **OA route containers** — live database objects that need their own keyed
  before/after counts;
- **via instances** — OA via objects; their cut-array contract comes from
  effective `cutRows`/`cutColumns`, not from the via count;
- **optimizer changed nets** — nets actually modified by an optimization
  stage, which must be named when protected-net preservation matters.

A wrapper should emit keyed fields (profile, host, workdir, release,
`lib/cell/view`, invocation, support level, authorized versus actual scope,
changed-net names, direction and marker policies, dirty/save state, protected
classes) instead of anonymous positional tuples.

## Layer Direction Policy Versus Route Flow

Layer direction policy and route flow selection are independent choices.
Setting a preferred layer does not set a direction rule, and changing the
route flow does not change the direction policy.

When horizontal and vertical routing must both be allowed on every routable
layer, the explicit form value for each layer must be `Allow`. Runtime
soft-cost lines such as `set_router_tax -wrongway 0.01` penalize wrong-way
routing while wrong-way routing remains enabled; they do not restrict a layer
to one direction. Such lines, a disabled direction check, or mixed
horizontal/vertical route lengths do not prove the form value was `Allow`.
Read the form, preset, or environment value independently per design.

A permissive `minimum cuts` setting also cannot satisfy a strict per-via array
contract; freeze a process-supported cut policy before routing and still verify
every resulting via from OA readback.

## Row-Based Placement Preconditions

When routing relies on standard-cell row abutment, confirm for the current
design: the placement tile is the actual master PR-boundary figure transformed
into instance coordinates, not the master or instance bounding box; within a
row, transformed PR boundaries share identical top and bottom edges and abut
exactly with zero gap and zero overlap; every instance in a row uses the same
orientation; and a second row is vertically mirrored so adjacent boundaries
abut vertically. Whether that abutment joins the VDD/VSS rails depends on the
cell family and the legal orientation; verify it for the current library.
"Merge" here means boundary abutment only, not flattening or combining
masters, and adjacent rows need not be equally wide.

## Automation Contract

1. Reconfirm the profile, host, release, process rules, workdir, exact
   `lib/cell/view`, and the current save/dirty state; back up the view and
   capture route geometry, labels, pins, net ownership, and power rails before
   any mutation, unless a no-backup budget is explicitly frozen (then preserve
   the disk view identity and prohibit saving a rejected candidate).
2. Freeze the explicit layer range, preferred layers, via policy, minimum cuts,
   width/spacing policy, snap mode, design style, route flow, per-layer
   direction policy, blocked-pin policy, and violations-versus-opens policy,
   and freeze the authorized net/object scope separately for Auto Route,
   repair, optimization, remaster, push, and save.
3. Load or save a preset only when its path and contents are in scope; read the
   settings back, since a successful load routes nothing. Apply marker handling
   as live preservation, audit inventory only, or authorized clearing — reject
   a flow that runs `-clear_annotations` when preservation is required.
4. Call documented Route APIs with the explicit cellview and explicit net or
   region scope, and check exact keyword spelling against the installed manual.
   Do not build unattended automation around `_iaAutomaticExecuteCmd`,
   `leAutoRoute`, or internal Tcl sourcing; a private dispatcher requires the
   exception fields above to be confirmed first, one dispatch per expression.
5. Capture the exact initiating request plus one bounded log interval per
   operation, correlated by unique BEGIN/END markers, covering the main flow,
   topology branch, specialty counts, omitted power/ground nets, exclusions,
   layer statistics, opens, shorts, and the final detailed-error/unroute result
   after all geometry mutations. Do not fabricate a literal callback echo.
6. With a hard via-array rule, record before/after cut-count histograms by
   viaDef and classify direct pin versus route stack; a disallowed array fails
   the gate and must be reported before push, reroute, placement change, rule
   relaxation, or save.
7. After the final optimization, repair, or remaster, require the same
   configured connectivity result, the detailed-error/unroute check, and the
   OA-effective via-array inventory; keep those checks inside the authorized
   budget or report `route-rejected`.
8. Read back instances, terminal-to-net connectivity, power rails, labels,
   markers, route containers, vias, and disk view identity as separate
   protected classes, with operation deltas kept apart from live totals. Run
   process-confirmed DRC and, when requested, extraction/LVS; router returns
   cannot replace them, and route acceptance does not authorize either run.

Freeze the net scope of each stage: if a router stage initializes with a narrow
scope and a later optimization silently expands to all design nets, compare
both scopes explicitly and reject the expansion unless it was authorized.

## Known IC618 Documentation Defects

The published IC618 manual disagrees with itself or with its own examples for
several names. Reported cases include:

| Function | Reported inconsistency |
|---|---|
| `rteFixViolations` | keyword variants across documentation and examples |
| `rteOptimizeRoute` | `detailCritic` versus `critic` |
| `rteFixAntenna` | `model` versus `models` |
| `rteCreateStripesScheme` | `minStripeWidth` versus `minStripeLength` |

The conclusion is procedural: do not copy an example blindly. Resolve the exact
signature with the version-local documentation for the installed build, or
with a separately authorized minimal test, before a real design mutation.
