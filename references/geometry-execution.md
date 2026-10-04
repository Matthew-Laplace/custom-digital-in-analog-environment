# Geometry Execution

Read this reference when the task actually creates or edits OA geometry or
binding state. It covers the mechanics; the owning Skill covers stage order,
candidate choice, and route acceptance. The shared rules for ownership, leases,
batching, and unknown outcomes are in
[bounded-operation-contract.md](bounded-operation-contract.md).

## Hard Rules

- Freeze the shared operation contract and acquire one continuous write lease
  before mutation. The root task is the single writer; readers wait until the
  mutation is quiescent.
- Before geometry creation or editing, freeze the geometry-driving rule plan
  from authoritative current evidence. Each rule needs a resolved value, a
  scope of top-only, cell-only, or both, and an exact target. Applicability is
  not write authorization; an unresolved rule plan blocks mutation.
- The write lease excludes concurrent manual editing. Release it before handing
  control to the user. After a user edit, invalidate the prior lease and the
  full-geometry preflight, then reacquire through fresh identity, dirty-state,
  and bounded preflight evidence before another mutation.
- Record save, readback, and each physical verification as separate gates in the
  shared verification vector. Reuse current authorization for necessary
  in-scope readback; an independent gate still needs its own authorization. An
  optional or skipped gate grants nothing, and skipping a repair never
  suppresses an enabled check.
- Confirm the exact `lib/cell/view` before editing. Do not infer the target from
  whichever window happens to be open.
- Create a backup only when it is authorized. Otherwise preserve the accepted
  disk OA identity and do not save a rejected live candidate.
- Never delete, move, rebuild, or omit existing text, label, or annotation
  objects unless the user explicitly asks for text or label changes. For edits
  whose protection scope includes text, inventory labels separately and compare
  name, layer, bounding box, and position. Do not infer label absence from
  drawing-purpose counts.
- Preserve connectivity topology. If two metal regions, pins, vias, gates,
  sources, drains, or pads were connected before, keep them connected unless the
  user explicitly requests a topology change.
- If source, drain, gate, or pad intent is ambiguous, stop and ask. Do not
  "optimize" by deleting user-drawn routes.
- Apply the smallest local patch that addresses the rule or coordinate problem.
  Avoid broad layer rebuilds after manual edits.
- Treat an instruction such as "do not consider density" as a generation or
  repair objective for that stage: do not proactively add density-driven fill or
  repair density unless it is separately requested. This does not change a later
  checker preset, deck, density switch, result parsing, or clean criterion.
- Read back OA geometry after each bounded mutation transaction when postflight
  is authorized. Do not turn repeated objects into per-object round trips. A
  SKILL return value or a saved script log is not enough.
- If a load or evaluation errors after modifying data, stop and reconcile the
  affected view once under the shared contract. Do not automatically restore,
  resend, or save a partial candidate; restoration needs an authorized exact
  source and target.
- Check every database-returning call before using its result. Guard library,
  cellview, technology-file, terminal, and instance lookups against an empty
  return.
- Treat layer ranges, preferred layers, via policy, minimum cuts, snap mode,
  route scope, design style, flow, and violation policy as user inputs. Never
  infer or silently reuse them across designs or processes.
- Prefer documented Route APIs. Treat a build-local private dispatcher as
  unsupported: use it only for a separately confirmed, exact
  profile, cellview, expression, order, one-shot, and save-boundary evaluation.
  Never directly source a vendor's internal flow files.
- Keep router connectivity and geometry evidence separate. Full completion or
  zero opens and shorts does not override remaining router errors, and it does
  not prove DRC, LVS, antenna, electromigration, or signoff.
- Treat route deletion, repair, optimization, antenna fixing, and power routing
  as geometry mutations. Their return values do not prove an automatic save,
  persistence, clean geometry, or recoverability.
- On timeout, abort, transport loss, or an ambiguous return, mark the mutation
  unknown, stop the sequence, and follow the shared single reconciliation rule.
  Never blind-retry or save the uncertain candidate.
- Use the grid and route-angle policy required by the active project. Passing
  DRC does not waive a confirmed geometry policy, and a value recorded for one
  project is not a default for another.
- Every routed signal metal must physically touch or overlap the intended pad
  metal. Do not stop near a pad edge.
- Preserve a rounded or filleted style only when it is part of the current
  drawing or is needed to avoid an acute-angle violation. Use geometric readback
  for the requested shape change; DRC safety remains unverified unless an
  authorized run proves it.

## Workflow

1. **Identify the target and intent:** the exact `lib/cell/view`; the process and
   PDK when a checker may run; whether connectivity, geometry only, text and
   labels, or hierarchy are in scope; and whether backup, save, postflight, DRC,
   LVS, repair, or GUI interaction are authorized. Freeze finite request and run
   budgets plus the structured output caps and overflow policy.

