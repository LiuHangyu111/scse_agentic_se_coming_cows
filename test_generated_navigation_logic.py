"""Behavioral tests for the generated decide_next_move(state) entry point."""

import importlib.util
import os
from pathlib import Path

import pytest

from runner import expected_action, scenarios


ROOT = Path(__file__).resolve().parent
MODULE_PATH = Path(os.environ.get(
    "NAVIGATION_LOGIC_PATH", ROOT / "generated" / "navigation_logic.py"))
spec = importlib.util.spec_from_file_location("navigation_logic_under_test", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
decide_next_move = module.decide_next_move


@pytest.mark.parametrize("state", list(scenarios()))
def test_every_known_perception_state(state):
    action = decide_next_move(state)
    assert action in {"FORWARD", "LEFT", "RIGHT", "STOP"}
    assert action == expected_action(state)


def test_goal_direction_is_used_when_safe():
    state = dict(front_blocked=False, left_blocked=False, right_blocked=False,
                 goal_ahead=False, goal_on_left=True, goal_on_right=False)
    assert decide_next_move(state) == "LEFT"


def test_stop_when_every_direction_is_blocked():
    state = dict(front_blocked=True, left_blocked=True, right_blocked=True,
                 goal_ahead=True, goal_on_left=False, goal_on_right=False)
    assert decide_next_move(state) == "STOP"


@pytest.mark.parametrize("state", [None, {}, {"front_blocked": "false"}])
def test_invalid_sensor_input_is_rejected(state):
    with pytest.raises((TypeError, ValueError)):
        decide_next_move(state)
