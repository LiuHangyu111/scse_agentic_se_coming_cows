def navigate(front_blocked, left_blocked, right_blocked, goal_direction):
    if goal_direction == "FORWARD" and not front_blocked:
        return "FORWARD"
    elif goal_direction == "LEFT" and not left_blocked:
        return "LEFT"
    elif goal_direction == "RIGHT" and not right_blocked:
        return "RIGHT"
    else:
        if not front_blocked:
            return "FORWARD"
        elif not left_blocked:
            return "LEFT"
        elif not right_blocked:
            return "RIGHT"
        else:
            return "STOP"
