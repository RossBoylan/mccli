#!/usr/bin/env python
from __future__ import print_function
from operator import add
import argparse
import csv
import collections
import json
import numpy as np
import os.path
import re
import sys
from randomgen import Generator, PCG64


def main():
	global RG  # the random generator
	args = parse_args()
	seed = args.seed
	if seed:
		RG = Generator(PCG64(seed, args.iteration, mode="sequence"))
	else:
		RG = Generator(PCG64(mode="sequence"))

	input_data = get_input_data()

	dat_files = input_data['dat_files']
	for datfiledata in dat_files:
		datfile = DatFile(datfiledata,RG)
		if not args.zero_run:
			datfile.vary()
			datfile.save_raw_data()
		datfile.print_mc()

	inp_files = input_data['inp_files']
	for i, fname in enumerate(inp_files):
		inpfile = InpFile(fname)
		if i == 0 and args.save:
			if args.zero_run:
				inpfile.effects.print_labels()
			else:
				inpfile.effects.print_data()

		if args.zero_run:
				inpfile.count_varied_lines()

		if not args.zero_run:
			inpfile.vary()
		inpfile.print_mc()


def parse_args():
	parser = argparse.ArgumentParser()
	inpgroup = parser.add_argument_group('.inp files, -r is default')
	mut_group = inpgroup.add_mutually_exclusive_group()
	mut_group.add_argument('--list','-l',dest='prefixes', nargs='+', type=str,
							help='list of .inp file prefixes')
	mut_group.add_argument('--readfile','-r',dest='prefix_file',
							action='store_const', const='MC/inputs/inp_files.txt',
							help='determine .inp files to be varied from listings in '
							'MC/inputs/inp_files.txt',default='MC/inputs/inp_files.txt (default)')
	options_group = parser.add_argument_group('options')
	options_group.add_argument('--zero_run','-z',help='test simulation '
							   'with no variation',action='store_true')
	options_group.add_argument('--save','-s',help='save montecarlo results to modfile',
							action='store_true')
	options_group.add_argument('--iteration', '-i', type=int, help='Which simulation this is.')
	options_group.add_argument('--seed', type=int, help="This seed and the iteration number pick a random number stream")
	return parser.parse_args()


def get_input_data():
	fname = 'MC/inputs/input_data.json'
	if os.path.isfile(fname):
		with open(fname) as data_file:
			return json.load(data_file)
	else:
		print('Error: could not find inputs file at {}'.format(fname))
		sys.exit(1)

def read_lines(fname):
	try:
		with open(fname,'r') as f:
			return f.read().splitlines()
	except IOError:
		print('Cannot find file: {}'.format(fname))
		sys.exit(1)

def is_data_line(line):
	return len(line) > 0 and str.isdigit(line[0][0])


def invalid_distribution_error(dist_name):
	print('Invalid distribution: ' + dist_name)
	print('Valid distributions include: Normal, LogNormal, Beta, and Gamma')
	sys.exit(1)


def is_number(s):
	try:
		float(s)
		return True
	except ValueError:
		return False


class VFile(object):
	"""Base class for files to be varied

	Attr:
		mc_file: File to write varied output to
		lines: Raw lines of mc0 file
		frmt_str: String to format data lines
		save: Boolean flag - if True save variation info
	"""

	def __init__(self,fname):
		pref,ext = fname.split('.')
		self.mc_file = open(pref + '_mc.' + ext,'w')
		self.lines = read_lines(pref + '_mc0.' + ext)
		self.frmt_str = ''

	def num_lines(self):
		return len(self.lines)

	def print_mc(self):
		"""Print varied lines to  mc_file"""
		for line in self.lines:
			print(line,file=self.mc_file)
		# without the close sometimes the file is not written out
		# though it seems as if it should be anyway
		# There do not appear to be any subsequent writes to the file after this call is invoked
		self.mc_file.close()

	def vary(self):
		for line_num in range(self.num_lines()):
			self.vary_line(line_num)

	def vary_line(self,line):
		pass

	def format_line(self,out_list):
		line_format = self.lead_spaces * ' ' + len(out_list) * self.frmt_str
		return line_format.format(*out_list)

	def replace_line(self,line,line_num):
		self.lines[line_num] = line


