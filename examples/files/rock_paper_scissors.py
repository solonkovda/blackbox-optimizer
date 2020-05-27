#!/usr/bin/python3
score_table = [
    [0, -1, 1],
    [1, 0, -1],
    [-1, 1, 0],
]
names_dict = {
    'rock': 0,
    'paper': 1,
    'scissors': 2,
}
first = names_dict[input().strip()]
second = names_dict[input().strip()]
print(score_table[first][second])
