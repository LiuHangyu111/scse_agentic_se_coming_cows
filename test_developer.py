"""Level 1 smoke test for the Developer Agent.

Runs the real Developer Agent on artifacts/plan.json, stores the validated
navigation module in generated/navigation_logic.py, and displays it.

The original navigation logic written by run_developer.py stays untouched in
navigation_logic.py. What other agents and programs call is decide_next_move(state),
which the developer-agent adapter adds on top of the retained navigate() function.
"""

from pathlib import Path

from developer_agent import (MODEL_NAME, build_navigation_module, run_developer)
from planner_agent import validate_plan


PROJECT_DIR = Path(__file__).resolve().parent
PLAN_FILE = PROJECT_DIR / "artifacts" / "plan.json"
OUTPUT_FILE = PROJECT_DIR / "generated" / "navigation_logic.py"


def main() -> int:
    import json

    print(f"Model under test: {MODEL_NAME}")
    print(f"Input : {PLAN_FILE.relative_to(PROJECT_DIR)}")

    with PLAN_FILE.open(encoding="utf-8") as source:
        plan = validate_plan(json.load(source))

    # The developer's own validation accepts or rejects the model output here.
    navigation_code = run_developer(plan)
    module_code = build_navigation_module(navigation_code)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(module_code, encoding="utf-8")

    has_entry_point = "def decide_next_move(state)" in module_code
    print(f"Output: {OUTPUT_FILE.relative_to(PROJECT_DIR)}")
    print(f"decide_next_move(state) present: {has_entry_point}")
    print("--- generated/navigation_logic.py ---")
    print(module_code)

    if not has_entry_point:
        print("RESULT: FAIL - decide_next_move(state) entry point is missing")
        return 1
    print("RESULT: PASS - plan turned into callable navigation logic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