class DatFile(VFile):
	"""Varying .dat file

	Attr:
		sdfile: SDFile object containing standard deviation information
	"""

	def __init__(self,file_data, random_generator):
		self.file_data = file_data
		self.fpath = os.path.join('modfile',file_data['filename'] + '.dat')
		VFile.__init__(self,self.fpath)
		self.sdfile = SDFile(file_data,self.lines, random_generator)
		self.frmt_str = ''
		self.lead_spaces = 0
		self.set_format()
		self.data_vec = []

	def save_raw_data(self):
		with open('MC/input_variation/dat_files/' + self.file_data['filename'] + '.csv', 'a',newline='') as totals_file:
			print(self.data_vec)
			writer = csv.writer(totals_file)
			writer.writerow(self.data_vec)

	def vary_line(self,line_num):
		means = self.lines[line_num].split()
		if is_data_line(means):
			varied = self.sdfile.get_variation(line_num)
			if 'sumToOne' in self.file_data and self.file_data['sumToOne']:
				varied[:] = [v / sum(varied) for v in varied]

			self.data_vec = varied
			formatted = self.format_line(varied)
			self.replace_line(formatted,line_num)

	def set_format(self):
		"""Set 'frmt_str' based on last line of dat file"""
		self.lead_spaces = self.file_data['format']['leading_spaces']
		num_spaces = self.file_data['format']['mid_spaces']
		num_format = self.file_data['format']['num_format']
		self.frmt_str = ('{{:<{0}}}{1}'.format(num_format,' ' * int(num_spaces)))


