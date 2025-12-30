import numpy as np


def det_pos(x, y):
    if x in {0, 3} and y in {0, 3}:
        return "esquina"
    elif x in {1, 2} and y in {1, 2}:
        return "centro"
    else:
        return "borde"


def presiones(x, y, s):
    P = np.zeros((4, 4))
    pos = det_pos(x, y)
    if pos == "esquina":
        for i in {0, 3}:
            for j in {0, 3}:
                P[i, j] = 4 - s

        P[(x + 2) % 4, y] = s
        P[(x + 2) % 4, (y + 2) % 4] = 4 - s
        P[x, (y + 2) % 4] = s

        P[3 - x, 2 - y // 3] = s
        P[2 - x // 3, 3 - y] = s

        return P

    elif pos == "centro":
        for a in (0, 1):
            for b in (0, 1):
                if ((2 * (x % 2) + a) == (2 * (y % 2) + b)) or (
                    (2 * (x % 2) + a) + (2 * (y % 2) + b)
                ) == 3:
                    P[(2 * (x % 2) + a, 2 * (y % 2) + b)] = 4 - s
                else:
                    P[(2 * (x % 2) + a, 2 * (y % 2) + b)] = s
        return P

    elif pos == "borde":
        ax = (x + 2) % 4
        by = (y + 2) % 4

        if x == 0:
            X = (0, 2, 3)
        elif x == 1:
            X = (2, 3)
        elif x == 2:
            X = (0, 1)
        else:
            X = (0, 1, 3)

        if y == 0:
            Y = (0, 2, 3)
        elif y == 1:
            Y = (2, 3)
        elif y == 2:
            Y = (0, 1)
        else:
            Y = (0, 1, 3)

        for i in X:
            for j in Y:
                P[i, j] = s if ((i == ax) ^ (j == by)) else (4 - s)

        return P


S = np.zeros((4, 4))
P = np.zeros((4, 4))
for x in range(0, 4):
    for y in range(0, 4):
        s = int(input(f"x:{x}, y:{y}, s:"))
        S[x, y] = s
        P = P + presiones(x, y, s)

P = P % 4
print(f"Estado inicial:\n{S}")
print(f"Matriz de presiones:\n{P}")
