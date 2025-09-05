# provide a graph illustrating correlation by row.
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

x = np.arange(1, 4, 1)
y = np.arange(1, 7, 1)
z = np.stack((x, x, x), axis=1)
fig, (ax1, ax2) = plt.subplots(2, 1)
#ax.pcolormesh(x, y, z)
#plt.show()

class CellPlot:
    """A plot of cells in a table.
    """
    def __init__(self, ax:Axes, dat, title=None, firstV=1):
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
        ax.set_xticks(x0, labels=(f"V{i+firstV}" for i in x0))
        ax.set_xticks(np.hstack((x0, nc))-0.5, minor=True)

        y0 = np.arange(nr)
        ax.set_yticks(y0, labels= y0+1)
        ax.set_yticks(np.hstack((y0, nr))-0.5, minor=True)
        ax.tick_params(labeltop=True, labelbottom=False, bottom=False, left=False)
        ax.tick_params(which="minor", top=False, bottom=False,
                       left=False, right=False)

class AgePlot(CellPlot):
    "adds a label to the vertical axis"
    def __init__(self, ax:Axes, dat, title=None, firstV=1):
        CellPlot.__init__(self, ax, dat, title=title, firstV=firstV)
        ax.set_ylabel("Age Group")

z = np.arange(1, x.size * y.size + 1).reshape((-1, x.size), order="F")

def simple_block():
    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1.imshow(z, cmap="tab20b", aspect="auto")
    AgePlot(ax1, z, title="Men")
    ax2.imshow(z, cmap="tab20b", aspect="auto")
    AgePlot(ax2, z, title="Women")


def block2():
    fig, ((ax1, ax3), (ax2, ax4)) = plt.subplots(2, 2)
    ax1.imshow(z, cmap="tab20b", aspect="auto")
    AgePlot(ax1, z, title="Men")
    ax2.imshow(z, cmap="tab20", aspect="auto")
    AgePlot(ax2, z, firstV=11)
    ax3.imshow(z, cmap="tab20b", aspect="auto")
    AgePlot(ax3, z, title="Women")
    ax4.imshow(z, cmap="tab20", aspect="auto")
    AgePlot(ax4, z, firstV=11)

block2()
plt.show()
#print(z)
