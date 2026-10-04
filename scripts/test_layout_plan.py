"""Synthetic integer-grid tests; no imports of Cadence or remote interfaces."""

from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from layout_plan import Edit, PlanInterrupted, PowerCandidate, Rect, apply_views, evaluate_power_candidates, plan_view


EDIT = Edit("gate", {"xy": (0, 0)}, {"xy": (10, 0)})


class AbsolutePlanTests(unittest.TestCase):
    def test_expected_state_plans_absolute_target_without_unrelated_fields(self):
        objects = {"gate": [{"xy": (0, 0), "label": "preserve"}]}
        self.assertEqual(plan_view((EDIT,), objects), (EDIT,))
        self.assertEqual(objects["gate"][0]["label"], "preserve")

    def test_repeated_target_is_noop_not_relative_move(self):
        self.assertEqual(plan_view((EDIT,), {"gate": [{"xy": (10, 0)}]}), ())

    def test_wrong_state_and_zero_or_multiple_matches_stop(self):
        for objects in ({}, {"gate": []}, {"gate": [{"xy": (3, 0)}]},
                        {"gate": [{"xy": (0, 0)}, {"xy": (0, 0)}]}):
            with self.assertRaises(ValueError):
                plan_view((EDIT,), objects)

    def test_mixed_state_requires_reconciliation(self):
        with self.assertRaisesRegex(ValueError, "mixed"):
            plan_view((EDIT, replace(EDIT, selector="other")),
                      {"gate": [{"xy": (10, 0)}], "other": [{"xy": (0, 0)}]})

    def test_missing_fields_and_duplicate_selectors_stop(self):
        with self.assertRaises(ValueError):
            plan_view((EDIT,), {"gate": [{}]})
        with self.assertRaises(ValueError):
            plan_view((EDIT, EDIT), {"gate": [{"xy": (0, 0)}]})

    def test_second_view_preflight_failure_preserves_first_saved_result(self):
        called = []
        def read(view, edits):
            if view == "L/top/layout":
                raise ValueError("user changed top")
            return {"gate": [{"xy": (0, 0)}]}
        def record(view, *args):
            called.append(view)
            return True
        result = apply_views([("L/child/layout", (EDIT,)), ("L/top/layout", (EDIT,))],
                             read, record, record, record)
        self.assertEqual(result["L/child/layout"], {"apply": "completed", "save": "completed", "readback": "verified"})
        self.assertEqual(result["L/top/layout"]["apply"], "not-run")
        self.assertEqual(called, ["L/child/layout"] * 3)

    def test_timeout_stops_before_save_or_next_view(self):
        calls = []
        def apply(*args):
            raise TimeoutError("unknown remote outcome")
        def later(*args):
            calls.append(args)
            return True
        result = apply_views([("L/child/layout", (EDIT,)), ("L/top/layout", (EDIT,))],
                             lambda *args: {"gate": [{"xy": (0, 0)}]}, apply, later, later)
        self.assertEqual(result["L/child/layout"]["apply"], "outcome-unknown")
        self.assertEqual(result["L/top/layout"]["apply"], "not-run")
        self.assertEqual(calls, [])

    def test_noop_does_not_claim_save(self):
        def forbidden(*args):
            self.fail("no mutation after no-op")
        result = apply_views([("L/c/layout", (EDIT,))], lambda *args: {"gate": [{"xy": (10, 0)}]},
                             forbidden, forbidden, forbidden)
        self.assertEqual(result["L/c/layout"], {"apply": "no-op", "save": "not-run", "readback": "not-run"})

    def test_mutation_only_never_adds_save(self):
        result = apply_views([("L/c/layout", (EDIT,))], lambda *args: {"gate": [{"xy": (0, 0)}]},
                             lambda *args: True)
        self.assertEqual(result["L/c/layout"], {"apply": "completed", "save": "not-run", "readback": "not-run"})

    def test_failed_save_remains_unknown_and_stops_readback(self):
        def forbidden(*args):
            self.fail("no readback after ambiguous save")
        result = apply_views([("L/c/layout", (EDIT,))], lambda *args: {"gate": [{"xy": (0, 0)}]},
                             lambda *args: True, lambda *args: None, forbidden)
        self.assertEqual(result["L/c/layout"]["apply"], "completed")
        self.assertEqual(result["L/c/layout"]["save"], "outcome-unknown")

    def test_interrupt_keeps_partial_results_and_interrupt_semantics(self):
        def apply(view, edits):
            if view == "L/top/layout":
                raise KeyboardInterrupt()
            return True
        with self.assertRaises(PlanInterrupted) as caught:
            apply_views([("L/child/layout", (EDIT,)), ("L/top/layout", (EDIT,))],
                        lambda *args: {"gate": [{"xy": (0, 0)}]}, apply, lambda *args: True, lambda *args: True)
        outcomes = caught.exception.outcomes
        self.assertEqual(outcomes["L/child/layout"]["readback"], "verified")
        self.assertEqual(outcomes["L/top/layout"]["apply"], "outcome-unknown")
        self.assertEqual(outcomes["L/top/layout"]["save"], "not-run")

    def test_readback_failure_preserves_saved_state_and_stops_next_view(self):
        result = apply_views([("L/a/layout", (EDIT,)), ("L/b/layout", (EDIT,)), ("L/c/layout", (EDIT,))],
                             lambda *args: {"gate": [{"xy": (0, 0)}]}, lambda *args: True, lambda *args: True,
                             lambda view, edits: view != "L/b/layout")
        self.assertEqual(result["L/a/layout"]["readback"], "verified")
        self.assertEqual(result["L/b/layout"]["save"], "completed")
        self.assertEqual(result["L/b/layout"]["readback"], "outcome-unknown")
        self.assertEqual(result["L/c/layout"]["apply"], "not-run")

    def test_unbounded_view_iterators_are_not_consumed(self):
        def unbounded():
            self.fail("iterator must not be consumed")
            yield None
        with self.assertRaises(ValueError):
            apply_views(unbounded(), None, None)


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.candidate = PowerCandidate("A", 4, 10, 2, 2, (0, 0), 12, 12,
                                        Rect(0, 0, 10, 10), 12, 12, "synthetic-layer-rule", 40)
        self.kwargs = dict(boundary=Rect(0, 0, 30, 30), legal_parameters={(4, 10), (5, 10)},
                           fixed_before={"PAD": (0, 25, "R0")}, fixed_after={"PAD": (0, 25, "R0")},
                           keepouts=(), pad_policy="synthetic under-PAD permitted", even_ng=True, max_instances=100)

    def evaluate(self, **overrides):
        return evaluate_power_candidates([replace(self.candidate, **overrides)], **self.kwargs)[0]

    def test_measured_candidate_reports_reproducible_extent_and_metric(self):
        result = self.evaluate()
        self.assertTrue(result["accepted"])
        self.assertEqual(result["extent"], Rect(0, 0, 22, 22))
        self.assertEqual(result["score"], 160)

    def test_odd_ng_illegal_params_negative_gap_and_boundary_rejected(self):
        for overrides, reason in (({"ng": 5}, "odd-ng"), ({"w": 11}, "unmeasured-or-illegal-parameters"),
                                  ({"pitch_y": -1}, "nonpositive-or-off-grid-parameter"),
                                  ({"pitch_y": 11}, "insufficient-routing-or-spacing-pitch"),
                                  ({"rows": 3}, "outside-PRBoundary")):
            result = self.evaluate(**overrides)
            self.assertFalse(result["accepted"])
            self.assertIn(reason, result["reasons"])

    def test_pad_move_or_rotate_rejected(self):
        for pad in ((1, 25, "R0"), (0, 25, "MX")):
            self.kwargs["fixed_after"] = {"PAD": pad}
            with self.assertRaises(ValueError):
                self.evaluate()

    def test_under_pad_keepout_and_missing_policy_rejected(self):
        self.kwargs["keepouts"] = (Rect(0, 0, 5, 5),)
        self.assertIn("PAD-or-device-keepout", self.evaluate()["reasons"])
        self.kwargs["pad_policy"] = ""
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_ring_envelope_overlap_uses_resolved_pitch_not_bbox_packing(self):
        result = self.evaluate(envelope=Rect(0, 0, 14, 14))
        self.assertTrue(result["accepted"])
        self.assertEqual(result["extent"], Rect(0, 0, 26, 26))
        self.assertIn("unresolved-ring-and-spacing", self.evaluate(pitch_evidence="")["reasons"])

    def test_budget_rejects_before_large_loop(self):
        self.assertIn("instance-budget-exceeded", self.evaluate(rows=10**12)["reasons"])

    def test_candidates_rank_by_explicit_metric(self):
        result = evaluate_power_candidates([self.candidate, replace(self.candidate, name="B", score_per_device=41)], **self.kwargs)
        self.assertEqual([row["candidate"] for row in result], ["B", "A"])

    def test_floats_are_not_silently_snapped(self):
        with self.assertRaises(ValueError):
            Rect(0, 0, 10.2, 10)
        self.assertFalse(self.evaluate(w=10.0)["accepted"])

    def test_bad_candidate_does_not_prevent_valid_candidate_result(self):
        for change in ({"ng": None}, {"rows": "2"}, {"pitch_x": 12.5}, {"origin": None}):
            results = evaluate_power_candidates([replace(self.candidate, name="BAD", **change), self.candidate], **self.kwargs)
            self.assertTrue(results[0]["accepted"])
            self.assertFalse(results[1]["accepted"])

    def test_unbounded_candidate_iterators_are_not_consumed(self):
        def unbounded():
            self.fail("iterator must not be consumed")
            yield None
        with self.assertRaises(ValueError):
            evaluate_power_candidates(unbounded(), **self.kwargs)


if __name__ == "__main__":
    unittest.main()
