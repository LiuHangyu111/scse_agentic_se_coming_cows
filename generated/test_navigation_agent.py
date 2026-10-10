import pytest
from generated.navigation_logic import decide_next_move

def test_safe_goal_direction():
    state = dict(front_blocked=False, left_blocked=False, right_blocked=False,
                 goal_ahead=False, goal_on_left=True, goal_on_right=False)
    assert decide_next_move(state) == "LEFT"

def test_stop_when_surrounded():
    state = dict(front_blocked=True, left_blocked=True, right_blocked=True,
                 goal_ahead=True, goal_on_left=False, goal_on_right=False)
    assert decide_next_move(state) == "STOP"

from runner import scenarios, expected_action

def test_all_perception_scenarios():
    for state in scenarios():
        assert decide_next_move(state) == expected_action(state), state
