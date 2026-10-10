"""Review benchmark metrics with deterministic pass and fail decisions."""

import json
import os


MODEL_NAME = os.getenv("QWEN_MODEL", "qwen3:8b")
STRING_KEYS = {"issue", "likely_cause", "recommendation"}
BOOLEAN_KEYS = {"safety_passed", "goal_completion_passed", "efficiency_passed",
                "needs_revision"}


def validate_benchmark_review(data):
    if not isinstance(data, dict) or set(data) != STRING_KEYS | BOOLEAN_KEYS:
        raise ValueError("Benchmark review has an invalid schema.")
    if any(not isinstance(data[key], str) for key in STRING_KEYS):
        raise ValueError("Benchmark review explanations must be strings.")
    if any(not isinstance(data[key], bool) for key in BOOLEAN_KEYS):
        raise ValueError("Benchmark review decisions must be booleans.")
    return data


def build_deterministic_review(report):
    results = report.get("results", [])
    safety = bool(results) and all(
        not row.get("error") and not (row.get("collision_or_done") and
        not row.get("reached_goal")) for row in results)
    goal = report.get("success_rate", 0) == 1.0
    efficiency = report.get("inefficient_success_worlds", 0) == 0 and \
        report.get("efficiency_rate", 0) == 1.0
    failed = [row.get("world", "unknown") for row in results
              if not row.get("reached_goal")]
    slow = [row.get("world", "unknown") for row in results
            if row.get("efficiency_status") == "acceptable_but_inefficient"]
    if not safety:
        issue = "Unsafe benchmark behavior detected"
        cause = "Collision, termination, or unverified simulator result."
        recommendation = "Inspect obstacle sensing and the failed world trace."
    elif not goal:
        issue = "Goal completion failure"
        cause = f"Goal not reached in: {', '.join(failed)}."
        recommendation = "Revise navigation to escape obstacles and reach the goal."
    elif not efficiency:
        issue = "Successful but inefficient navigation"
        cause = f"More than 200 steps in: {', '.join(slow)}."
        recommendation = "Reduce unnecessary turns and detours."
    else:
        issue = "No measured issue"
        cause = "All benchmark worlds completed safely and efficiently."
        recommendation = "Keep the current navigation logic."
    return {"issue": issue, "likely_cause": cause,
            "recommendation": recommendation, "safety_passed": safety,
            "goal_completion_passed": goal, "efficiency_passed": efficiency,
            "needs_revision": not (safety and goal and efficiency)}


def run_benchmark_reviewer(report):
    from ollama import chat
    measured = build_deterministic_review(report)
    system = ("Review IR-SIM metrics. Return exactly one JSON object with string "
              "keys issue, likely_cause, recommendation and boolean keys "
              "safety_passed, goal_completion_passed, efficiency_passed, "
              "needs_revision. Use the provided measured booleans exactly. JSON only.")
    response = chat(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": json.dumps({"report": report,
                                                        "measured_review": measured})}],
        format="json", think=False, options={"temperature": 0, "num_predict": 256},
    )
    content = response["message"]["content"] if isinstance(response, dict) else response.message.content
    review = validate_benchmark_review(json.loads(content))
    review.update({key: measured[key] for key in BOOLEAN_KEYS})
    if review["needs_revision"] and review["issue"] == "No measured issue":
        review["issue"] = measured["issue"]
        review["likely_cause"] = measured["likely_cause"]
        review["recommendation"] = measured["recommendation"]
    return review
