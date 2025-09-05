# provide a graph illustrating correlation by row.
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

x = np.arange(1, 4, 1)
y = np.arange(1, 7, 1)
z = np.arange(1, x.size * y.size + 1).reshape((-1, x.size), order="F")


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



def byrow(fname=None):
    fig, ax1 = plt.subplots(1)
    x = np.arange(1, 5, 1)
    y = np.arange(1, 4, 1)
    z = np.stack((x, x, x), axis=1)
    fig.suptitle("Correlation by row")
    ax1.imshow(z, cmap="Set1", aspect="auto")
    CellPlot(ax1, z)
    if fname:
        fig.savefig(fname)

def simple_block(fname=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(3, 7))
    fig.suptitle("Correlation by block")
    ax1.imshow(z, cmap="tab20b", aspect="auto")
    AgePlot(ax1, z, title="Men")
    ax2.imshow(z, cmap="tab20b", aspect="auto")
    AgePlot(ax2, z, title="Women")
    if fname:
        fig.savefig(fname)

def block2(fname=None):
    fig, ((ax1, ax3), (ax2, ax4)) = plt.subplots(2, 2, figsize=(7, 6.5))
    fig.suptitle("Correlation by block with 2 blocks per group")
    ax1.imshow(z, cmap="tab20b", aspect="auto")
    AgePlot(ax1, z, title="Men")
    ax2.imshow(z, cmap="tab20", aspect="auto")
    AgePlot(ax2, z, firstV=11)
    ax3.imshow(z, cmap="tab20b", aspect="auto")
    AgePlot(ax3, z, title="Women")
    ax4.imshow(z, cmap="tab20", aspect="auto")
    AgePlot(ax4, z, firstV=11)
    if fname:
        fig.savefig(fname)

byrow("corr-row.svg")
simple_block("corr-block.svg")
block2("corr-block2.svg")
#plt.show()
#print(z)
