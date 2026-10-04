# Bounded Layout Operation Contract

Use this contract for any operation that reads or writes a live layout database.
It keeps reads, geometry writes, persistence, and physical verification as
separate evidence gates.

## Ownership

- The stage-planning role owns candidate planning, stage order, budgets, and
  route-acceptance decisions. It does not hold a geometry write lease.
- The geometry role owns geometry-complete-within-scope preflight and postflight
  and is the only role that may execute an authorized geometry mutation or save.
- An electrical or connectivity snapshot reader owns one-request, getter-only
  acquisition of electrical or display state. It does not provide arbitrary
  placement, route, via, or full-shape geometry.
- A verification runner owns the generic check contract, source gating,
  normalized result states, violation classification, and the final report. It
  does not choose the process rule, repair geometry, or save the database.

One task never holds more than one of these roles against the same live session
at the same time.

## Freeze The Contract

For a live write or a new verification run, use the applicable fields below and
update only the fields that changed during a valid continuous task. A simple
read-only request needs only its exact target, authorized scope, session
identity when required, and actual output limits; do not force a full template
or unrelated verification gates onto it. Never infer a missing identity or
authorization from the active window, an environment default, or a previous
task.

```yaml
request:
  owner_task: <current task identity>
  operation: <read | mutate | save | check | signoff | repair>
  exact_targets: [<library/cell/view or run artifact>]
  requested_result: <literal deliverable>
rule_plan:
  - rule: <geometry-driving rule or user constraint>
    source: <authoritative current source>
    applies_to: <TOP | CELL | BOTH>
    exact_targets: [<exact library/cell/view>]
    state: <resolved | unresolved | not-applicable>
authorization:
  profile: <confirmed named profile or not-applicable>
  process_pdk: <confirmed identity or not-applicable>
  readable_objects: [<bounded classes>]
  writable_objects: [<exact classes or objects>]
  backup: <yes | no | unresolved>
  save: <yes | no | unresolved>
  postflight: <yes | no | unresolved>
  check_drc: <yes | no>
  check_lvs: <yes | no>
  repair: <yes | no>
verification_vector:
  - gate: <SAVE | READBACK | DRC | LVS | DENSITY_CHECK | DENSITY_REPAIR>
    claim: <exact completion claim>
    target: <exact view or artifact>
    method: <readback, check, or authorized run>
    state: <required | optional | not-run>
    on_fail: <stop condition>
budgets:
  candidates: <finite count>
  read_requests: <finite count>
  mutation_requests: <finite count>
  saves: <finite count>
  verification_runs: <finite count>
  output:
    mode: <summary | bounded-records | authorized-artifact>
    max_records: <finite positive integer>
    max_samples: <finite nonnegative integer>
    max_bytes: <finite positive integer | producer-not-enforced>
    overflow: <aggregate | stop | authorized-artifact>
```

`TOP` means only the named hierarchy root, `CELL` means only the explicitly
named child or master cellviews, and `BOTH` requires both sets to be checked.
Applicability never expands the writable object list.

For a mutation or geometry repair, every geometry-driving rule must be resolved
from authoritative current evidence before dispatch. A missing source,
applicability, value, or exact target blocks drawing. Read-only and verification
operations may record the rule plan as not applicable; do not force drawing
rules into those workflows.

For a mutation or repair, record all six verification gates explicitly. A
read-only request does not need gates unrelated to its deliverable. The density
check is the rule-domain execution and report gate; density repair is a separate
mutation objective. Marking repair not run never disables or filters an enabled
density check. A required gate needs an exact method and a failure stop; an
optional or not-run gate does not authorize execution.

Saving, DRC, LVS, repair, GUI inspection, simulation, extraction, cleanup, and
signoff are independent operations. Authorizing or configuring one never
authorizes another. A deck, preset, or profile confirmation binds an input; it
does not authorize execution.

## Continuous Session Lease

For each live session, bind:

```text
owner_task | mode(read|write|verification-run) | profile | host | workdir |
port | session identity | release/PDK | exact views | writable objects |
writer(user|agent|none) | acquired marker | invalidators
```

- Only the root task may own the write lease. Do not run another reader or
  writer against the same session while a mutation is in flight.
- A snapshot reader may hold only a read lease, after the writer is quiescent.
- A verification runner owns an exclusive fresh run directory, not a write
  lease.
- Invalidate the lease on profile, target, host, workdir, port, session or PDK
  drift; unexpected dirty state; external target changes; timeout; abort or
  interruption; transport loss; or evidence of another writer. Rebind identity
  and authority before continuing.

Only one of the human user and the agent may be the writer. Before the agent
yields control, prove that no request is in flight, report the live dirty, save,
and outcome state, and release the lease. A user edit invalidates the prior
agent lease and geometry snapshot. A statement that editing is finished
expresses handback intent, not database state evidence; reacquire only after
exact identity, dirty-state, and one fresh bounded preflight readback. If either
writer may still be active, dispatch nothing.

### Verification Input Acceptance

