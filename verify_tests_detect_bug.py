"""Demonstrate a real test failure from one intentional navigation bug."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "artifacts" / "navigation_logic.py"
REPORT = ROOT / "artifacts" / "testing_evidence.json"
MARKER = "def decide_next_move(state):\n"
BUG = ("def decide_next_move(state):\n"
       "    if state == dict(front_blocked=False, left_blocked=True, "
       "right_blocked=True,\n"
       "                     goal_ahead=True, goal_on_left=False, "
       "goal_on_right=False):\n"
       "        return 'RIGHT'  # Intentional bug: right is blocked.\n")


def run_tests(env):
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "test_generated_navigation_logic.py"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    if source.count(MARKER) != 1:
        raise RuntimeError("Expected exactly one decide_next_move entry point")
    with tempfile.TemporaryDirectory(prefix="scse-navigation-bug-") as directory:
        mutant = Path(directory) / "navigation_logic.py"
        mutant.write_text(source.replace(MARKER, BUG, 1), encoding="utf-8")
        env = os.environ.copy()
        env["NAVIGATION_LOGIC_PATH"] = str(mutant)
        faulty = run_tests(env)
    if faulty.returncode == 0 or "FAILED" not in faulty.stdout:
        raise RuntimeError("Behavioral tests did not detect the intentional bug")
    clean_env = os.environ.copy()
    clean_env.pop("NAVIGATION_LOGIC_PATH", None)
    clean = run_tests(clean_env)
    if clean.returncode != 0:
        raise RuntimeError("Original navigation logic failed after removing the bug:\n"
                           + clean.stdout + clean.stderr)
    report = {
        "mutation": "Return RIGHT while right is blocked and forward is safe",
        "counterexample": {
            "state": {"front_blocked": False, "left_blocked": True,
                      "right_blocked": True, "goal_ahead": True,
                      "goal_on_left": False, "goal_on_right": False},
            "expected": "FORWARD", "mutant_actual": "RIGHT"},
        "mutant_test_exit_code": faulty.returncode,
        "mutant_failed_as_expected": True,
        "mutant_pytest_summary": next(
            (line for line in faulty.stdout.splitlines() if " failed" in line), ""),
        "original_test_exit_code": clean.returncode,
        "original_passed": True,
        "original_pytest_summary": next(
            (line for line in clean.stdout.splitlines() if " passed" in line), ""),
        "method": "Mutant was an isolated temporary copy; tracked navigation logic was unchanged"
    }
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
