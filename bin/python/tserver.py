import asyncio
import sys

async def do_one(name):
    p = await asyncio.create_subprocess_exec(
        sys.executable, 'bin/python/tclient.py', name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    taskout = None
    taskerr = None
    while not (p.stdout.at_eof() and p.stderr.at_eof()):
        # x = await p.stdout.readline()
        # if x:
        #     print(x.decode().rstrip())
        # else:
        #     print('EOF on stdout')
        # continue
        if taskout is None:
            taskout = asyncio.create_task(p.stdout.readline(), name="stdout")
        if taskerr is None:
            taskerr = asyncio.create_task(p.stderr.readline(), name="stderr")
        done, pending = await asyncio.wait(
            [taskout, taskerr],
            return_when=asyncio.FIRST_COMPLETED)
        for s in done:
            line = s.result()
            # I generally get back 0 byte string for stderr even when nothing was written to stderr
            n = len(line)
            if n:
                line = line.decode().rstrip()
            if s.get_name() == "stderr":
                taskerr = None
                if n:
                    print(f"ERR: {line}")
            else:
                taskout = None
                if n:
                    print(line)
    print(f'{name} returns {p.returncode}')

async def main():
    await asyncio.gather(
        do_one('alice'),
        do_one('bob'),
    )
asyncio.run(main())