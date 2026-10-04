"""Pure planning helpers. No OA, bridge, filesystem, process, or network access."""

from dataclasses import dataclass
from collections.abc import Sequence
from typing import Mapping


@dataclass(frozen=True)
class Edit:
    selector: str
    before: Mapping
    after: Mapping


class PlanInterrupted(KeyboardInterrupt):
    def __init__(self, outcomes):
        super().__init__("layout plan interrupted; inspect per-view outcomes")
        self.outcomes = outcomes


def plan_view(edits: tuple[Edit, ...], matches: Mapping[str, list[Mapping]]) -> tuple[Edit, ...]:
    """Compare absolute fields; the caller must re-resolve selectors inside OA."""
    if len({edit.selector for edit in edits}) != len(edits):
        raise ValueError("duplicate object selector")
    pending, reached = [], []
    for edit in edits:
        if not edit.before or edit.before.keys() != edit.after.keys():
            raise ValueError("before and after must name the same nonempty field set")
        objects = matches.get(edit.selector, [])
        if len(objects) != 1:
            raise ValueError("zero or multiple matches: " + edit.selector)
        current = objects[0]
        if not edit.before.keys() <= current.keys():
            raise ValueError("missing observed fields: " + edit.selector)
        state = {key: current[key] for key in edit.before}
        if state == edit.after:
            if edit.before != edit.after:
                reached.append(edit)
        elif state == edit.before:
            pending.append(edit)
        else:
            raise ValueError("unexpected object state: " + edit.selector)
    if pending and reached:
        raise ValueError("mixed before/target state; reconcile this view before applying")
    return tuple(pending)


def apply_views(view_edits, read_matches, apply_batch, save_view=None, readback_view=None):
    """Sequential adapter callbacks; preserve partial outcomes, never retry.

    This is not a live OA adapter. Callers own authorization, identity, leases,
    remote atomic guards, error detection and field-limited absolute updates.
    readback_view must independently verify the persisted target, not echo it.
    """
    if not isinstance(view_edits, Sequence):
        raise ValueError("finite view sequence required; generators are not consumed")
    view_edits = tuple(view_edits)
    if readback_view is not None and save_view is None:
        raise ValueError("persisted readback callback requires an authorized save callback")
    views = [view for view, _ in view_edits]
    if len(set(views)) != len(views) or any(len(view.split("/")) != 3 or not all(view.split("/")) for view in views):
        raise ValueError("unique exact library/cell/view targets required")
    outcomes = {view: {"apply": "not-run", "save": "not-run", "readback": "not-run"} for view in views}
    for view, edits in view_edits:
        stage = "preflight"
        try:
            pending = plan_view(edits, read_matches(view, edits))
            if not pending:
                outcomes[view]["apply"] = "no-op"
                continue
            stage = "apply"
            outcomes[view][stage] = "outcome-unknown"
            if apply_batch(view, pending) is not True:
                raise ValueError("apply callback did not establish success")
            outcomes[view][stage] = "completed"
            if save_view is None:
                continue
            stage = "save"
            outcomes[view][stage] = "outcome-unknown"
            if save_view(view) is not True:
                raise ValueError("save callback did not establish success")
            outcomes[view][stage] = "completed"
            if readback_view is None:
                continue
            stage = "readback"
            outcomes[view][stage] = "outcome-unknown"
            if readback_view(view, edits) is not True:
                raise ValueError("persisted target readback not established")
            outcomes[view][stage] = "verified"
        except KeyboardInterrupt as exc:
            outcomes[view]["error"] = f"{stage}: KeyboardInterrupt"
            raise PlanInterrupted(outcomes) from exc
        except Exception as exc:
            outcomes[view]["error"] = f"{stage}: {type(exc).__name__}: {exc}"
            break
    return outcomes


@dataclass(frozen=True)
class Rect:
    x0: int
    y0: int
    x1: int
    y1: int

    def __post_init__(self):
        if any(type(value) is not int for value in (self.x0, self.y0, self.x1, self.y1)):
            raise ValueError("coordinates must be integer process-grid units")
        if self.x1 <= self.x0 or self.y1 <= self.y0:
            raise ValueError("rectangle must have positive area")

    def shifted(self, dx, dy):
        return Rect(self.x0 + dx, self.y0 + dy, self.x1 + dx, self.y1 + dy)

    def contains(self, other):
        return self.x0 <= other.x0 and self.y0 <= other.y0 and self.x1 >= other.x1 and self.y1 >= other.y1

    def overlaps(self, other):
        return self.x0 < other.x1 and other.x0 < self.x1 and self.y0 < other.y1 and other.y0 < self.y1


