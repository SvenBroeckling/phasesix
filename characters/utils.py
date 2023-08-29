def crit_successes(value, crit_threshold=11):
    """Returns the number of additional successes caused by crits"""
    ca = 0
    while value > crit_threshold - 1:
        value -= 6
        ca += 1
    return ca


