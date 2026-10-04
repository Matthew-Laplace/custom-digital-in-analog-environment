# Attribution

## Origin Of This Skill

This skill consolidates two working agent skills that were developed while
operating Cadence Virtuoso on real standard-cell and custom-digital blocks:

- `virtuoso-standard-cell-layout-flow` - stage order, placement policy, route
  acceptance, tap contract, and completion gates.
- `virtuoso-layout-drawing` - geometry-write mechanics, Layout XL binding,
  SKILL generation patterns, and geometry heuristics.

The consolidation kept the portable engineering content and removed every
project, site, host, process, and library identity that the originals carried.
The bounded operation contract, the write-safety rules, the Route API notes,
and the pure planning helpers were rewritten for general use. No project data,
design data, foundry documentation, or vendor rule deck is redistributed here.

## What Was Learned From Operating The Tool

The Route API map, the double-cut and push semantics, the direct-pin-access
classification, the marker lifecycle rules, the count taxonomy, and the
documented-defect list in
[references/wire-assistant-routing.md](references/wire-assistant-routing.md)
come from reading the installed vendor reference material and the tool's own
context files for one IC618 generation, together with observed behavior in
that environment.

Vendor documentation and installed symbols are **not** redistributed in this
repository. What is published is a summary of behavior and a set of procedural
rules, written in the author's own words, with release-dependent identifiers
replaced by placeholders such as `<cadence_install>/IC618/...`.

| Topic | How it is evidenced |
|---|---|
| `rte*` Route API names, power-routing families, scheme constructors, preset APIs | Read in the installed release's own reference material and context metadata |
| `t` return semantics and the `rteCheckDataForRouting` exception | Read in the installed reference material |
| `rteAutoRoutes` being installed-only and undocumented | Established by comparing the installed context file against the installed reference material |
| Double-cut, max-rule, remaster, and push behavior | Combination of vendor documentation statements and observed runtime behavior |
| Direct pin access classification | Derived from the database model: terminal ownership, transformed pin figure, and via definition metal layers |
| Documentation defects list | Observed disagreement between published examples and the installed build |

Every one of these is release-dependent. Confirm the exact signature and
behavior against your own installation before relying on it.

## Public Sources Consulted

The coding-hygiene guidance in
[references/skil-coding-patterns.md](references/skil-coding-patterns.md) and
part of the generation patterns in
[references/geometry-execution.md](references/geometry-execution.md) were
informed by publicly readable Chinese-language articles and forum answers about
automating Virtuoso layout with SKILL, including:

- a Zhihu column article on automating layout drawing with SKILL scripts;
- a Zhihu column article on creating parameterized cells with SKILL;
- a Zhihu question thread on learning SKILL systematically, specifically its
  answers on parameter definitions, API reference usage, and connection APIs.

Those sources are working notes of varying quality, published on a
user-generated platform. They are treated here as **illustrative only**: their
layer names, numeric rules, and code fragments are process-specific and are
explicitly not adopted. What was carried over is general coding hygiene -
checking returned database objects, avoiding dependence on the active window,
declaring array parameters explicitly, and treating a failed load as possible
partial state.

No source code from those articles is reproduced in this repository.

## Scope Of The Licence

This repository is MIT licensed - see [LICENSE](LICENSE).

The licence covers the text and the Python helpers in this repository. It does
not grant any right to Cadence software, vendor PDKs, foundry design rules, or
any third-party documentation. Reading about a vendor API here does not make
that API available to you; you still need your own licensed installation.