class SDFile(object):
	"""Standard deviations for .dat files

	Same format as .dat file
	Attr:
		file_data:	model specification
		lines: Raw lines in file
		mean_lines: values from the means file
		block_nums: List of block indices for each data line
		num_blocks: Integer number of blocks in file
		RG a <RandomGenerator> to use
		cols:	Number of columns of data

	Internal Use only
		_do_line:	a function taking a line number as argument
			Process that line appropriately, returning random values

		_do_dist:	a function taking quantiles (only for correlated variables),
					means and sds as arguments.  Called by _do_line.
					returns appropriate "random" values.


	This can produce random variables that are correlated by block or row.
	If the correlation is by block, the correlation is actually across
	lines aka rows that are members of the same block.  The values in different 
	columns, returned by _do_lines, are uncorrelated with eah other within a row.
	In this scenario, different rows usually correspond to different ages.  There may
	be 2 such groups for male and female; in those cases the men and women are also correlated.

	If the correlation is by row, values within the same row *are* correlated with each other.

	The correlation, if present, is always as perfect as it can be, in that random variables
	with different means and sds will have different values, but the values will all be at the same
	percentile of the distribution.  For normal this produces a conventional (Pearson) correlation of 1,
	but for other distributions the value will be lower because it is impossible to achieve 1.0.
	In that case, the values are completely dependent, but not linearly dependent.

	
	"""

	def __init__(self, file_data, mean_lines, random_generator):
		self.file_data = file_data
		self.RG = random_generator
		sdpath = os.path.join('modfile',file_data['filename'] + '_sd.dat')
		self.mean_lines = mean_lines
		self.lines = read_lines(sdpath)
		self.block_nums = [-1] * len(self.lines)
		self.cols = self._count_cols()
		self.row_offset = 1
		if 'rowLabels' in file_data and file_data['rowLabels'] == False:
			self.row_offset = 0

		if 'distribution' in self.file_data and \
			self.file_data['distribution'] in ('beta', 'lognormal'):
			self._basic_generator = self.RG.random   # uniform [0, 1]
		else:
			self._basic_generator = self.RG.standard_normal

		if file_data['correlation'] == 'block':
			self._set_block_nums()
			self._do_line = self.vary_by_block
			dims = (file_data['blocksPerGroup'], self.cols)
			self._rnd = self._basic_generator(dims)
			self._set_correlated_distribution()
		elif file_data['correlation'] == 'row':
			self._rnd = self._basic_generator()
			# note _rnd will be changed as we advance through the file
			self._do_line = self.vary_by_row
			self._set_correlated_distribution()
		else:
			self._do_line = self.vary_individually
			self._set_uncorrelated_distribution()

	def _set_correlated_distribution(self):
		"Establish right function to call for each line"
		if 'distribution' in self.file_data:
			distn = self.file_data['distribution']
			if distn == 'beta':
				self._do_dist = self._correlated_beta
				return
			elif distn == 'lognormal':
				self._do_dist = self._correlated_lognormal
				return
			elif distn != 'normal':
				raise ValueError("Unknow distribution type {}".format(distn))
		# normal is the default
		self._do_dist = self._correlated_normal

	def _set_uncorrelated_distribution(self):
		"Establish right function to call for each line when all values are independent"
		if 'distribution' in self.file_data:
			distn = self.file_data['distribution']
			if distn == 'beta':
				self._do_dist = self._rand_beta
				return
			elif distn == 'lognormal':
				self._do_dist = self._rand_lognormal
				return
			elif distn != 'normal':
				raise ValueError("Unknow distribution type {}".format(distn))
		# normal is the default
		self._do_dist = self._rand_normal

	def _count_cols(self):
		"""Get number of data columns"""
		for line in self.lines:
			if is_data_line(line.split()):
				return len(line.split()) - 1

	def _set_block_nums(self):
		"""Set num_blocks, block_nums"""
		n_line = 0
		for i,line in enumerate(self.lines):
			if is_data_line(line.split()):
				self.block_nums[i] = n_line // 6
				n_line += 1
				self.num_blocks = n_line // 6

	def get_block_num(self,line_num):
		return self.block_nums[line_num] % self.file_data['blocksPerGroup']


	def _correlated_normal(self, e, means, sds):
		"""Return <np.array> of perfectly correlated normals.

		e is an error term, or a vector of error terms, from
		the standard normal.
		means and sds are the means and standard deviations
		of the distributions from which we draw.
		"""
		return means + e*sds

	def _rand_normal(self, means, sds):
		"""Return <np.array> of random variables drawn from normals
		with indicated means and sds.
		"""
		return self.RG.normal(means, sds)

	def _correlated_lognormal(self, q, means, sds):
		"""Return <np.array> of correlated or uncorrelated log-normals.

		q are the quantiles to use.  If None, generate independent random variables.

		Each individual element has mean and sd as given in input vectors.
		q must either be the same size as those vectors or a single number.

		The input means and sds refer to the lognormal variable, not to
		the related normal variable.  This function derives appropriate
		parameters for the lognormal parameterized in terms of mu and
		sigma, which do refer to the related normal variable.

		Formulae for translation from
		https://en.wikipedia.org/wiki/Log-normal_distribution#Alternative_parameterizations
		"""
		f = 1.0 + np.power(sds/means, 2)
		mu = np.log(means/np.sqrt(f))
		sigma = np.sqrt(np.log(f))
		res = empty_like(means)
		mask = (sigma>0.0)
		# scipy docs say if log(Y) has mean mu and sd sigma then
		# use s = sigma and scale = exp(mu)
		if q is None:
			res[mask] = self.RG.lognormal(mu[mask], sigma[mask])
		else:
			res[mask] = stats.lognorm.ppf(q[mask], s = sigma[mask], scale = np.exp(mu[mask]))
		# It seems ~x is same as np.logical_not(x) but I can't find that documented anywhere.
		mask = np.logical_not(mask)
		# if sd=0 use original mean
		res[mask] = means[mask]
		return res

	def _rand_lognormal(self, means, sds):
		return self._corr_lognormal(None, means, sds)

	def _correlated_beta(self, q, means, sds):
		"""Return <np.array> of correlated or uncorrelated beta random variables.

		Means in [-1, 0) are permitted and interpreted as negative of the 
		corresponding value from a beta with abs(means).

		If the mean is 0 or the sd<=0 the generated random variable is
		always the mean.

		q are the quantiles to use.  If None, generate uncorrelated random variables.
		Each individual element has mean and sd as given in input vectors.
		q must either be the same size as those vectors or a single number.
		"""
		res = empty_like(means)
		# mean of 0 should imply sd of 0
		mask = (means == 0.0) | (sds <= 0.0)
		res[mask] = means[mask]
		mask = np.logical_not(mask)
		switch = (means < 0.0)
		means = np.abs(means)
		# to avoid division by zero must remove masked elements
		ms = means[mask]
		ss = sds[mask]
		alpha = ((1 - ms) / ss ** 2 - (1 / ms)) * ms ** 2
		beta = alpha * (1 / ms - 1)
		if q is None:
			res[mask] = self.RG.beta(alpha, beta)
		else:
			res[mask] = stats.beta.ppf(q[mask], a = alpha, b = beta )
		res[switch] = - res[switch]
		return res

	def _rand_beta(self, means, sds):
		"return random values from the beta distribution"
		return self._correlated_beta(None, means, sds)


	def get_variation(self,line_num):
		"""Returns list of variations for line 'line_num'"""
		return self._do_line(line_num)


	def vary_individually(self,line_num):
		sds = [float(sd) for sd in self.lines[line_num].split()[self.row_offset:]]
		means = [float(mean) for mean in self.mean_lines[line_num].split()[self.row_offset:]]
		return self._do_dist(means, sds)


	def vary_by_row(self,line_num):		
		rnd = self._rnd
		# prepare for next call
		self._rnd = self._basic_generator()
		sds = [float(sd) for sd in self.lines[line_num].split()[self.row_offset:]]
		means = [float(mean) for mean in self.mean_lines[line_num].split()[self.row_offset:]]
		return self._do_dist(rnd, means, sds)

	def vary_by_block(self,line_num):
		"""return <np.array> of parameters for indicated line
		All rows within a column in the same block will return the same quantile.

		It might be a good idea to sanity check the inputs, though it's a little silly to do
		for each simulation.

		self._rnd are standard normal deviates for normal distributions and 
		quantiles in [0, 1] for other distributions.
		"""
		block_num = self.get_block_num(line_num)
		sds = np.array([float(sd) for sd in self.lines[line_num].split()[self.row_offset:]])
		means = np.array([float(mean) for mean in self.mean_lines[line_num].split()[self.row_offset:]])
		return self._do_dist(self._rnd[block_num,], means, sds)



