import asyncio
import itertools
import json

class SwitchBoard:
    """Receives messages and routes them to interested parties via function calls.
    The functions should take 2 arguments, the JSON "object" and its string representation.
    """
    def __init__(self):
        self._syncFunctions = []
        self._asyncFunctions = []

    def addSyncFunction(self, fn):
        "add a regular function, which is blocking"
        self._syncFunctions.append(fn)

    def addAsyncFunction(self, fn):
        "add an async function that is awaitable"
        self._asyncFunctions.append(fn)

    async def message_obj(self, obj):
        "Receive message as a JSON object.  Transmit it to all interested."
        # Because this is async it will not do to put the string
        # version in an instance variable.
        json_str = json.dumps(obj)
        myasyncs = [f(obj, json_str) for f in self._asyncFunctions]
        later = asyncio.gather(*myasyncs)
        for f in self._syncFunctions:
            f(obj, json_str)
        await later

    def close(self):
        "Call when all done to assure cleanup"
        for f in itertools.chain(self._asyncFunctions, self._syncFunctions):
            try:
                f.close()
            except:
                pass
