"""Run all supplied IR-SIM worlds and aggregate their saved reports."""

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
WORLDS = ("world_easy.yaml", "world_medium.yaml", "world_difficult.yaml",
          "world_custom.yaml")


def run_world(world_file):
    report_file = ARTIFACTS / "irsim_report.json"
    report_file.unlink(missing_ok=True)
    env = os.environ.copy()
    env.setdefault("MPLBACKEND", "Agg")
    try:
        process = subprocess.run(
            [sys.executable, str(ROOT / "test_irsim_with_agent.py"), str(world_file)],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        return {"world": world_file.name, "reached_goal": False,
                "collision_or_done": False, "steps_taken": 0,
                "efficiency_status": "failed",
                "error": "IR-SIM process timed out after 180 seconds"}
    if process.returncode != 0 or not report_file.exists():
        return {"world": world_file.name, "reached_goal": False,
                "collision_or_done": False, "steps_taken": 0,
                "efficiency_status": "failed", "error":
                (process.stderr or process.stdout)[-3000:] or
                "IR-SIM process did not produce a report"}
    result = json.loads(report_file.read_text(encoding="utf-8"))
    result["world"] = world_file.name
    result["error"] = None
    return result


def run_benchmark():
    ARTIFACTS.mkdir(exist_ok=True)
    results = [run_world(ROOT / "irsim_worlds" / name) for name in WORLDS]
    total = len(results)
    reached = sum(bool(row["reached_goal"]) for row in results)
    efficient = sum(row["efficiency_status"] == "efficient" for row in results)
    slow = sum(row["efficiency_status"] == "acceptable_but_inefficient"
               for row in results)
    report = {"total_worlds": total, "goals_reached": reached,
              "success_rate": reached / total, "efficient_worlds": efficient,
              "inefficient_success_worlds": slow,
              "failed_worlds": total - reached,
              "efficiency_rate": efficient / total,
              "average_steps_taken": sum(row["steps_taken"] for row in results) / total,
              "results": results}
    path = ARTIFACTS / "irsim_benchmark_report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run_benchmark()
