# Virtuoso Standard-Cell Layout

An agent skill for taking a Cadence Virtuoso standard-cell or custom-digital
block from an empty artifact set to an accepted, well-evidenced route.

Standard-cell automation usually fails in the same places: a layout is created
without a working `physConfig`, cells are placed against the wrong boundary
figure, supply rails are assumed to be connected, routing is called a success
because the completion percentage reads 100, or a double-cut request is treated
as a guarantee. This skill is built around those failure points.

```text
Stage order      artifact set -> placement -> M1 supply tracks -> route
                 feedback -> signal routing -> tap/DRC -> LVS interpretation

Evidence layers  command-completed -> connectivity-closed
                 -> detailed-geometry-closed -> via-contract-closed
                 -> saved-readback-closed
```

Each arrow is a gate, not a formality. A later stage never repairs an earlier
missing gate, and a passing result in one layer never stands in for another.

## What It Covers

- **Artifact establishment.** Separate layout creation, `physConfig` creation,
  source generation, config and connectivity reference assignment, active
  binder update, and cross-probe verification. A successful Layout XL launch
  does not prove that any of the later states exist.
- **Placement from real boundaries.** PR-boundary figures rather than instance
  or master bounding boxes; legal transform sets read back from the library
  instead of assumed; protected groups translated as rigid bodies.
- **Joint placement and equivalent-pin search.** Legal left-right mirroring,
  three-terminal shared-tree topology, linear chain clustering, and explicit
  fixed endpoints, all scored as whole-net cost rather than pairwise distance.
- **Occupancy policy.** Single-height default, decoupling-capacitor-first exact
  integer-site cover, narrow residual gaps closed only by legal filler, and an
  explicit multi-height escape hatch that must be enabled per transaction.
- **Supply tracks.** Uniform-length M1 power and ground tracks sized from the
  routing footprint, with the two outside boundary rails required to be
  ground and to physically contact the cell rails.
- **Route acceptance.** The ordered evidence vector above, plus a strict
  effective via-array gate read from the database rather than from the router's
  own summary.
- **Tap insertion.** Latch-up spacing confirmed per process, converted into a
  finite per-row count with edge intervals, and validated against the target's
  own DRC when that run is authorized.
- **Write safety.** Single-writer leases, bounded request budgets, batching,
  and one bounded reconciliation instead of blind retries after an ambiguous
  return.

## Layout

```
SKILL.md                                entry point, stage order, gates
README.md                               this file
ATTRIBUTION.md                          sources and evidence levels
LICENSE                                 MIT
agents/openai.yaml                      skill interface metadata
references/
  bounded-operation-contract.md         ownership, leases, budgets, evidence
  geometry-execution.md                 OA edit mechanics, binding, heuristics
  wire-assistant-routing.md             Route APIs, via and push semantics
  local-layout-planning.md              offline planning helpers
  skil-coding-patterns.md               SKILL coding hygiene
scripts/
  layout_plan.py                        pure planning helpers
  test_layout_plan.py                   their tests
```

## Installing As A Skill

Copy the directory into your agent's skill folder, for example:

```bash
cp -R virtuoso-standard-cell-layout ~/.codex/skills/virtuoso-standard-cell-layout
```

The skill is plain Markdown plus two standard-library Python files. There is
nothing to build and no dependency to install. Run the included tests with:

```bash
python3 scripts/test_layout_plan.py
```

## Honest Limits

- This skill **does not** run DRC, LVS, extraction, or signoff, and it does not
  ship a rule deck. It prepares a candidate and interprets results produced by
  a separately bound verification flow using the current process rules.
- It does **not** ship a live layout adapter. The bundled Python is pure
  calculation with no database, filesystem, or network access; the callbacks
  that reach a real session are supplied by your own project.
- Route API names and semantics recorded here were read from a specific
  installation generation. Vendor documentation and installed symbols vary by
  release; confirm the exact signature against your own version before use.
- A geometric cost such as half-perimeter wire length or minimum spanning tree
  length is a **placement proxy**. It is not evidence of shorter routed metal,
  and no claim of routed-length improvement should be made from it alone.
- Numeric values that appear in the worked patterns are examples of the
  confirmation procedure, not portable defaults. Process rules, layer names,
  legal masters, and legal orientations all come from the design in front of
  you.

## Non-Negotiable Rules

1. **One writer.** A live session has exactly one geometry writer. Readers wait
   until the mutation is quiescent, and the lease is released before control
   returns to the user.
2. **Do not save a rejected candidate.** A candidate that fails connectivity,
   detailed geometry, or a hard via contract stays explicitly live and unsaved,
   with the last accepted disk state preserved.
3. **Do not retry an ambiguous mutation.** A timeout or ambiguous return is an
   unknown outcome. Perform at most one bounded reconciliation and never
   blind-retry, save, or clean up first.
4. **Preserve protected objects.** Text, labels, pin figures, existing routes,
   power geometry, and terminal-to-net mapping are protected unless the exact
   object is in the authorized write set.
5. **A request is not a guarantee.** Asking the router for double-cut vias,
   maximum rules, or a push pass does not prove that any of them happened.
   Read the database back and require the exact contract.

## Scope Note

This is a working engineering skill, not a specification. Some rules describe
practices confirmed against a particular tool generation, and a few encode
lessons from real failure modes. Where a rule depends on a process, a library,
or a site convention, it says so; do not universalize a local convention into a
portable one.

## Licence

MIT - see `LICENSE`. Public sources consulted are listed in `ATTRIBUTION.md`.
No third-party or vendor documentation is redistributed in this repository.
