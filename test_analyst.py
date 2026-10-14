"""Run the real Analyst Agent against the original brief (testing exercise)."""

import json
from pathlib import Path

from analyst_agent import run_analyst, validate_requirements
from testing_support import allow_local_ollama


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "artifacts" / "requirements.json"


def main() -> None:
    allow_local_ollama()
    brief = (ROOT / "brief.txt").read_text(encoding="utf-8")
    requirements = validate_requirements(run_analyst(brief))
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(requirements, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print(f"Validated Analyst Agent output: {OUTPUT.relative_to(ROOT)}")
    print(OUTPUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
