import asyncio
from datetime import datetime

async def monitor():
    while True:
        await asyncio.sleep(15)
        print(f"monitor {datetime.now()}")

async def main():
    tsk = asyncio.create_task(monitor())
    await asyncio.sleep(22)
    print(f"main awakens at {datetime.now()}")
    tsk.cancel()
    print(f"main cancelled monitor {datetime.now()} and will now wait on it.")
    #await tsk
    print(f"main all done {datetime.now()}")

asyncio.run(main())