import sys
from time import sleep

who = sys.argv[1]
for i in range(3):
    sleep(3)
    print(f'This is {who} at iteration {i}')
