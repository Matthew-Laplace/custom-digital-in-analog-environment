# Local Layout Planning

Use [scripts/layout_plan.py](../scripts/layout_plan.py) only when the current
project lacks the corresponding small pure calculation. It has no command-line
interface and no database, filesystem, or network access. Do not replace a
working project planner with it, and do not use it to edit binary database
files.

## Absolute Edits And Per-View Outcomes

`Edit(selector, before, after)` contains only the explicitly changed fields.
Supply absolute coordinates and parameters in the current process grid, not a
relative displacement to be replayed. The selector is the current project's
object locator, never a serialized database handle.

`plan_view(edits, matches)` requires one object per selector and compares only
the named fields. It returns the pending edits when all changed objects remain
at their expected state, no edits when all already match the target, and rejects
zero or multiple matches, unexpected fields, or a mixed before-and-target state.
Extra observed fields are neither copied nor rewritten.

`apply_views` accepts a finite, dependency-ordered list of exact
`library/cell/view` targets and project-owned callbacks:

- `read_matches(view, edits)` resolves the current selected fields.
- `apply_batch(view, pending)` must re-resolve and guard those same fields
  inside one bounded request, then apply only absolute targets.
- `save_view(view)` is optional and supplied only when saving is authorized.
- `readback_view(view, edits)` is optional and independently reads the saved
  target. It cannot be used without the save callback.

Write callbacks return the literal `True` only after their actual operation
success is established. A timeout, ambiguous reply, or partial error must raise
or return a non-true result, never a truthy response object. The helper stops at
the first failure, preserves completed earlier views, leaves later views not
run, and never retries, restores, or saves after an ambiguous apply. It returns
apply, save, and readback state per view, not a global transaction result. A
no-op does not claim a new save or a persisted readback. Keyboard interruption
raises `PlanInterrupted` with the partial outcomes attached; report them and
preserve the interruption rather than retrying. View and candidate inputs must
be finite sequences; unbounded iterators are rejected without consumption.

The caller still owns profile confirmation, exact identity, leases, protected
objects, authorization, and native API correctness. A fresh per-view check is
required after saving a changed child that affects its parent. No callback
adapter is bundled: the tests use only in-memory callbacks. Do not wire this to
a live session until an authorized project task supplies its actual API
contract.

## Finite Power-Device Candidates

`evaluate_power_candidates` filters an explicitly finite list of measured
`PowerCandidate` records. Coordinates and dimensions use integer process-grid
units. Convert authoritative measurements exactly; do not silently round. The
helper reports extent, count, the caller-selected score, and rejection reasons,
then ranks accepted candidates by that explicit score.

Inputs must include:

- the actual top-level boundary, origin, and transformed full device, metal, and
  ring envelope for each measured parameter combination. One candidate is a
  regular array of one resolved orientation; arbitrary packing and alternating
  transforms require a real project planner, not bounding-box guesses;
- a finite set of legal measured parameter pairs and the user's choice among
  them. There is no fitted size law and no historical default;
- the minimum X and Y pitch already resolved from the relevant conductor and
  device geometry, gate routing width, wide-metal spacing, and intended ring
  joining, with the exact current evidence named in the pitch record;
- fixed object positions and orientations before and after, the current
  under-pad policy source, and process-spaced keepouts for all prohibited
  regions. An empty keepout list is appropriate only when current evidence
  establishes no exclusions, and pad permission cannot be inferred from a
  marker;
- a positive finite instance-count bound and an explicit positive per-device
  score under the user's metric. Do not assume that an area product, a bounding
  box, or a device count is the intended electrical objective.

The footprint may exceed the legal pitch when adjacent same-net rings merge. Do
not impose total-bounding-box non-overlap in that case; resolve conductor
spacing and the ring union in the minimum pitch first. Conversely, entering a
small pitch and an arbitrary evidence string does not prove that merging is
legal. The helper verifies the numeric inputs, boundary, and keepout
relationships; it does not verify source provenance, polygons, gate continuity,
holes, interlayer vias, arbitrary hierarchy transforms, or process rules.

Rejected examples covered by the offline tests include odd parameter counts,
unmeasured parameters, nonpositive or insufficient pitch, boundary overflow,
moved or rotated fixed objects, forbidden under-pad overlap, and oversized
instance loops. Accepted candidates are local geometric proposals, not
DRC-clean, LVS-clean, or globally optimal layouts. Final database generation and
any requested verification remain separate authorized operations.
