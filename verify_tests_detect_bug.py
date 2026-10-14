"""Prove that the test suite actually detects bugs in the navigation logic.

Testing assignment, "Introduce a bug":
  - change something important in navigation_logic.py
  - run the tests again; at least one test must fail
  - if the bug is not detected, add a test that detects it
  - then remove the bug and run everything again

This script automates that check against the navigation logic the Developer
Agent produced. Every mutant is injected into generated/navigation_logic.py and
then the existing suite is re-run unchanged:

    Level 2 : pytest test_generated_navigation_logic.py generated/
    Level 3 : the exhaustive 64-state simulation in runner.py

No test, threshold or perception rule is modified here. The original file is
restored from memory in a finally block, and its SHA-256 is verified before and
after so an interrupted run cannot leave a bug behind.
"""

import hashlib
from pathlib import Path
import subprocess
import sys


PROJECT_DIR = Path(__file__).resolve().parent
MODULE = PROJECT_DIR / "generated" / "navigation_logic.py"

# (name, description, original snippet, replacement snippet)
MUTANTS = [
    (
        "blocked-goal-first",
        "Go to the goal direction without checking whether it is blocked",
        '    if goal_direction == "FORWARD" and not front_blocked:\n',
        '    if goal_direction == "FORWARD":\n',
    ),
    (
        "never-reach-stop",
        "Move left instead of stopping when every direction is blocked",
        '        else:\n            return "STOP"\n',
        '        else:\n            return "LEFT"\n',
    ),
    (
        "crash-into-front",
        "Treat the front direction as permanently clear",
        "        if not front_blocked:\n            return \"FORWARD\"\n",
        "        if True:\n            return \"FORWARD\"\n",
    ),
]

PYTEST_TARGETS = ["test_generated_navigation_logic.py", "generated"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_pytest() -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *PYTEST_TARGETS],
        cwd=PROJECT_DIR, capture_output=True, text=True, timeout=300,
    )
    output = (result.stdout + result.stderr).strip().splitlines()
    summary = next((line for line in reversed(output) if line.strip()), "")
    return result.returncode, summary


def run_exhaustive() -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "runner.py"],
        cwd=PROJECT_DIR, capture_output=True, text=True, timeout=300,
    )
    output = (result.stdout + result.stderr).strip().splitlines()
    summary = next((line for line in reversed(output) if line.strip()), "")
    return result.returncode, summary


def main() -> int:
    print("=" * 78)
    print("Bug-detection verification (Testing assignment: 'Introduce a bug')")
    print("=" * 78)

    if not MODULE.exists():
        print(f"FAIL: {MODULE} is missing; run main.py first.")
        return 1

    original_hash = sha256(MODULE)
    original_source = MODULE.read_text(encoding="utf-8")
    print(f"Target module : {MODULE.relative_to(PROJECT_DIR)}")
    print(f"SHA-256 before: {original_hash}")
    print()

    failures: list[str] = []

    # ---- Baseline: the unmodified logic must pass both levels. -------------
    print("-" * 78)
    print("BASELINE  (no bug injected)")
    print("-" * 78)
    code, summary = run_exhaustive()
    print(f"  exhaustive 64-state simulation : exit={code} | {summary}")
    if code != 0:
        failures.append("baseline: exhaustive simulation does not pass")
    code, summary = run_pytest()
    print(f"  pytest suite                   : exit={code} | {summary}")
    if code != 0:
        failures.append("baseline: pytest suite does not pass")
    print()

    # ---- Inject each bug and confirm the suite catches it. ----------------
    try:
        for index, (name, description, needle, replacement) in enumerate(MUTANTS, 1):
            print("-" * 78)
            print(f"BUG {index}: {name} - {description}")
            print("-" * 78)

            if original_source.count(needle) != 1:
                print(f"  SKIP: anchor not found exactly once in the current logic")
                failures.append(f"{name}: could not inject (anchor missing)")
                print()
                continue

            MODULE.write_text(original_source.replace(needle, replacement, 1),
                              encoding="utf-8")
            print(f"  injected, module SHA-256 now: {sha256(MODULE)}")

            code, summary = run_exhaustive()
            detected_exhaustive = code != 0
            print(f"  exhaustive 64-state simulation : exit={code} | {summary}")
            print(f"    -> detected: {detected_exhaustive}")

            code, summary = run_pytest()
            detected_pytest = code != 0
            print(f"  pytest suite                   : exit={code} | {summary}")
            print(f"    -> detected: {detected_pytest}")

            if not (detected_exhaustive or detected_pytest):
                failures.append(f"{name}: no test detected this bug")
                print("  RESULT: NOT DETECTED")
            else:
                print("  RESULT: DETECTED")
            print()

            MODULE.write_text(original_source, encoding="utf-8")
    finally:
        # Always put the real logic back, even on interrupt.
        MODULE.write_text(original_source, encoding="utf-8")

    # ---- Restore and re-verify. ------------------------------------------
    restored_hash = sha256(MODULE)
    print("-" * 78)
    print("RESTORE   (bug removed)")
    print("-" * 78)
    print(f"SHA-256 after : {restored_hash}")
    print(f"unchanged     : {restored_hash == original_hash}")
    if restored_hash != original_hash:
        failures.append("restored file differs from the original")

    code, summary = run_exhaustive()
    print(f"  exhaustive 64-state simulation : exit={code} | {summary}")
    if code != 0:
        failures.append("after restore: exhaustive simulation does not pass")
    code, summary = run_pytest()
    print(f"  pytest suite                   : exit={code} | {summary}")
    if code != 0:
        failures.append("after restore: pytest suite does not pass")
    print()

    print("=" * 78)
    if failures:
        print("RESULT: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print(f"RESULT: PASS - all {len(MUTANTS)} injected bugs were detected, "
          f"and the original logic passes unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
