# provide a graph illustrating correlation by row.
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

x = np.arange(1, 4, 1)
y = np.arange(1, 7, 1)
z = np.stack((x, x, x), axis=1)
fig, ax = plt.subplots()
#ax.pcolormesh(x, y, z)
#plt.show()

class CellPlot:
    """A plot of cells in a table.
    """
    def __init__(self, ax:Axes, dat, title=None):
        """
        dat is a 2D array. cells with the same number will
        get the same color.
        """
        if title:
            ax.set_title(title)
        nr, nc = dat.shape
        ax.xaxis.set_label_position("top")
        ax.grid(visible=True, which="minor", color="black", linewidth=3)
        ax.xaxis.set_label_position("top")
        x0 = np.arange(nc)
        ax.set_xticks(x0, labels=(f"V{i+1}" for i in x0))
        ax.set_xticks(x0+0.5, minor=True)

        y0 = np.arange(nr)
        ax.set_yticks(y0, labels= y0+1)
        ax.set_yticks(y0+0.5, minor=True)
        ax.tick_params(labeltop=True, labelbottom=False, bottom=False, left=False)

z = np.arange(1, x.size * y.size + 1).reshape((-1, x.size), order="F")
ax.imshow(z, cmap="tab20b", aspect="auto")
CellPlot(ax, z, "Men")
ax.set_ylabel("Age Group")
plt.show()
#print(z)
