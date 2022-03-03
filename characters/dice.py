import random


def roll_single(kind) -> int:
    result = random.randint(1, kind)
    while result % 6 == 0:
        result += random.randint(1, kind)
    return result


def roll(dice_string):
    amount, kind = dice_string.split('d')
    modifier = 0

    if '+' in kind:
        kind, modifier = kind.split('+')

    if '-' in kind:
        kind, modifier = kind.split('-')
        modifier = int(modifier) * -1

    result = list(reversed(sorted([roll_single(int(kind)) for r in range(int(amount))])))
    return {
        'list': result,
        'sum': sum(result) + int(modifier)
    }


if __name__ == '__main__':
    print(roll("12d6"))
    print(roll("12d6+3"))
    print(roll("1d6+3"))
    print(roll("1d6-3"))
