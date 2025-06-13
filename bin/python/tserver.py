import asyncio
import sys

async def do_one(name):
    p = await asyncio.create_subprocess_exec(
        sys.executable, 'bin/python/tclient.py', name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    while not (p.stdout.at_eof() and p.stderr.at_eof()):
        # x = await p.stdout.readline()
        # if x:
        #     print(x.decode().rstrip())
        # else:
        #     print('EOF on stdout')
        # continue
        done, pending = await asyncio.wait(
            [await p.stdout.readline(), await p.stderr.readline()],
            return_when=asyncio.FIRST_COMPLETED)
        for s in done:
            line = s.result().decode().rstrip()
            if s == p.stdout:
                print(line)
            else:
                print(f"ERR: {line}")
    print(f'{name} returns {p.returncode}')

async def main():
    await asyncio.gather(
        do_one('alice'),
        do_one('bob'),
    )
asyncio.run(main())