class InpFile(VFile):
	"""Varying .inp file

	Attr:
		effects: Effects object containing variation data
	"""

	def __init__(self,fname):
		VFile.__init__(self,fname + '.inp')
		self.effects = Effects()
		self.frmt_str = '{:<8.6f}'
		self.lead_spaces = 0
		self.fileprefix = fname

	def vary_line(self,line_num):
		line = self.lines[line_num]

		line_data = self.effects.get_data(line)

		if line_data != None:
			varied,add_mean = line_data
			mean = float(line.split()[0])

			if add_mean:
				varied = mean + mean * varied

			formatted = self.format_line([varied])
			self.replace_line(formatted,line_num)

	def count_varied_lines(self):
		varied_line_counts = self.effects.key_matches(self.lines)
		counts = [value for key,value in varied_line_counts.items()]
		format_str = '{:<16}  ' * (len(counts) + 1)
		if len(counts) > 0:
			self.effects.save_write(format_str.format(self.fileprefix,*counts) + '\n')



class Effects(object):
	"""Contains data from inp_distribution.txt

	Used to vary .inp file.
	inp_distribution.txt format can be found on github.com/ecfairle/CHDMOD
	Attr:
		key_result_pairs: Dict of key->data pairs - where
			key_result_pairs[key][0]' replaces the value on the current line
			and 'key_result_pairs[key][1]' indicates whether to add the mean
			on the current line
		lines: Raw lines of inp_distribution.txt
	"""

	save_file_name = 'MC\input_variation\inp.txt'

	def __init__(self):
		self.key_result_pairs = collections.OrderedDict()
		self.lines = []
		self._read_lines()
		self._generate_pairs()

	def print_data(self):
		vals = [data[0] for key,data in self.key_result_pairs.items()]
		format_str = '{:<16.7f}  ' * len(vals)
		if len(vals) > 0:
			self.save_write(format_str.format(*vals) + '\n')

	def print_labels(self):
		labels = [key for key in self.key_result_pairs]
		format_str = '{:<16}  ' * (len(labels) + 1)
		if len(labels) > 0:
			self.save_write(format_str.format('simulation #',*labels) + '\n')

	def save_write(self,string):
		with open(self.save_file_name,'a') as f:
			f.write(string)

	def _read_lines(self):
		fname = 'MC/inputs/inp_distribution.txt'
		file_lines = []
		if os.path.isfile(fname):
			file_lines = read_lines(fname)
		for line in file_lines:
			data = line.split('#')[0].strip()
			if len(data) != 0:
				self.lines.append(data)

	def num_lines(self):
		return len(self.lines)

	def _generate_pairs(self):
		# ignore everything after '#'
		line_num = 0
		while line_num < self.num_lines():
			key,num_lines = self.lines[line_num].split(',')
			num_lines = int(num_lines)

			component_lines = self.lines[line_num + 1:line_num + num_lines + 1]
			line_num += num_lines + 1  # skip past component lines

			self.key_result_pairs[key] = self._sum_components(component_lines)

	def _sum_components(self,component_lines):
		"""Sum samples from each component distribution"""
		s = 0
		add_mean = False
		for line in component_lines:
			component = Component(line)
			s += component.sample()
			add_mean = component.depends_on_mean_line()

		if add_mean and len(component_lines) != 1:
			print('error: the MEAN placeholder only makes sense when '
				'the label contains a single component')
			sys.exit(1)

		return s, add_mean

	def get_data(self,line):
		"""Return varied value appropriate for line, else None"""
		for key,varied in self.key_result_pairs.items():
			if line.find(key) != -1:
				self._test_for_repeats(key,line)
				return varied
		return None

	def key_matches(self,lines):
		matches_by_key = collections.OrderedDict()
		for key in self.key_result_pairs:
			matches_by_key[key] = 0
		for line in lines:
			for key,varied in self.key_result_pairs.items():
				if line.find(key) != -1:
					matches_by_key[key]+=1
		return matches_by_key

	def _test_for_repeats(self,key,line):
		"""Make only one key found in line"""
		other_keys = [k for k in self.key_result_pairs.keys() if k != key]
		if any(line.find(k) != -1 for k in other_keys):
			print('keys overlap -- keys must be unique to'
								 'achieve desired behavior')
			sys.exit(1)


