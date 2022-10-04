#!/usr/bin/env python
from __future__ import print_function

import argparse
import csv
import collections
import json
import numpy as np
from pathlib import Path
from scipy import stats
import os.path
import re
import sys

def main():
	global RG  # the random generator
	args = parse_args()
	seed = args.seed
	#print(f"montecarlo.py {args.iteration} called.")
	if seed:
		# https://github.com/numpy/numpy/issues/22119#issuecomment-1213579174
		# recommends the following strategy
		RG = np.random.default_rng([args.iteration, seed])
	else:
		# While I do have the iteration, if I use it for a seed it will block
		# use of system randomness, which is probably greater.
		# However, this may hang up if there is not enough entropy
		# available from the system.
		# Possible alternative: combine iteration with a fixed but complex seed.
		RG = np.random.default_rng()

	# default_rng is PCG64 in NumPy 1.23.  Might consider using PCG64DXSM for even
	# more robust parallel independence.

	input_data = get_input_data()

	dat_files = input_data['dat_files']
	for datfiledata in dat_files:
		datfile = DatFile(datfiledata, RG)
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
	#print(f"montecarlo.py {args.iteration} finished.")


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


def get_input_data(ifname=None, ifile=None):
	if ifile is None:
		if ifname is None:
			ifname = 'MC/inputs/input_data.json'
		if os.path.isfile(ifname):
			with open(ifname) as data_file:
				return json.load(data_file)
		else:
			print('Error: could not find inputs file at {}'.format(ifname))
			sys.exit(1)
	else:
		return json.load(ifile)

def read_lines(fname=None, fin=None):
	""" Read lines from a file given by name or file-like object
	Ordinarily called read_lines('myfile'), in which case the argument is assigned
	to fname.  fname can be any pathlike object.
	Alternately called with
	read_lines(fin=myfile) where myfile is any readable stream
		the call will close fin at the end.

	fin may not have a file name and so we do not catch errors in it.
	fname is ignored if fin is present.

	Returns list of strings with each line of the file.
	"""
	if fin:
		lines = fin.read().splitlines()
		fin.close()
		return lines
	# fname handling below here
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

def mean_to_native(dist:str, means, sds, check=True):
	"""
	Get the native distribution parameters implied by indicated means and 
	standard deviations.

	Returns a 2 element tuple of the first and second parameters.
	If each parameter has a single value, each element of the return value
	will be a float; otherwise each will be an np.array.

	means and sds may be single numbers or any iterables of the same
	length.  The returned np.array's will have the same length.

	If return value is (p1, p2) then p1[i], p2[i] are the parameters 
	implied by means[i], sds[i].

	May raise a ValueError for unknown distributions or illegal parameters.
	Set check=False to skip sanity checks on input parameters.

	Recommendation: Always call this function, not the functions it calls,
	even if you know what the distribution is.
	"""
	means = np.asarray(means)
	sds = np.asarray(sds)
	if check:
		if sds.min() < 0:
			raise ValueError("Negative standard deviation")
		if means.size != sds.size:
			raise ValueError("means and sds must be same length")
	dist = dist.lower()
	if dist == "normal":
		r = (means, sds)
	elif dist == "beta":
		r = beta_native(means, sds, check)
	elif dist == "lognormal":
		r = lognormal_native(means, sds, check)
	elif dist == "gamma":
		r = gamma_native(means, sds, check)
	else:
		raise ValueError("Unknow distribution type {}".format(dist))
	if r[0].ndim == 0:
		# In this case each component is an np.array with 0
		# dimensions.  It can not be addressed by x[0], so
		# there seems no point in treating it as np.array
		return (float(r[0]), float(r[1]))
	else:
		return r

