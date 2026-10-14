"""Run the real Planner Agent using the saved requirements artifact."""

import json
from pathlib import Path

from analyst_agent import validate_requirements
from planner_agent import run_planner, validate_plan
from testing_support import allow_local_ollama


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "artifacts" / "requirements.json"
OUTPUT = ROOT / "artifacts" / "plan.json"


def main() -> None:
    allow_local_ollama()
    requirements = validate_requirements(json.loads(INPUT.read_text(encoding="utf-8")))
    plan = validate_plan(run_planner(requirements))
    OUTPUT.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print(f"Validated Planner Agent output: {OUTPUT.relative_to(ROOT)}")
    print(OUTPUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