2. **Preflight:** acquire one geometry dataset complete for the authorized
   question - exact layers and purposes, object classes, region, hierarchy, and
   needed neighboring evidence. A limited sample is not complete geometry for a
   placement or spacing question; report the missing scope instead of silently
   expanding a layer-only read. Create a backup only when authorized. Inventory
   protected labels and relevant connectivity separately, and only when that
   protection or readback scope is needed. Summarize geometry with counts,
   bounds, extrema, violations, and finite samples rather than defaulting to a
   full object dump.

3. **Edit:** calculate pure coordinates and parameters locally from the acquired
   data, then apply them through the existing OA API; never edit binary OA
   bytes. Write to the explicit target cellview rather than the currently active
   one unless that cellview has just been verified. Keep edits local and
   topology-preserving. Batch every deterministic change in an authorized stage
   or candidate into one guarded mutation request, and use finite parameterized
   functions or arrays instead of hand-coded repeated shapes or per-object
   calls. Validate counts, pitch, progress, and all pre-save assertions, and
   stop on the first error. Keep each batch within one profile, one exact view,
   one authorization, and one write domain.

4. **Postflight:** save at most once, and only when the accepted candidate and
   the save are authorized. Use one independent reopen or readback request only
   when it is in budget. Verify that changed shapes have the intended bounding
   boxes, points, layers, and grid alignment; that protected labels and text are
   unchanged; and that original connectivity and pad overlap still hold. Use the
   same confirmed adapter for postflight as for preflight.

5. **DRC, only when explicitly authorized:** start from rule names and
   coordinates in the report, group violations by rule, layer, hierarchy
   transform, and common geometric cause, and repair only the requested classes
   and iteration count. Preserve full totals and unfixed findings. Use the
   process-confirmed deck for the target; never reuse another process's rules.

6. **LVS, only when separately authorized:** first confirm the
   schematic-to-layout correspondence, the source netlist export, the rule deck,
   and the include or recognition file. Never use an include file as the circuit
   source netlist. Report whether virtual connect was disabled, configured, or
   proven active.

## Layout XL Binding And Cross-Probing

When schematic instances cross-highlight but custom layout routing does not,
separate stored OA connectivity from the active Layout XL Binder context before
changing geometry:

1. Bind the exact schematic, layout, and `physConfig` cellviews. Confirm that the
   editors were launched as one Layout XL pair rather than as an unrelated plain
   layout window. A correct connectivity reference or `physConfig` file does not
   prove that the current graphical session activated that context.
2. Read schematic and layout nets and the instance-terminal mappings, then count
   routed conductor and via figures with and without OA net ownership. Plain
   labels may legitimately have no net owner; clicking such text is not proof
   that the underlying conductor is unbound.
3. If the OA nets and routed figures are correct but cross-probing is
   incomplete, use the native command:

   ```text
   Connectivity -> Update -> Binding
   ```

4. In the binding form, enable extraction to the finite hierarchy depth the
   current design requires. A displayed default of zero must not be accepted
   silently when the required connectivity lies below the top level. Do not
   guess a depth, select an unlimited depth, or reuse a depth from another
   design; larger values expand extraction scope and runtime.
5. Do not replace this repair with a source regeneration, a new layout, or a
   replacement `physConfig`. Those can create or alter objects and need separate
   authorization. Treat binding update, save, and geometry repair as distinct
   gates.
6. Verify the chosen depth and test cross-highlighting in both directions for a
   representative schematic instance, an internal net, an actual routed metal
   figure, and a via where applicable. Report labels separately. A successful
   binding command does not prove that every hierarchy level or figure now
   cross-probes.

## Wire Assistant And Standard-Cell Placement

- Compute placement from each master cell's actual PR-boundary figure after
  applying the instance transform. Do not substitute the instance or master
  total bounding box.
- Derive row orientation and abutment from the selected cell family and its
  legal transforms. Verify transformed PR boundaries, rail shapes, net
  identity, and current process rules; boundary abutment does not mean
  flattening or merging.
- Before signal routing, freeze the user-selected Wire Assistant settings or an
  explicit preset. Loading or saving a preset only manages settings; it does not
  perform routing.
- Freeze each routable layer's direction policy independently. When the user
  permits either horizontal or vertical routing on every layer, use the form's
  explicit allow value for those layers and verify runtime wrong-way support. A
  nonzero wrong-way tax is a soft cost, not a direction prohibition. Runtime
  wrong-way flags, a disabled direction check, or mixed horizontal and vertical
  route lengths do not by themselves prove what the form or preset contained.
- Keep native implementation provenance separate from API support. A sourcing
  line in a log does not authorize a private dispatcher or a direct Tcl include,
  and a double-cut preference does not prove that every resulting via has two
  cuts.
- Freeze the live-marker policy before automatic routing. If the selected native
  flow clears annotations, it is incompatible with a hard requirement to retain
  existing live markers; an exported marker inventory is audit evidence and does
  not preserve those objects.