def lognormal_native(means:np.array, sds:np.array, check=True):
		"""
		The input means and sds refer to the lognormal variable, not to
		the related normal variable.  This function derives appropriate
		parameters for the lognormal parameterized in terms of mu and
		sigma, which do refer to the related normal variable.

		Formulae for translation from
		https://en.wikipedia.org/wiki/Log-normal_distribution#Alternative_parameterizations

		This only returns rows for sane values of the inputs.
		A mean of 0 isn't really sane, but we allow it, assuming the sd will be <=0, i.e.,
		the goal is to zero something out.
		"""
		if check and means.min() < 0.0:
			raise ValueError("Mean of LogNormal < 0")
		mask = (sds <= 0)
		if np.any(mask):
			# WARNING: next 2 lines require NumPy 1.19+
			sds = np.delete(sds, mask)
			means = np.delete(means, mask)
		f = 1.0 + np.power(sds/means, 2)
		mu = np.log(means/np.sqrt(f))
		sigma = np.sqrt(np.log(f))
		return (mu, sigma)

def beta_native(means:np.array, sds:np.array, check=True):
	"""
	Return alpha and beta that give means and sds.
	E.g., https://en.wikipedia.org/wiki/Beta_distribution#Mean_and_variance,
	though the formulae here are slightly transformed.
	"""
	if check:
		if means.max()>1.0:
			raise ValueError("mean of Beta > 1")
		if means.min()<0.0:
			raise ValueError("mean of Beta < 0")
		if sds**2 > means*(1-means):
			raise ValueError("Var Beta > mu(1-mu)")
	alpha = ((1 - means) / sds ** 2 - (1 / means)) * means ** 2
	beta = alpha * (1 / means - 1)
	return (alpha, beta)

def gamma_native(means:np.array, sds:np.array, check=True):
	"""
	Return parameters of Gamma distribution that
	give requested means and sds.
	https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.gamma.html
	indicates parameterization use shape and scale (k and theta)
	https://en.wikipedia.org/wiki/Gamma_distribution gives
	mean = k theta
	var = k theta^2
	From which we derive the following
	"""
	if check and means.min() <= 0.0:
		raise ValueError("Gamma with mean <= 0")
	v = sds**2
	theta = v/means
	k = means**2/v
	return (k, theta)

