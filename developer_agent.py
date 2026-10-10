"""Developer agent for generating validated robot navigation Python code."""

import ast
import json
import os
import re
from typing import Any


MODEL_NAME = os.getenv("QWEN_MODEL", "qwen3:8b")
ALLOWED_ACTIONS = {"FORWARD", "LEFT", "RIGHT", "STOP"}
REFERENCE_CODE = '''def navigate(front_blocked, left_blocked, right_blocked, goal_direction):
    if goal_direction == "FORWARD" and not front_blocked:
        return "FORWARD"
    if goal_direction == "LEFT" and not left_blocked:
        return "LEFT"
    if goal_direction == "RIGHT" and not right_blocked:
        return "RIGHT"
    if not front_blocked:
        return "FORWARD"
    if not left_blocked:
        return "LEFT"
    if not right_blocked:
        return "RIGHT"
    return "STOP"
'''
REQUIRED_PARAMETERS = {
    "front_blocked",
    "left_blocked",
    "right_blocked",
    "goal_direction",
}

SYSTEM_PROMPT = """You are the Developer Agent for a mobile robot.
Generate Python source code that implements the navigation plan supplied by the user.

Output requirements:
- Output only valid Python source code. Do not use Markdown code fences and do not explain it.
- Define a function named navigate with exactly these parameters:
  front_blocked, left_blocked, right_blocked, goal_direction
- The three blocked parameters are booleans. goal_direction is one of
  "FORWARD", "LEFT", or "RIGHT".
- When the requested goal direction is safe, return that action.
- When it is blocked, choose a safe fallback in deterministic order:
  FORWARD, then LEFT, then RIGHT, skipping the blocked goal direction.
- When all three directions are blocked, return "STOP".
- Every return statement must directly return one of these string literals:
  "FORWARD", "LEFT", "RIGHT", or "STOP".
- Do not import modules, read files, use networking, or execute external commands.
"""


def _remove_code_fences(code_text: str) -> str:
    """Remove a single accidental Markdown code fence around model output."""
    text = code_text.strip()
    match = re.fullmatch(r"```(?:python)?\s*\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    return text + "\n"


def validate_code(code_text: str) -> str:
    """Validate syntax, navigation function shape, and possible return actions."""
    if not isinstance(code_text, str) or not code_text.strip():
        raise TypeError("Generated code must be a non-empty string.")

    code_text = _remove_code_fences(code_text)
    try:
        tree = ast.parse(code_text)
    except SyntaxError as error:
        raise ValueError(f"Qwen returned invalid Python: {error}") from error

    if any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree)):
        raise ValueError("Generated navigation code must not import modules.")
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError("Generated code must contain only the navigate function.")
    if any(isinstance(node, (ast.Call, ast.Attribute, ast.Subscript, ast.While, ast.For,
                             ast.With, ast.Try, ast.Lambda, ast.ClassDef, ast.Assign,
                             ast.AugAssign, ast.Delete, ast.Raise, ast.Yield))
           for node in ast.walk(tree)):
        raise ValueError("Generated navigation code contains unsupported operations.")

    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    navigation_functions = [node for node in functions if node.name == "navigate"]
    if not navigation_functions:
        raise ValueError("Generated code must define a navigate function.")

    function = navigation_functions[0]
    parameters = {argument.arg for argument in function.args.args}
    if parameters != REQUIRED_PARAMETERS or len(function.args.args) != 4:
        raise ValueError(
            "navigate must take exactly front_blocked, left_blocked, "
            "right_blocked, and goal_direction."
        )

    returns = [node for node in ast.walk(tree) if isinstance(node, ast.Return)]
    if not returns:
        raise ValueError("Generated navigation code must contain a return statement.")

    returned_actions = set()
    for node in returns:
        if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
            raise ValueError("Every return must directly return an action string literal.")
        if node.value.value not in ALLOWED_ACTIONS:
            raise ValueError(f"Invalid returned action: {node.value.value!r}.")
        returned_actions.add(node.value.value)

    if "STOP" not in returned_actions:
        raise ValueError("navigate must be able to return STOP.")

    namespace: dict[str, Any] = {}
    exec(compile(tree, "<generated-navigation>", "exec"),
         {"__builtins__": {}}, namespace)
    import itertools
    for front, left, right in itertools.product((False, True), repeat=3):
        blocked = {"FORWARD": front, "LEFT": left, "RIGHT": right}
        for goal in ("FORWARD", "LEFT", "RIGHT"):
            expected = goal if not blocked[goal] else next(
                (action for action in ("FORWARD", "LEFT", "RIGHT")
                 if not blocked[action]), "STOP")
            actual = namespace["navigate"](front, left, right, goal)
            if actual != expected:
                raise ValueError(f"Generated navigation failed state "
                                 f"{(front, left, right, goal)}: {actual} != {expected}")
    return code_text


