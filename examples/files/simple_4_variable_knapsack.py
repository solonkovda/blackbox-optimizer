#!/usr/bin/python3
# This example tests the constraint system by throwing exception if
# bad values are given.
cost_table = [240, 1, 60, 60]
weight_table = [60, 1, 30, 35]
max_weight = 100

total_cost = 0
total_weight = 0
for i in range(len(cost_table)):
    amount = int(input())
    total_cost += cost_table[i] * amount
    total_weight += weight_table[i] * amount
if total_weight > max_weight:
    raise AttributeError('Maximum weight exceeded')
print(-total_cost)
