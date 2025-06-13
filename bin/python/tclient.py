import sys
from time import sleep

who = sys.argv[1]
for i in range(3):
    sleep(3)
    if i == 1 and who == 'bob':
        print(f'{who} dislikes iteration {i}', file=sys.stderr)
    else:
        print(f'This is {who} at iteration {i}')
