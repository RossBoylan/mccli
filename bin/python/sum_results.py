from os import listdir
from os.path import isfile,join,basename,splitext
from collections import defaultdict
import csv
import json
import matplotlib.pyplot as plt
import ntpath
import numpy as np
import re

INP_FILE_LIST = 'MC/inputs/input_data.json'
DATFILE_DIR = 'MC/results/cumulative'
INP_OUTPUTS = 'MC/input_variation/inp.txt'


def main():
	with open(INP_FILE_LIST,'r') as f:
		input_data = json.load(f)

	inp_files = input_data['inp_files']
	for inp_file_name in inp_files:
		inp_file = InpFile(inp_file_name)

		inp_file.csv_dump()

	if isfile(INP_OUTPUTS):
		with open(INP_OUTPUTS,'r') as f:
			lines = f.readlines()
			
		res = []
		for line in lines[1+len(inp_files):]:
			res.append([float(v) for v in line.split()[1:]])
		means = np.mean(np.array(res),axis=0).tolist()
		sds = np.std(np.array(res),axis=0).tolist()
		
		format_str = '{:<16}  ' + '{:<16.7f}  '*len(means)
		with open(INP_OUTPUTS,'a') as f:
			f.write(format_str.format('means', *means) + '\n')
			f.write(format_str.format('sds', *sds) + '\n')

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
	return [ atoi(c) for c in re.split('([0-9]+)', text) ]


class InpFile(object):

	def __init__(self,fname):
		self.fname = fname
		self.sim_files = self.get_sim_files()
		self.labels = list(self.sim_files[0].data_rows)

		self.data = defaultdict(list)
		self.files = defaultdict(list)
		self.aggregate_data()

	def csv_dump(self):
		for label in self.labels:
			means = self.means(label)
			sds = self.sds(label)

			try: 
				with open('MC/results/summary/ageranges_{}.csv'.format(label), 'a', newline='') as fp:
				    a = csv.writer(fp, delimiter=',')
				    a.writerow(['File', 'Simulation Number'] + self.sim_files[0].headers)
				    a.writerow([self.fname, 'Mean'] + means.tolist())
				    a.writerow([self.fname, 'Standard Deviation'] + sds.tolist())
				    for file_name, data in zip(self.files[label],self.data[label]):
				    	prefix,sim_number = file_name.split('_')
				    	a.writerow([self.fname, sim_number] + data.tolist())
			except:
				with open('MC/results/summary/ageranges_{}.csv'.format(label), 'ab') as fp:
				    a = csv.writer(fp, delimiter=',')
				    a.writerow(['File', 'Simulation Number'] + self.sim_files[0].headers)
				    a.writerow([self.fname, 'Mean'] + means.tolist())
				    a.writerow([self.fname, 'Standard Deviation'] + sds.tolist())
				    for file_name, data in zip(self.files[label],self.data[label]):
				    	prefix,sim_number = file_name.split('_')
				    	a.writerow([self.fname, sim_number] + data.tolist())

	def plot(self,col,label):
		plt.hist(np.array(self.data[label])[:,0])
		plt.show()

	def means(self,label):
		return np.mean(self.data[label],axis=0)

	def sds(self,label):
		return np.std(self.data[label],axis=0)

	def aggregate_data(self):
		for label in self.labels:
			for sim_file in self.sim_files:
				self.data[label].append(np.array(sim_file.data_rows[label]))
				self.files[label].append(sim_file.base_filename)


	def includes_file(self,f):
		return isfile(join(DATFILE_DIR,f)) and f.startswith(self.fname)

	def get_sim_files(self):
		sim_file_names = [f for f in listdir(DATFILE_DIR) if self.includes_file(f)]
		sim_file_names.sort(key=natural_keys)

		sim_files = []
		for sim_file_name in sim_file_names:
			sim_files.append(SimFile(sim_file_name))

		return sim_files


class SimFile(object):

	header_line = 3

	def __init__(self,file):
		self.file_name = file
		self.headers = []
		self.data_rows = {}
		self.get_sim_lines()
		self.base_filename = splitext(ntpath.basename(self.file_name))[0]
		

	def get_sim_lines(self):
		with open(join(DATFILE_DIR,self.file_name),'r') as f:
			lines = f.read().splitlines()

		self.headers = lines[self.header_line].split()

		self.data_rows = {line.split()[0] : [int(float(datum)) for datum in line.split()[1:]] for line in lines[self.header_line + 1:] }	

	def get_male_cols(self):
		pattern = re.compile('M[0-9].*')	
		return [i for i,header in enumerate(self.headers) if pattern.match(header)]

	def get_female_cols(self):
		pattern = re.compile('F[0-9].*')	
		return [i for i,header in enumerate(self.headers) if pattern.match(header)]

	def get_male_total(self):
		for line in self.male_cols:
			pass

	def get_totals(self):
		pass

if __name__ == '__main__':
	# debug
	#os.chdir(r"C:\Users\rdboylan\Documents\KBD\A. Mod91_mexPA_MCs_06.28.2019")
	main()