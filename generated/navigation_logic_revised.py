def navigate(front_blocked, left_blocked, right_blocked, goal_direction):
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

def decide_next_move(state):
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
