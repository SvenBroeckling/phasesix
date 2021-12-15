import random


def roll_single(kind) -> int:
    result = random.randint(1, kind)
    while result % 6 == 0:
        result += random.randint(1, kind)
    return result


def roll(dice_string) -> list[int]:
    amount, kind = dice_string.split('d')
    return list(reversed(sorted([roll_single(int(kind)) for r in range(int(amount))])))


if __name__ == '__main__':
    print(roll("12d6"))
