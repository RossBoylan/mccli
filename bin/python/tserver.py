import asyncio
import sys

async def main():
    p = await asyncio.create_subprocess_exec(
        sys.executable, 'bin/python/tclient.py', "fred", "barney",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    print(f'[{stdout.decode()}]')
    if stderr:
        print(f'[{stderr.decode()}]')
    print(f'[{p.returncode}]')
asyncio.run(main())