- For automatic routing, preserve a bounded vendor-log window and identify the
  main entry, topology branch, normal and specialty branches, routed net count,
  excluded power and ground nets, layer use, final comparable detailed-error
  count, opens, shorts, and the post-route effective cut-array histogram. A
  bridge call need not echo the literal callback into the vendor log; correlate
  the external exact call record with unique begin and end markers and the
  bounded native log.
- Bind automatic routing, internal repair, optimization, remaster, push, and
  save to separate net and object scopes. After any stage reports changed nets,
  earlier connectivity and geometry summaries are stale until they are rerun
  after the final mutation. A power exclusion in automatic routing does not
  prove that a later optimization used the same scope.

## SKILL Generation Patterns

Use these patterns as implementation ideas, not as process-agnostic drop-ins.
See [skil-coding-patterns.md](skil-coding-patterns.md) for coding hygiene.

- When the user supplies a via example, first read its exact via definition,
  overrides, orientation, landing layers, and target net intent. Prefer
  documented native copy and transform APIs over reconstructing its appearance.
  Read standard vias from the via collection, not only from the shape list. Do
  not carry a source net into a different target net, and validate that the
  target fits; an example is not a waiver.
- For simple repeated geometry, build a parameterized procedure around an array
  API with explicit layer, origin, width, pitch, rows, and columns.
- Avoid relying on the active-view accessor in unattended scripts unless the
  active layout window has been explicitly checked. Prefer opening the exact
  target cellview by library, cell, and view.
- For reusable generated geometry, consider a parameterized cell with explicit
  parameters. Validate that the target library exists before defining it, and
  use a unique project prefix for helper names to avoid collisions with system
  or process functions.
- For arrayed rectangles or via and contact arrays, compute the count and the
  centered start coordinates from process rule values and the available metal or
  contact enclosure, then read back the generated bounding boxes.
- Keep pin sets stable where possible. Variable pin counts require symbol and
  parameter regeneration and can break reuse, netlisting, or LVS expectations.
- For shared cells, do not default to user or effective parameter views, which
  may not be saved into the library for other users. Prefer the base definition
  when library permissions and project policy allow it, or create an explicit
  parameter export and load workflow.
- When generating schematic-side helpers, bind objects to nets and terminals
  intentionally. Do not draw disconnected graphics and assume that netlisting
  will infer the intent.
- Use the vendor's API documentation or API finder for exact signatures.
  Article and forum examples may be simplified or process-specific.
- Check file ports before writing logs or reports from a SKILL script; an empty
  port should stop the script with a clear error rather than failing later.

## Geometry Heuristics

- Optimize active layers before metals when the user asks for compact devices,
  unless connectivity or DRC evidence says otherwise.
- Choose metal width from the user's objective: widen within the confirmed
  spacing, width, and enclosure rules for a widening task; shrink only for an
  explicit compact-layout objective. A via-only task must not change the parent
  metal.
- Keep continuous gate metal independent of via-array generation. Place vias in
  the legal overlap after enclosure and spacing constraints; changing via rows
  or columns must not trim or rebuild protected metal. Check ring edits at
  corners, joins, gate leads, and the narrowest segments rather than only by
  area or bounding box. Local continuity evidence does not prove LVS.
- Wide-metal exemptions and exclusion layers are process, layer, purpose, rule,
  and region specific. Resolve their legal applicability and the remaining
  spacing, notch, and width constraints from the current deck before using them,
  and never apply one as a universal waiver. User acceptance of a violation does
  not remove it from the report or prove a clean result.
- When fixing acute or angle violations at route ends, prefer short chamfers,
  true 45-degree transitions, or small local caps over long detours.
- For hierarchy-boundary violations, dump parent and child geometry, transform
  child master coordinates by the instance origin and orientation, and compare
  endpoint and bounding-box differences. Sub-nanometer-scale mismatches can
  matter.
- For pad entry with 45-degree metal, entering the pad at a corner may avoid
  extra cap shapes. Check the real overlap and the requested geometry before
  accepting the change, and claim safety only from an authorized check.

For power-device area utilization, use an existing project planner to compare a
finite set of candidates before making edits. Include the actual transformed
cell and metal envelopes, the top-level boundary, fixed pad positions and
orientations, legal parameter ranges, and the gate-ring and row routing space
under the current width-dependent spacing. Circuit under a pad requires the
current pad and process allowance. Keep the user's optimization metric explicit
and report reproducible dimensions rather than a claim of global optimality.
Historical parameter values are not defaults, and schematic changes need their
own exact view authorization.

For reusable local absolute-field planning and finite measured regular-array
screening, read [local-layout-planning.md](local-layout-planning.md). It includes
offline-tested no-op and per-view partial-outcome handling; it is not an
installed live OA adapter. Reuse a capable current project planner first and do
not replace it merely to use this helper.
