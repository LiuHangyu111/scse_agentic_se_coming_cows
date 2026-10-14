"""Run the real Developer Agent and save its simulator-facing entry point."""

import json
from pathlib import Path

from developer_agent import build_navigation_module, run_developer
from planner_agent import validate_plan
from testing_support import allow_local_ollama


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "artifacts" / "plan.json"
OUTPUT = ROOT / "artifacts" / "navigation_logic.py"
GENERATED = ROOT / "generated" / "navigation_logic.py"


def main() -> None:
    allow_local_ollama()
    plan = validate_plan(json.loads(INPUT.read_text(encoding="utf-8")))
    # The agent validates navigate() and adds the required decide_next_move(state)
    # entry point while retaining the original navigation function.
    module = build_navigation_module(run_developer(plan))
    OUTPUT.write_text(module, encoding="utf-8")
    GENERATED.parent.mkdir(exist_ok=True)
    GENERATED.write_text(module, encoding="utf-8")
    print(f"Validated Developer Agent output: {OUTPUT.relative_to(ROOT)}")
    print(OUTPUT.read_text(encoding="utf-8"))
    print(f"Simulator module: {GENERATED.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
