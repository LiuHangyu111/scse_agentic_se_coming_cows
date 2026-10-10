"""Review measured truth-table simulation results."""

import json
import os


MODEL_NAME = os.getenv("QWEN_MODEL", "qwen3:8b")
KEYS = {"issue", "likely_cause", "recommendation", "needs_revision"}
SYSTEM_PROMPT = """You review a mobile robot navigation simulation report.
Return exactly one JSON object with string keys issue, likely_cause,
recommendation, and boolean needs_revision. Identify concrete failed states.
If all scenarios pass, needs_revision must be false. Return JSON only."""


def validate_review(data):
    if not isinstance(data, dict) or set(data) != KEYS:
        raise ValueError("Simulation review has an invalid schema.")
    if any(not isinstance(data[key], str) for key in KEYS - {"needs_revision"}):
        raise ValueError("Review explanations must be strings.")
    if not isinstance(data["needs_revision"], bool):
        raise ValueError("needs_revision must be a boolean.")
    return data


def run_reviewer(simulation_report):
    from ollama import chat
    failures = [row for row in simulation_report["results"] if not row["passed"]]
    response = chat(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": json.dumps({
                      "total_scenarios": simulation_report["total_scenarios"],
                      "failed_scenarios": simulation_report["failed_scenarios"],
                      "failures": failures})}],
        format="json", think=False, options={"temperature": 0, "num_predict": 256},
    )
    content = response["message"]["content"] if isinstance(response, dict) else response.message.content
    review = validate_review(json.loads(content))
    review["needs_revision"] = bool(failures)
    return review
