"""Level 1 smoke test for the Analyst Agent.

Runs the real Analyst Agent on the original brief.txt and stores the validated
result in artifacts/requirements.json, then displays it.
"""

import json
from pathlib import Path

from analyst_agent import MODEL_NAME, run_analyst


PROJECT_DIR = Path(__file__).resolve().parent
BRIEF_FILE = PROJECT_DIR / "brief.txt"
OUTPUT_FILE = PROJECT_DIR / "artifacts" / "requirements.json"


def main() -> int:
    print(f"Model under test: {MODEL_NAME}")
    print(f"Input : {BRIEF_FILE.name}")

    brief_text = BRIEF_FILE.read_text(encoding="utf-8")

    # The agent's own validation accepts or rejects the model output here.
    requirements = run_analyst(brief_text)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as output:
        json.dump(requirements, output, ensure_ascii=False, indent=2)
        output.write("\n")

    print(f"Output: {OUTPUT_FILE.relative_to(PROJECT_DIR)}")
    print("--- requirements.json ---")
    print(json.dumps(requirements, ensure_ascii=False, indent=2))
    print("RESULT: PASS - brief text turned into a usable requirements artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