class VFile(object):
	"""Base class for files to be varied

	Attr:
		mc_file: File to write varied output to
		lines: Raw lines of mc0 file
		frmt_str: String to format data lines
		save: Boolean flag - if True save variation info
	"""

	def __init__(self, fname=None, ifname=None, ifile=None, ofname=None, ofile=None):
		"""
		Standard Call: VFile(f) where f is a string representing the base path
			E.g., "b.dat" which implies "b_mc0.dat" has inputs and "b_mc.dat" gets results

		Alternatives: VFile(ifname="b_mc0.dat", ofname="b_mc.dat")
		    You explicitly name the input and output files.
			ifname and ofname, but not fname, can be any pathlike object,
			and may specify a full or relative path, not just a filename. 

		VFile(ifile=if, ofile=of)
			Where if and of are stream or filelike objects for input and output.

		Options can be mixed and matched, file arguments are preferred, then i/ofnames, 
			and finally fname.
		Note that if you do not use fname you must specify the _mc part yourself.
		"""
		if fname:
			pref,ext = fname.split('.')
			if ifname is None:
				ifname = pref + '_mc0.' + ext
			if ofname is None:
				ofname = pref + '_mc.' + ext
		self.ifname = ifname
		self.ofname = ofname
		if ifile:
			self.ifile = ifile
		elif ifname:
			self.ifile = open(self.ifname, "rt")
		if ofile:
			self.mc_file = ofile
		elif ofname:
			self.mc_file = open(ofname,'w')
		self.lines = read_lines(self.ifname, fin=self.ifile)
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

	def __init__(self,file_data, random_generator, ifname=None, ifile=None,
		ofname=None, ofile=None,
		sdifname=None, sdifile=None):
		"""
		file_data  JSON object with specification for this variable
		random_generator random generator to use

		ifile optional input stream with the main .dat information
		ifname optional path-like object with the main .dat information
			Only used if ifile is None.
			Ordinarily omitted and given program default

		ofile
		ofname
			The output analogs of ifile, ifname

		sdifile optional input stream in .dat format but with standard deviations
		sdifname optional Path-like object with the location of the sd file
			Only used if sdifile is None
			Ordinarily omitted and given program default
		"""
		self.file_data = file_data
		if ifile is None:
			if ifname is None:
				ifname = os.path.join('modfile',file_data['filename'] + '_mc0.dat')
		if ofile is None:
			if ofname is None:
				ofname = os.path.join('modfile',file_data['filename'] + '_mc.dat')
		self._ifname = ifname
		self._ifile = ifile
		VFile.__init__(self, ifname = ifname, ifile = ifile, ofname=ofname, ofile=ofile)

		self.sdfile = SDFile(file_data,self.lines, random_generator, sdifname, sdifile)
		self.frmt_str = ''
		self.lead_spaces = 0
		self.set_format()
		self.data_vec = []

	def save_raw_data(self):
		with open('MC/input_variation/dat_files/' + self.file_data['filename'] + '.csv', 'a',newline='') as totals_file:
			#print(self.data_vec)
			writer = csv.writer(totals_file)
			writer.writerow(self.data_vec)

	def vary_line(self,line_num):
		means = self.lines[line_num].split()
		if is_data_line(means):
			varied = self.sdfile.get_variation(line_num)
			if 'sumToOne' in self.file_data and self.file_data['sumToOne']:
				varied[:] = [v / sum(varied) for v in varied]

			self.data_vec.append(varied)
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
	columns, returned by _do_lines, are uncorrelated with each other within a row.
	In this scenario, different rows usually correspond to different ages.  There may
	be 2 such groups for male and female; in those cases the men and women are also correlated.

	If the correlation is by row, values within the same row *are* correlated with each other.

	The correlation, if present, is always as perfect as it can be, in that random variables
	with different means and sds will have different values, but the values will all be at the same
	percentile of the distribution.  For normal this produces a conventional (Pearson) correlation of 1,
	but for other distributions the value will be lower because it is impossible to achieve 1.0.
	In that case, the values are completely dependent, but not linearly dependent.

	
	"""

	def __init__(self, file_data, mean_lines, random_generator, ifname=None, ifile=None):
		self.file_data = file_data
		self.RG = random_generator
		if ifile is None:
			if ifname is None:
				ifname = os.path.join('modfile',file_data['filename'] + '_sd.dat')
		self._ifname = ifname
		self._ifile = ifile
		self.mean_lines = mean_lines
		self.lines = read_lines(ifname, ifile)
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
		"""
		# convert from lists, which don't support math
		means = np.array(means)
		sds = np.array(sds)
		# mu and sigma may have fewer elements than means and sds
		# since they are only returned for rows with valid means and sds
		mu, sigma = mean_to_native("lognormal", means, sds)
		res = np.empty_like(means)
		mask = (sds>0.0)  # must be sds, not sigma
		# scipy docs say if log(Y) has mean mu and sd sigma then
		# use s = sigma and scale = exp(mu)
		if q is None:
			res[mask] = self.RG.lognormal(mu, sigma)
		else:
			q0 = np.array(q, copy=False)  # q might be a single number
			if q0.size > 1:
				res[mask] = stats.lognorm.ppf(q[mask], s = sigma, scale = np.exp(mu))
			else:
				res[mask] = stats.lognorm.ppf(np.full(sum(mask), q), s = sigma, scale = np.exp(mu))
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
		res = np.empty_like(means)
		# mean of 0 should imply sd of 0
		mask = (means == 0.0) | (sds <= 0.0)
		res[mask] = means[mask]
		mask = np.logical_not(mask)
		switch = (means < 0.0)
		means = np.abs(means)
		# to avoid division by zero must remove masked elements
		ms = means[mask]
		ss = sds[mask]
		alpha, beta = mean_to_native("beta", ms, ss)
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

	def __init__(self, fname=None, ifname=None, ifile=None, ofname=None, ofile=None, effects=None):
		"""
		fname, if used, should have no suffix or _mc.
		See VFile for the other file arguments
		effects provides a way to create Effects based on custom inputs or outputs
		"""
		if fname:
			fname += '.inp'
		VFile.__init__(self, fname, ifname, ifile, ofname, ofile)
		if effects:
			self.effects = effects
		else:
			# Do NOT make this a default argument
			# Because that would share the Effects instances between
			# InpFiles.
			self.effects = Effects()
		self.frmt_str = '{:<10.8f}'
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
		lines: Raw lines of ifile or ifname
	"""

	def __init__(self, 
				ifname=Path("MC") / "inputs" / "inp_distribution.txt",
				ifile=None,
				ofname=Path("MC") / "input_variation" / "inp.txt",
				ofile=None):
		"""
		Typically this is called without arguments to get it to operate on
		the default inputs (ifname) and outputs (ofname).  Those arguments, though 
		typically strings, can be any pathlike object.

		Alternatively, one can directly provide a filelike object (or streamlike)
		as input (ifile) our output (ofile).  If present, those will be used in
		preference to ifname and ofname, though we recommend providing strings for them 
		to help understand error messages.
		"""
		self.save_file_name = ofname
		self.save_file = ofile
		self.in_file_name = ifname
		self.in_file = ifile
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
		if self.save_file:
			self.save_file.write(string)
			# not sure if I should close it
			# the else branch does, but it's easy for it
			# to reopen the file
		else:
			with open(self.save_file_name,'a') as f:
				f.write(string)

	def _read_lines(self):
		file_lines = read_lines(self.in_file_name, fin=self.in_file)
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
	"""
	Component is a single distribution, which may have an associated group.
	Several components are summed to produce a final value.

	WARNING: This is designed for a single monte-carlo iteration.  Calling it 
	multiple times will simply reproduce the original numbers because of the 
	cached state, described below.

	CAUTION: Distributions have optional max and min values; if the basic distribution produces
	values outside of the bounds, they are recoded to the bounds.  It would likely
	be better to draw from, or produce, a truncated distribution.  Currently bounds produced
	censored, not truncated, distributions.

	group_state, a class variable, holds the group-specific state of the random number
	generator, and does so persistently across different instantiations
	of Component.  set_group() sets the initial state.

	Why?  The inp_distribution file may have multiple rows
	with the same group (g=NN).  We want those rows to be strongly
	correlated, perfectly if possible.  So we reset the random number
	state each time we encounter such a group.  If the two rows have
	different distributions the correlation may be imperfect.

	CAUTION: It is not guaranteed that the same initial state will produce perfect correlation 
	between random numbers of the same type, e.g., N(2.2, 0.5) and N(10.1, 4.3).  Even less
	guaranteed are results for 2 different distribution families.  That is why
	I took a different approach for the dat files and matched quantiles; it should probably be 
	imitated here.  For now we stick with what we have.

	If we have several .inp files we are considering, this also assures
	the rows are correlated across those input files.  In this case the behavior
	described in the WARNING above is a desired feature.

	On the other hand, we assume that different groups are completely
	uncorrelated, and so each group has its own state.  
	
	Note that one must actually call the random number generator between groups for
	the state to advance.
	"""
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
			self.fn = RG.standard_normal
			self.params = float(params[1])
		else:
			self.params = [float(p) for p in params[:self.num_params]]
			self.params = mean_to_native(self.name, *self.params)

		bounds = params[self.num_params:]
		self.lower_bound = self.get_lower(bounds)
		self.upper_bound = self.get_upper(bounds)

	def depends_on_mean_line(self):
		return self.fn == RG.standard_normal

	def set_group(self,group_str):
		"""Sets group for component, returns True if successful.
		Also sets the group-specific state of the random number
		generator.
		"""
		match = re.search(r'g=(.+)',group_str)
		if match is not None:
			self.group = match.group(1).strip()
			if not self.group in self.group_state:
				self.group_state[self.group] = RG.bit_generator.state
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
			RG.bit_generator.state = self.group_state[self.group]

		if self.fn == RG.standard_normal:
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
