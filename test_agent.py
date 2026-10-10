"""LLM test agent with mandatory exhaustive safety coverage."""

import ast
import json
import os


MODEL_NAME = os.getenv("QWEN_MODEL", "qwen3:8b")
SYSTEM_PROMPT = """You are a robot navigation Test Agent. Return only Python pytest code.
Import decide_next_move from generated.navigation_logic. The function accepts a
dictionary of six booleans: front_blocked, left_blocked, right_blocked,
goal_ahead, goal_on_left, goal_on_right. It returns FORWARD, LEFT, RIGHT, or STOP.
Write at least one test function with assert statements for goal preference,
blocked directions, safe fallback, and STOP when every direction is blocked.
No Markdown fences or explanation."""


def validate_test_code(code):
    if not isinstance(code, str) or not code.strip() or "```" in code:
        raise ValueError("Test Agent must return plain non-empty Python code.")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise ValueError("Test Agent returned invalid Python.") from exc
    if "from generated.navigation_logic import decide_next_move" not in code or \
       not any(isinstance(n, ast.Assert) for n in ast.walk(tree)):
        raise ValueError("Tests must import and assert decide_next_move behavior.")
    if not any(isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
               for n in tree.body):
        raise ValueError("Tests must contain a pytest test function.")
    return code.rstrip() + "\n"


def run_test_agent(requirements, plan, navigation_code):
    from ollama import chat
    response = chat(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": json.dumps({
                      "requirements": requirements, "plan": plan,
                      "decide_next_move": navigation_code})}],
        think=False,
        options={"temperature": 0, "num_predict": 256},
    )
    content = response["message"]["content"] if isinstance(response, dict) else response.message.content
    try:
        generated = validate_test_code(content)
    except ValueError as exc:
        import logging
        logging.getLogger("pipeline").warning(
            "Test Agent draft failed validation (%s); using exhaustive tests", exc)
        generated = '''import pytest
from generated.navigation_logic import decide_next_move

def test_safe_goal_direction():
    state = dict(front_blocked=False, left_blocked=False, right_blocked=False,
                 goal_ahead=False, goal_on_left=True, goal_on_right=False)
    assert decide_next_move(state) == "LEFT"

def test_stop_when_surrounded():
    state = dict(front_blocked=True, left_blocked=True, right_blocked=True,
                 goal_ahead=True, goal_on_left=False, goal_on_right=False)
    assert decide_next_move(state) == "STOP"
'''
        generated = validate_test_code(generated)
    exhaustive = '''\nfrom runner import scenarios, expected_action

def test_all_perception_scenarios():
    for state in scenarios():
        assert decide_next_move(state) == expected_action(state), state
'''
    return generated + exhaustive
