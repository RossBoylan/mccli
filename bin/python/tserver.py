import asyncio
import sys

async def do_one(name):
    p = await asyncio.create_subprocess_exec(
        sys.executable, 'bin/python/tclient.py', name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    print(f'[{stdout.decode()}]')
    if stderr:
        print(f'[{stderr.decode()}]')
    print(f'{name} returns {p.returncode}')

async def main():
    await asyncio.gather(
        do_one('alice'),
        do_one('bob'),
    )
asyncio.run(main())