Apply this distinction independently to every schematic or layout input before a
new export or verification run; it does not apply to reading an old report.

- With a preceding write transaction, retain the exact writer, the released
  write lease, the saved-clean readback, the release marker, and the
  invalidators.
- With no preceding write transaction in this task, do not invent a writer or a
  release marker. The existing read or verification path may use a `none` writer
  only when current evidence establishes exact view and session identity, a
  saved-clean state, no in-flight or unresolved writer, and compatible adapter
  behavior. Mark only the nonexistent writer and release fields as not
  applicable; view identity, saved-clean readback, and invalidators remain
  required.
- Unknown writer state is not `none`. Dirty state, active or unresolved writes,
  an unknown outcome, or drift blocks the dependent export or run. Missing
  evidence is not permission to save, to release someone else's lease, or to
  manufacture a handoff. Required profile and process confirmation are
  unchanged.

Before accepting the no-preceding-writer path, establish whether the selected
exporter consumes saved data or live memory, and whether its environment, hooks,
or templates can save implicitly. An independent shell invocation, the absence
of a literal save call, or a configuration pass does not prove those properties.
Without applicable adapter evidence, report the export or run as
preflight-blocked and name the missing evidence. This reference is a protocol,
not a claim of live adapter validation, and it never authorizes a save.

## Minimize Round Trips

1. Read a fresh, directly accessible netlist when it fully answers the question.
2. Otherwise acquire each authorized dataset once and filter or calculate
   locally. Do not requery the database per instance, net, rule, or filter miss.
3. Full placement, route, via, PR-boundary, and arbitrary-shape preflight
   belongs to the geometry role. Return counts, bounds, minima and maxima,
   violation coordinates, and finite representative samples instead of dumping
   every object by default.
4. Within each authorized stage or isolated candidate, batch deterministic
   object changes for one exact view into one guarded mutation request. Keep
   logically separate tools and authorization gates separate, but never degrade
   a batch into per-object calls or saves.
5. If saving is authorized, save at most once after all pre-save assertions for
   that accepted candidate pass. Use one independent postflight request only
   when it is in budget.
6. Every loop or generated array must have a finite count derived before entry,
   validate positive pitch and progress, and stop on the first error. No retry
   loop may mutate until success.

A bulk request is not a cross-view atomic transaction. Apply dependent views
separately and report each view's applied, saved, and readback state if a later
view fails. Re-identify objects in the target view; database handles are not
durable cross-process identifiers. Reject zero or multiple matches. Prefer
absolute target coordinates and parameters: the original state permits
applying, the target state returns without another move, and any other state
stops. This does not permit replaying an unknown-outcome request; reconcile it
under the rule below first.

Geometry scope includes layers, purposes, classes, region, and finite hierarchy.
Filter at the producer where supported; labels, vias, terminals, and instances
must not bypass an explicit layer or class filter. State unsupported filters and
truncation instead of claiming that a sample answers a complete geometric
question.

The target list and request count can be bounded while response bytes, producer
execution, and memory have different guarantees. Record each producer's actual
limits instead of promoting one cap into another. Some snapshot exporters
hard-cap appended records, accepted contract bytes, and retained standard output
and error; they still do not hard-cap object-window scans, getter runtime,
process memory, nesting depth, or remote cancellation. For any producer without
explicitly enforced record or byte caps, report the contract as bounded but the
payload as not hard-bounded, and never treat a cooperative timeout or target cap
as a hard execution or memory limit.

## Unknown Outcome

If a dispatched operation times out, is aborted, loses transport, or returns
without a trustworthy terminal result, mark the outcome unknown and invalidate
its lease. Do not automatically retry, save, restore, clean up, or dispatch the
next operation.

Perform at most one separately bounded reconciliation:

- For a database mutation, establish that the previous request is no longer in
  flight, then compare the exact target identity, dirty state, protected-object
  readback, save marker, and accepted disk identity as applicable.
- For a checker run, inspect only the exact process or job identity, the run
  directory, the terminal marker, and the expected artifact identities.

If reconciliation cannot prove one terminal state, remain blocked on the
unknown outcome. A timeout is not a deterministic failure signature and never
qualifies for a signature-matched retry.

## Evidence States

Report each applicable gate actually proved, and list every requested or
relevant missing gate as not run, blocked, or failed:

```text
planned -> preflight-checked -> live-unsaved-candidate -> saved ->
oa-readback-checked
DRC: independently not-run | blocked | checked (include result)
LVS: independently not-run | blocked | checked (include result)
signoff: separate authorized scope and qualification evidence
```

The persistence sequence applies to edits, not as a demand to mutate or save
before inspecting existing reports. DRC is not an LVS prerequisite and LVS is
not a DRC prerequisite; each new run follows its own input and source gate.

Route quality is orthogonal to persistence. Command completion, router
completion, connectivity closure, detailed-geometry closure, a via contract,
save success, DRC, and LVS are separate facts. Never use a later-looking label to
fill an earlier missing gate.
