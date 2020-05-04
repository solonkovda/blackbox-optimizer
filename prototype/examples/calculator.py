#!/usr/bin/python3
operation = input().strip()
x = float(input())
y = float(input())
if operation == 'plus':
    print(x+y)
elif operation == 'minus':
    print(x-y)
else:
    print(x*y)
