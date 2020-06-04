#!/usr/bin/python3
import argparse
import os
import sys
from math import sin

parser = argparse.ArgumentParser()
parser.add_argument('--y', type=float)
args = parser.parse_args()

x = float(input())
y = args.y
z = float(os.environ.get('z'))
print(sin(x) + sin(y) + sin(z))
