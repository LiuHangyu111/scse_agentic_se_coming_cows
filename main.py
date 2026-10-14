"""Run the integration and simulation assignment from one entry point."""

import json
import logging
import os
from pathlib import Path
import subprocess
import sys

from analyst_agent import run_analyst
from benchmark_irsim import run_benchmark
from developer_agent import (build_navigation_module, run_developer,
                             run_developer_revision)
from planner_agent import run_planner
from reviewer_agent import run_reviewer
from reviewer_benchmark_agent import run_benchmark_reviewer
from runner import run_simulation
from test_agent import run_test_agent


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
GENERATED = ROOT / "generated"
LOG = logging.getLogger("pipeline")


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    LOG.info("Saved %s", path.relative_to(ROOT))


def validate_navigation(module_text, test_name):
    (GENERATED / "navigation_logic.py").write_text(module_text, encoding="utf-8")
    LOG.info("Developer Agent created generated/navigation_logic.py")
    (ARTIFACTS / "navigation_logic.py").write_text(module_text, encoding="utf-8")
    LOG.info("Developer Agent saved artifacts/navigation_logic.py")
    test_code = run_test_agent(
        json.loads((ARTIFACTS / "integration_requirements.json").read_text()),
        json.loads((ARTIFACTS / "integration_plan.json").read_text()), module_text)
    test_file = GENERATED / test_name
    test_file.write_text(test_code, encoding="utf-8")
    LOG.info("Test Agent created %s", test_file.relative_to(ROOT))
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q",
         "test_generated_navigation_logic.py", str(test_file.relative_to(ROOT))],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    LOG.info("Pytest exit=%s: %s", result.returncode,
             (result.stdout + result.stderr).strip())
    if result.returncode:
        raise RuntimeError("Generated navigation tests failed; see trace.log")
    from importlib import import_module, reload
    importlib_module = import_module("generated.navigation_logic")
    reload(importlib_module)
    simulation = run_simulation(importlib_module.decide_next_move)
    save_json(ARTIFACTS / "simulation_report.json", simulation)
    LOG.info("Simulation Runner passed %d/%d scenarios",
             simulation["passed_scenarios"], simulation["total_scenarios"])
    simulation_review = run_reviewer(simulation)
    save_json(ARTIFACTS / "simulation_review.json", simulation_review)
    LOG.info("Reviewer Agent reviewed simulation: revision=%s",
             simulation_review["needs_revision"])
    benchmark = run_benchmark()
    LOG.info("IR-SIM benchmark created irsim_benchmark_report.json")
    for row in benchmark["results"]:
        LOG.info("IR-SIM world=%s reached=%s steps=%s efficiency=%s error=%s",
                 row["world"], row["reached_goal"], row["steps_taken"],
                 row["efficiency_status"], row.get("error"))
    benchmark_review = run_benchmark_reviewer(benchmark)
    save_json(ARTIFACTS / "irsim_benchmark_review.json", benchmark_review)
    LOG.info("Benchmark Reviewer finished: revision=%s",
             benchmark_review["needs_revision"])
    return simulation, simulation_review, benchmark, benchmark_review


def main():
    bypass = os.environ.get("NO_PROXY", "")
    os.environ["NO_PROXY"] = ",".join(part for part in
        (bypass, "127.0.0.1", "localhost") if part)
    ARTIFACTS.mkdir(exist_ok=True)
    GENERATED.mkdir(exist_ok=True)
    (GENERATED / "__init__.py").touch()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(ROOT / "trace.log", mode="w"),
                                  logging.StreamHandler(sys.stdout)])
    try:
        brief = (ROOT / "brief.txt").read_text(encoding="utf-8")
        LOG.info("Orchestrator loaded brief.txt")
        requirements = run_analyst(brief)
        save_json(ARTIFACTS / "integration_requirements.json", requirements)
        LOG.info("Analyst Agent created integration_requirements.json")
        plan = run_planner(requirements)
        save_json(ARTIFACTS / "integration_plan.json", plan)
        LOG.info("Planner Agent created integration_plan.json")
        navigate_code = run_developer(plan)
        (ARTIFACTS / "integration_navigation_logic.py").write_text(
            navigate_code, encoding="utf-8")
        LOG.info("Developer Agent created integration_navigation_logic.py")
        original_module = build_navigation_module(navigate_code)
        simulation, simulation_review, benchmark, benchmark_review = \
            validate_navigation(original_module, "test_navigation_agent.py")
        save_json(ARTIFACTS / "initial_simulation_report.json", simulation)
        save_json(ARTIFACTS / "initial_irsim_benchmark_report.json", benchmark)
        LOG.info("Developer Agent starting revision from review notes and benchmark")
        revised_module = run_developer_revision(
            navigate_code,
            {"simulation": simulation_review, "benchmark": benchmark_review},
            benchmark, requirements, plan,
            str(GENERATED / "navigation_logic_revised.py"))
        LOG.info("Developer Agent created generated/navigation_logic_revised.py")
        simulation, simulation_review, benchmark, benchmark_review = \
            validate_navigation(revised_module, "test_navigation_agent_revised.py")
        LOG.info("Revised navigation logic re-tested in all four IR-SIM worlds")
        summary = {"simulation_passed": not simulation_review["needs_revision"],
                   "safety_passed": benchmark_review["safety_passed"],
                   "goal_completion_passed": benchmark_review["goal_completion_passed"],
                   "efficiency_passed": benchmark_review["efficiency_passed"],
                   "needs_revision": benchmark_review["needs_revision"] or
                   simulation_review["needs_revision"]}
        save_json(ARTIFACTS / "pipeline_summary.json", summary)
        LOG.info("Orchestrator finished: %s", summary)
        return 0 if not summary["needs_revision"] else 2
    except Exception:
        LOG.exception("Orchestrator failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