class Component(object):

	group_state = {}

	def __init__(self,data_line):
		parts = data_line.split(',')
		parts[0] = parts[0].strip()

		self.group = None
		if self.set_group(parts[0]):
			parts = parts[1:]

		# if first listing (after group) is a number, assume normal distribution
		if is_number(parts[0]) or parts[0].upper() == 'MEAN':
			self.set_dist('norm')
			params = parts
		else:
			self.set_dist(parts[0])
			params = parts[1:]

		if self.name == 'NORMAL' and params[0].upper() == 'MEAN':
			self.fn = RG.randn
			self.params = float(params[1])
		else:
			self.params = [float(p) for p in params[:self.num_params]]

		bounds = params[self.num_params:]
		self.lower_bound = self.get_lower(bounds)
		self.upper_bound = self.get_upper(bounds)

	def depends_on_mean_line(self):
		return self.fn == RG.randn

	def set_group(self,group_str):
		"""Sets group for component, returns True if successful"""
		# here I get state from new RG.  Motivation for using it remains
		# obscure.
		match = re.search(r'g=(.+)',group_str)
		if match is not None:
			self.group = match.group(1).strip()
			if not self.group in self.group_state:
				self.group_state[self.group] = RG.state
				# RB: Why isn't this the same for every group?
			return True
		return False

	def get_lower(self,bounds):
		try:
			lower_bound = bounds[0]
			return float(lower_bound)
		except (ValueError,IndexError):
			return float("-inf")

	def get_upper(self,bounds):
		try:
			upper_bound = bounds[1]
			return float(upper_bound)
		except (ValueError,IndexError):
			return float("inf")

	def set_dist(self,dist_name):
		dist_name = dist_name.lower()
		if dist_name == 'norm' or dist_name == 'normal' or dist_name == '':
			self.name = 'NORMAL'
			self.fn = RG.normal
			self.num_params = 2

		elif dist_name == 'lognormal':
			self.name = 'LOGNORMAL'
			self.fn = RG.lognormal
			self.num_params = 2

		elif dist_name == 'beta' or dist_name == 'b':
			self.name = 'BETA'
			self.fn = RG.beta
			self.num_params = 2

		elif dist_name == 'gamma':
			self.name = 'GAMMA'
			self.fn = RG.gamma
			self.num_params = 2

		else:
			invalid_distribution_error(dist_name)

	def sample(self):
		if self.group:
			RG.state = self.group_state[self.group]

		if self.fn == RG.randn:
			val = self.fn() * self.params
		else:
			val = self.fn(*self.params)

		return self.threshold(val)

	def threshold(self,val):
		if val > self.upper_bound:
			return self.upper_bound
		elif val < self.lower_bound:
			return self.lower_bound
		else:
			return val


if __name__ == '__main__':
	main()
