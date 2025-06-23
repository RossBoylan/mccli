if False:
    # from pathlib import Path
    import sys

    MAGIC=888

    # There has got to be a better way
    # Modify path so we can pickup my parts, regardless of cwd
    target = str((Path(__file__).parent) / "test_dir")
    if target not in sys.path:
        sys.path.append(target)
    from fred import silly

    silly()

from datetime import datetime, timedelta
import numpy as np
a = np.array([10, 13, 4])
print(a, np.diff(a))

d = np.full((3,1), np.nan)
d=np.array([1750467809.396 ,1750467912.724, 1750467896.259])
dd = np.diff(d)
print(d, dd, [datetime.fromtimestamp(s) for s in d], [timedelta(seconds=s) for s in dd])

## now with missing
# a[2] = np.nan
# ad = np.diff(a)
# print(f"a = {a}, diff = {ad}, mean diff = {np.mean(ad)}, nan mean = {np.nanmean(ad)}")

d[2] = np.nan
dd = np.diff(d)
print(d, np.diff(d), [datetime.fromtimestamp(s) for s in d if np.isfinite(s)])
print(f"d = {d}, diff = {dd}, mean diff = {np.mean(dd)}, nan mean = {np.nanmean(dd)}")
