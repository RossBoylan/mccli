"""Each class here takes a call with a message from SwitchBoard
and does something useful with the message.

All must be callable with 2 arguments, a json object and its
string representation.  They must *not* modify either.

They should also implement a close() method to do whatever cleanup is
necessary.
"""
from pathlib import Path

class StupidLogfile:
    "really simple logging to a file"
    def __init__(self, logfile: Path|str):
        self._logfile = Path(logfile)
        self._fout = self._logfile.open("at")

    def __call__(self, obj, json_str):
        "log the message"
        self._fout.write(json_str)

    def close(self):
        self._fout.close()

class DumbTerminalLog:
    """simple logging that works for any stdout
    No coloring, beeping or styling.
    No curses-type manipulation.
    No filtering out unimportant info.
    """
    def __call__(self, obj, json_str):
        print(json_str, end="")

    def close(self):
        "Leave it open for others"
        pass