"""Exhaustive truth-table simulation for the navigation decision."""

import itertools
import json
from pathlib import Path


ARTIFACTS = Path(__file__).resolve().parent / "artifacts"


def expected_action(state):
    directions = ("FORWARD", "LEFT", "RIGHT")
    blocked = dict(zip(directions, (state["front_blocked"],
                                    state["left_blocked"], state["right_blocked"])))
    goal = next((action for action, flag in zip(directions,
                 (state["goal_ahead"], state["goal_on_left"],
                  state["goal_on_right"])) if flag), "FORWARD")
    if not blocked[goal]:
        return goal
    return next((action for action in directions if not blocked[action]), "STOP")


def scenarios():
    keys = ("front_blocked", "left_blocked", "right_blocked",
            "goal_ahead", "goal_on_left", "goal_on_right")
    for values in itertools.product((False, True), repeat=len(keys)):
        yield dict(zip(keys, values))


def run_simulation(decision_function=None):
    if decision_function is None:
        from generated.navigation_logic import decide_next_move
        decision_function = decide_next_move
    results = []
    for state in scenarios():
        expected = expected_action(state)
        try:
            actual = decision_function(state)
            error = None
        except Exception as exc:
            actual = None
            error = f"{type(exc).__name__}: {exc}"
        results.append({"state": state, "expected": expected, "actual": actual,
                        "passed": actual == expected, "error": error})
    passed = sum(item["passed"] for item in results)
    return {"total_scenarios": len(results), "passed_scenarios": passed,
            "failed_scenarios": len(results) - passed,
            "success_rate": passed / len(results), "results": results}


if __name__ == "__main__":
    ARTIFACTS.mkdir(exist_ok=True)
    report = run_simulation()
    path = ARTIFACTS / "simulation_report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{report['passed_scenarios']}/{report['total_scenarios']} scenarios passed; {path}")