@dataclass(frozen=True)
class PowerCandidate:
    name: str
    ng: int
    w: int
    rows: int
    columns: int
    origin: tuple[int, int]
    pitch_x: int
    pitch_y: int
    # Full transformed footprint, including ring and all protruding metal.
    envelope: Rect
    # Resolved from current layer geometry, ring width and width-dependent rules.
    min_pitch_x: int
    min_pitch_y: int
    pitch_evidence: str
    # User-selected metric for one device, not an assumed ng*w formula.
    score_per_device: int


def evaluate_power_candidates(candidates, *, boundary: Rect, legal_parameters,
                              fixed_before: Mapping, fixed_after: Mapping,
                              keepouts: tuple[Rect, ...], pad_policy: str,
                              even_ng: bool, max_instances: int):
    """Filter finite measured regular arrays, not arbitrary packing or DRC.

    Keepouts include process-spaced PAD/device exclusions. pad_policy names the
    current under-PAD allowance and its source, including an explicit no-PAD
    case. It is provenance, not proof that a foundry permits circuit under PAD.
    """
    if fixed_before != fixed_after:
        raise ValueError("fixed object positions/orientations changed")
    if not pad_policy.strip() or type(max_instances) is not int or max_instances <= 0:
        raise ValueError("resolved PAD policy and positive finite instance bound required")
    if not isinstance(candidates, Sequence):
        raise ValueError("finite candidate sequence required; generators are not consumed")
    candidates = tuple(candidates)
    if len({item.name for item in candidates}) != len(candidates):
        raise ValueError("duplicate candidate name")
    results = []
    for item in candidates:
        reasons = []
        numbers = (item.ng, item.w, item.rows, item.columns, item.pitch_x, item.pitch_y,
                   item.min_pitch_x, item.min_pitch_y, item.score_per_device)
        if any(type(value) is not int or value <= 0 for value in numbers):
            reasons.append("nonpositive-or-off-grid-parameter")
        if not isinstance(item.origin, (tuple, list)) or len(item.origin) != 2 or any(type(value) is not int for value in item.origin):
            reasons.append("invalid-origin")
        if reasons:
            results.append({"candidate": item.name, "accepted": False, "reasons": reasons,
                            "extent": None, "device_count": None, "score": None})
            continue
        if even_ng and item.ng % 2:
            reasons.append("odd-ng")
        if (item.ng, item.w) not in legal_parameters:
            reasons.append("unmeasured-or-illegal-parameters")
        if not isinstance(item.pitch_evidence, str) or not item.pitch_evidence.strip():
            reasons.append("unresolved-ring-and-spacing")
        if item.pitch_x < item.min_pitch_x or item.pitch_y < item.min_pitch_y:
            reasons.append("insufficient-routing-or-spacing-pitch")
        count = item.rows * item.columns
        if count > max_instances:
            reasons.append("instance-budget-exceeded")
        extent = None
        if not reasons:
            x, y = item.origin
            extent = Rect(item.envelope.x0 + x, item.envelope.y0 + y,
                          item.envelope.x1 + x + (item.columns - 1) * item.pitch_x,
                          item.envelope.y1 + y + (item.rows - 1) * item.pitch_y)
            if not boundary.contains(extent):
                reasons.append("outside-PRBoundary")
            else:
                # Bounded by max_instances; never allocate the full OA geometry.
                for row in range(item.rows):
                    for column in range(item.columns):
                        placed = item.envelope.shifted(x + column * item.pitch_x, y + row * item.pitch_y)
                        if any(placed.overlaps(keepout) for keepout in keepouts):
                            reasons.append("PAD-or-device-keepout")
                            break
                    if reasons:
                        break
        results.append({"candidate": item.name, "accepted": not reasons,
                        "reasons": reasons, "extent": extent, "device_count": count,
                        "score": count * item.score_per_device if not reasons else None})
    return sorted(results, key=lambda row: (not row["accepted"], -(row["score"] or 0), row["candidate"]))
