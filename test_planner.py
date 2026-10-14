"""Level 1 smoke test for the Planner Agent.

Runs the real Planner Agent on artifacts/requirements.json and stores the
validated plan in artifacts/plan.json, then displays it.
"""

import json
from pathlib import Path

from planner_agent import MODEL_NAME, run_planner


PROJECT_DIR = Path(__file__).resolve().parent
REQUIREMENTS_FILE = PROJECT_DIR / "artifacts" / "requirements.json"
OUTPUT_FILE = PROJECT_DIR / "artifacts" / "plan.json"


def main() -> int:
    print(f"Model under test: {MODEL_NAME}")
    print(f"Input : {REQUIREMENTS_FILE.relative_to(PROJECT_DIR)}")

    with REQUIREMENTS_FILE.open(encoding="utf-8") as source:
        requirements = json.load(source)

    # The planner's own validation accepts or rejects the model output here.
    plan = run_planner(requirements)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as output:
        json.dump(plan, output, ensure_ascii=False, indent=2)
        output.write("\n")

    print(f"Output: {OUTPUT_FILE.relative_to(PROJECT_DIR)}")
    print("--- plan.json ---")
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    print("RESULT: PASS - requirements artifact turned into a plan the developer can use")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
