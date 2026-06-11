ATTRIBUTES = ("mind", "will", "instinct", "dexterity", "body", "presence", "gift", "perception")
ATTRIBUTE_DISTRIBUTION = {0: 2, 1: 3, 2: 2, 3: 1}
CENTURY_LEVELS = {
    1: (1, 1), 2: (1, 2), 3: (1, 3), 4: (1, 4), 5: (1, 5),
    6: (2, 4), 7: (3, 3), 8: (4, 2), 9: (5, 1), 10: (6, 0),
}


def magic_slots(gift):
    return {"aspects": 0 if gift <= 0 else 1 if gift == 1 else 2, "spells": 0 if gift <= 0 else min(gift + 2, 5)}


def valid_attribute_distribution(values):
    return all(list(values).count(rank) == count for rank, count in ATTRIBUTE_DISTRIBUTION.items())


def valid_skill_distribution(ranks):
    return len(ranks) >= 4 and ranks.count(3) == 1 and ranks.count(2) == 3 and ranks.count(1) == len(ranks) - 4
