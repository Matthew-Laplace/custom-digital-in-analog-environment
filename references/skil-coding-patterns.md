# SKILL Coding Patterns

Guidance for writing layout-generation SKILL scripts, adapted from public
articles and forum answers about automating Virtuoso layout and parameterized
cells. Treat every example as illustrative: article and forum code is often
simplified, dated, or specific to one process.

## Why Script At All

Use SKILL for repetitive layout work instead of manual repeated drawing. A
typical example is a via or contact array built by a procedure that takes the
layer, origin, pitch, via size, rows, and columns as explicit parameters.

## Target Binding

An accessor such as `deGetCellView()` depends on an already-open and intended
layout cellview. In unattended automation, prefer opening the explicit target by
library, cell, and view, or verify the current cellview first. Do not build a
script whose correctness depends on whichever window happens to be focused.

## Repetition

For repeated via, contact, or rectangle arrays, compute the dimensions from
process rule values and parameters, then create arrayed shapes through the
database array API or the corresponding ROD array call. Prefer a finite
parameterized procedure over hand-written repeated shapes.

Guard every count and pitch: derive the element count before the call, require a
positive pitch, and stop on the first error rather than looping until success.

## Reusable Generators

For reusable layout generators, a parameterized cell can be defined with
explicit default parameters and a body wrapped in a local binding form. Validate
that the library object exists before defining the cell, and use a unique
project prefix for helper names to avoid collisions with system or process
functions.

Article examples typically hard-code layer names and rule numbers. Replace those
with the active process rule deck and user-confirmed layer and purpose values;
do not import example values blindly.

## Parameters And CDF

Parameter definitions matter for schematic cells and callable parameters. If a
cell needs schematic reuse, define stable parameters and keep pin sets stable
where possible. For shared cells, do not default to user or effective parameter
views, which may not be saved into the library for other users; prefer the base
definition where policy allows, or add an explicit export and load step.

A generated schematic cell with a variable pin count requires that symbol
generation, parameters, netlisting, and LVS expectations be reconsidered
together. Stable symbol pins are safer for reused generators.

## Connectivity, Not Just Graphics

Schematic-side generators use object-level connectivity operations to create
nets, terminals, and instance terminals and to bind figures to nets. The
transferable lesson for layout is the same: create objects and attach them to
nets intentionally rather than drawing disconnected graphics and assuming that a
later netlister will infer the intent.

## Hygiene

- Define procedures clearly and avoid accidental global state.
- Use complete file paths for file input and output, and check the returned
  port before writing. A `nil` port should stop the script with a clear error.
- Close ports when done.
- Prefer readable coordinate helpers over deeply nested list accessors.
- Check every database object returned by library, cellview, technology-file,
  and terminal lookups before passing it into a later drawing call. A common
  failure mode is a later error stating that an argument should be a database
  object but is `nil`.
- Treat load failures as important evidence: depending on statement order, a
  failed load can leave a partially completed operation behind. Keep
  database-changing code behind explicit procedure calls.

## What Not To Copy From Examples

- Do not adopt example layer names or numeric minimum rules into another process
  without confirming them against that process's own rules.
- Do not make GUI-only steps the default automation path. Prefer the command or
  API channel and verify the log.
- Do not create database-changing startup or save hooks merely because an
  example loads a script from a session file.
- Do not treat forum and question pages as clean sources; they mix several
  answers, comments, and recommendations of varying quality.
- Do not assume that a duplicated example is independent confirmation of a
  technique.

## Practical Pattern

1. Turn repeated manual drawing into a small parameterized procedure or cell.
2. Pass every process-sensitive value explicitly: layer, purpose, width, pitch,
   enclosure, row and column count, and target library, cell, and view.
3. Guard the target: the library exists, the target cellview is explicit, and
   the write mode is intentional.
4. Generate the geometry.
5. Save only when intended.
6. Read back bounding boxes, points, layers and purposes, labels, and
   connectivity.
7. Run the process-confirmed DRC flow before accepting the result.
