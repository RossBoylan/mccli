import matplotlib.pyplot as plt
import numpy as np
import pandas
import sys
import os

PLOT_DIR = "MC/results/plots"

basename = sys.argv[1]
index = int(sys.argv[2])
fname = 'MC/input_variation/dat_files/{}.csv'.format(basename)
try:
	data = pandas.read_csv(fname, header=None)
except IOError as e:
	print("File {} does not exist".format(fname))
	sys.exit()

data_col = data[index]
plt.hist(data_col.tolist())
fig = plt.gcf()
plt.show()
if not os.path.isdir(PLOT_DIR):
	os.mkdir(PLOT_DIR)

im_file = os.path.join(PLOT_DIR, "{}_{}.png".format(basename,index))
if not os.path.isfile(im_file):
	fig.savefig(im_file, figsize=(1000,1000))
	print("Plot saved to {}".format(im_file))
else:
	print("Plot already exists at {}".format(im_file))