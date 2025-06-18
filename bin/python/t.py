from pathlib import Path
import sys

MAGIC=888

# There has got to be a better way
# Modify path so we can pickup my parts, regardless of cwd
target = str((Path(__file__).parent) / "test_dir")
if target not in sys.path:
    sys.path.append(target)
from fred import silly

silly()