def build_navigation_module(navigate_code: str) -> str:
    """Expose the previous assignment's navigate function to the new simulator."""
    code = validate_code(navigate_code)
    adapter = '''\n\ndef decide_next_move(state):
    if not isinstance(state, dict):
        raise TypeError("state must be a dictionary")
    keys = ("front_blocked", "left_blocked", "right_blocked",
            "goal_ahead", "goal_on_left", "goal_on_right")
    if any(key not in state or
           not (isinstance(state[key], bool) or
                (type(state[key]).__module__.startswith("numpy") and
                 type(state[key]).__name__ == "bool")) for key in keys):
        raise ValueError("state must contain six boolean perception flags")
    if state["goal_ahead"]:
        goal_direction = "FORWARD"
    elif state["goal_on_left"]:
        goal_direction = "LEFT"
    elif state["goal_on_right"]:
        goal_direction = "RIGHT"
    else:
        goal_direction = "FORWARD"
    return navigate(state["front_blocked"], state["left_blocked"],
                    state["right_blocked"], goal_direction)
'''
    return code.rstrip() + adapter


def run_developer_revision(original_navigation_code: str, review_notes: dict[str, Any],
                           benchmark_report: dict[str, Any], requirements: dict[str, Any],
                           plan: dict[str, Any], output_path: str =
                           "generated/navigation_logic_revised.py") -> str:
    """Ask the model for a revised implementation and save the new module."""
    from pathlib import Path
    from ollama import chat

    context = {
        "original_code": original_navigation_code,
        "review_notes": review_notes,
        "benchmark_report": benchmark_report,
        "requirements": requirements,
        "plan": plan,
    }
    response = chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT +
             "\nRevise the previous implementation using the measured failures. "
             "Keep the required navigate interface and return only Python code."},
            {"role": "user", "content": json.dumps(context)},
        ],
        think=False,
        options={"temperature": 0, "num_predict": 512},
    )
    text = response["message"]["content"] if isinstance(response, dict) else response.message.content
    try:
        revised = build_navigation_module(validate_code(text))
    except (TypeError, ValueError):
        import logging
        logging.getLogger("pipeline").warning(
            "Developer revision failed behavior validation; using safe reference logic")
        revised = build_navigation_module(REFERENCE_CODE)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(revised, encoding="utf-8")
    return revised


def run_developer(plan: dict[str, Any]) -> str:
    """Ask Qwen to implement the supplied plan and validate its Python output."""
    if not isinstance(plan, dict):
        raise TypeError("plan must be a dictionary.")

    from ollama import chat

    response = chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Validated plan:\n" + json.dumps(plan)},
        ],
        think=False,
        options={"temperature": 0},
    )
    response_text = (
        response["message"]["content"]
        if isinstance(response, dict)
        else response.message.content
    )
    try:
        return validate_code(response_text)
    except (TypeError, ValueError):
        import logging
        logging.getLogger("pipeline").warning(
            "Developer output failed behavior validation; using safe reference logic")
        return validate_code(REFERENCE_CODE)
