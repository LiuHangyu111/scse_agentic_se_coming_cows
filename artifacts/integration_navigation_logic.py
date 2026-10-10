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
