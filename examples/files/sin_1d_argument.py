#!/usr/bin/python3
import argparse
import math

parser = argparse.ArgumentParser()
parser.add_argument('--x', type=float)
args = parser.parse_args()
x = args.x
print(math.sin(x))
