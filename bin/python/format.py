#!/usr/bin/env python
from __future__ import print_function

import argparse
import sys
import os.path
import re

#for debug
import os, pdb


OUTPUT_EXTENSION = '.frmt'

SECTIONS = [["NEW CHD CASES"],
			["CVD PREVALENCE - first of year"],
			["NEW INTERVENED CHD CASES"],
			["NUMBER TREATED"],
			["CHD DEATHS"],
			["CHD Deaths (Bridge)"],
			["Acute CHD Death 11-17"],
			["Acute CHD Death 1-10"],
			["Acute CHD Deaths (Bridge & DH)"],
			["Acute CHD Deaths (Bridge)"],
			["Chronic CHD Death"],
			["Non-CVD Death (DE)"],
			["DE Intervened Non-CVD Deaths"],
			["Non-CVD Death (DH)"],
			["Non-CVD Death"],
			["Total Pop (DE)"],
			["Total Pop (DH 1-10)"],
			['+',"Total Pop -- DE + (DH 1-10)",
						"Total Pop (DE)","Total Pop (DH 1-10)"],
			["Total Pop (DH 11-17)"],
			["Total DE Diabetes Pop"],
			["NEW DIABETES CASES"],
			["NEW HEART FAILURE CASES"],
			["CVD EVENTS",17],
			["Revascularization Events"],
			["CVD POPULATION DISTRIBUTION BY STATE"],
			["CVD POPULATION DISTRIBUTION BY STATE",15],
			["CVD POPULATION DISTRIBUTION BY STATE",26],
			["CVD POPULATION DISTRIBUTION BY STATE",37],
			["CVD POPULATION DISTRIBUTION BY STATE",48],
			["Total MI"],
			["Bridge MI"],
			["DH First MI (1,2,14)"],
			["First MI"],
			["DH 2nd MI (11,12,15, and dhxevt)"],
			["DH Re-MI (3-8,11-13,15)"],
			["DH MI Stroke (9,10,16,17)"],
			["TOTAL STROKE"],
			["BRIDGE STROKE"],
			["NEW INTERVENED STROKE CASES"],
			["First Stroke (DH ONLY)"],
			["STROKE DEATHS"],
			["TOTAL DEATHS"],
			["NON-CVD Costs"],
			["CHD TREATMENT COSTS"],
			["TOTAL PREVENTION COSTS"],
			["TOTAL STROKE COSTS"],
			["Total QALY"],
			["Total DH QALY"]]


def main():
	args = parse_args()

	outfile = find_outfile(args.filename)
	formatted_file = open(args.filename + OUTPUT_EXTENSION,'w')

	reformatter = Reformatter(outfile,formatted_file)

	for section_params in SECTIONS:
		if section_params[0] == '+':
			section = add_sections(reformatter,*section_params[1:])
		else:
			section = TrackedSection(*section_params)
			if section_params[0] == "NEW DIABETES CASES":
				xyzzy = 1
			reformatter.format(section)
		
		section.print_lines(formatted_file)


def add_sections(reformatter,title,*add_titles):
	first_section = TrackedSection(add_titles[0])
	reformatter.format(first_section)

	section = first_section
	section.set_title(title)

	for cur_title in add_titles[1:]:
		cur_section = TrackedSection(cur_title)
		reformatter.format(cur_section)
		section.add_lines(cur_section)

	return section


def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('filename',help='prefix of .out file to be reformatted'
							'e.g. \'base\' if the .out file is \'base.out\'')
	return parser.parse_args()


def find_outfile(file_prefix):
	if not os.path.isfile(file_prefix + '.out'):
		print('Invalid File Name: ' + file_prefix + '.out')
		print('If using mc.bat, ensure .out file is made with same prefix as inp file')
		sys.exit(1)
	return CVDOutfile(file_prefix)


class TrackedSection(object):
	"""Used to represent group of numeric data blocks denoted by 'title'

	Attr:
		title: String to look for that indicates start of block
		linesdown: Integer number of lines down to search for block after title
			--by default (linesdown=0) searches for first number-containing
			line after the title, but this isn't possible for some groups
			e.g. "CVD POPULATION DISTRIBUTION BY STATE"
		lines: List of formatted lines for group
	"""

	def __init__(self, title, linesdown=0):
		self.title = title
		self.linesdown = linesdown
		self.year_offset = 0
		self.lines = [title]
		self.num_format = ''

	def set_title(self,title):
		self.title = title
		self.lines[0] = title

	def append_line(self,str):
		self.lines.append(str)

	def add_lines(self,group):
		lines = group.lines
		for line_num,line in enumerate(lines):
			split_line = line.split()
			if str.isdigit(split_line[0][0]):
				self.add_line(split_line,line_num)

	def add_line(self,line,line_num):
			nums_to_add = line[1:]
			nums_self = self.lines[line_num].split()[1:]
			sums = []
			for a,b in zip(nums_to_add,nums_self):
				try:
					num = int(a)+int(b)
				except:
					num = round(float(a)+float(b),2)
				sums.append(num)
			sum_line = [line[0]] + sums
			self.lines[line_num] = self.num_format.format(*sum_line)

	def format_num_line(self,base_year,num_list):
		format_str = self.num_format
		cur_year = base_year + self.year_offset
		self.year_offset = self.year_offset + 1
		if len(num_list) != self.num_nums:
		    num_list = [0] * self.num_nums
		return format_str.format(cur_year,*num_list)

	def write_header(self,category_line):
		header = OutputHeader(category_line)
		formatted_topline = header.get_topline()
		formatted_categories = header.get_categories()
		self.num_nums = 12*len(header.categories)
		self.num_format = '{}     ' + '{:<18} ' * self.num_nums
		self.append_line(formatted_categories)
		self.append_line(formatted_topline)

	def print_lines(self,file):
		for line in self.lines:
			print(line,file=file)
		file.write('\n')



class OutputHeader(object):
	"""Data for header of data associated with section

	Contained in TrackedSection object

	Attr:
		categories: List of categories in containing section
	"""

	top_line= ['M35-44', 'M45-54', 'M55-64', 'M65-74', 'M75-84', 'M85-94',
	'F35-44',  'F45-54',  'F55-64',   'F65-74',  'F75-84',  'F85-94']

	def __init__(self,category_line):
		self.categories = self._parse_categories(category_line)
		self.num_categories = len(self.categories)
		self.category_format = '         ' + '{:<228}'*self.num_categories
		self.topline_format = 'Year     ' + '{:<18} '*(12*self.num_categories)

	def _parse_categories(self,category_line):
		#categories separated by at least 2 whitespace characters
		match = re.split(r'(\s\s+)',category_line.rstrip())
		#filter out categories that are empty or only whitespace
		categories = [m for m in match if len(m)>0 and m[0]!=' ']

		if categories:
			return categories
		else:  #default category
			return ['Age/Sex Breakdown']

	def get_categories(self):
		format_str = self.category_format
		return format_str.format(*self.categories)

	def get_topline(self):
		topline = self._make_topline()
		format_str = self.topline_format
		return format_str.format(*topline)

	def _make_topline(self):
		topline_full = []
		for i in range(self.num_categories):
			topline_full += self.top_line
		return topline_full


class Reformatter(object):
	"""Used to build formatted file from .out file

	Attr:
		formatted_file: File to be written to
		outfile: CVDOutfile object containing information for .out file
	"""

	def __init__(self,outfile,formatted_file):
		self.formatted_file = formatted_file
		self.outfile = outfile

	def format(self,section):
		""" Reformats sections with particular label

		Args:
			section: TrackedSection object to be formatted
		"""
		for line_num in range(self.outfile.num_lines):
			if self.outfile.lines_list[line_num].find('SUMMED VARIABLES') > -1:
				break
			if self.outfile.find_title(line_num,section.title):
				self._format_block(line_num,section)

	def _format_block(self,line_num,section):
		base_year = self.outfile.base_year
		start_line = self._next_block_line(section,line_num)

		if section.year_offset == 0:
			category_line = self.outfile.get_line(start_line-2)
			section.write_header(category_line)

		num_list = self.outfile.get_block(start_line)
		formatted_nums = section.format_num_line(base_year,num_list)
		section.append_line(formatted_nums)

	def _next_block_line(self, section, line_num):
		"""Returns first line of next numeric block to read in"""
		return (section.linesdown + line_num if section.linesdown!=0
						else self.outfile.next_data_line(line_num))

class CVDOutfile(object):
	"""Contains information of .out file

	Attr:
		base_year_line: Integer ine of .outfile to look for base year
		age_ranges: Integer number of age ranges considered
		max_lines_after: Integer number of lines to search for block
			of numbers after finding a title
		lines_list: List of lines in .out file
		base_year: Integer first year of simulation
		num_lines: Integer number of lines in lines_list
	"""
	base_year_line = 9
	max_lines_after = 15

	def __init__(self,filename):
		self.lines_list = self._get_lines(filename)
		self.base_year = int(self.lines_list[self.base_year_line])
		self.num_lines = len(self.lines_list)

	def _get_lines(self,filename):
		with open(filename + '.out', 'r') as myfile:
			return myfile.readlines()

	def _replace_bad_chars(self, start_line):
		"""Replace characters that mess with reading in file"""
		for i in range(start_line, start_line + 6):
			self.lines_list[i] = self.lines_list[i].replace('. ', ' ')
			self.lines_list[i] = self.lines_list[i].replace('.\n',' ')
			#for CVD prevalence -- don't want 'x/y' just want rate
			self.lines_list[i] = re.sub(r'[0-9]*./ \s*[0-9]*',' ',
												self.lines_list[i])

	def find_title(self, line_num, title):
		return (self.lines_list[line_num].find(title + '     ') != -1 or
			self.lines_list[line_num].find(title + '\n') != -1 and
			self.lines_list[line_num].find('Acute ' + title) == -1)

	def next_data_line(self, line_num):
		"""Find next line containing numbers after line line_num"""
		for offset in range(self.max_lines_after):
			line = self.lines_list[offset+line_num]
			if 'age' in line:
				return offset + line_num + 1
		return -1

	def get_block(self, start_line):
		"""Get list of values in block starting at line start_line"""
		self._replace_bad_chars(start_line)
		block_lines = self.lines_list[start_line:start_line+6]
		block = NumBlock(block_lines)
		block.reorder_block()
		return block.get_list()

	def get_line(self,line_num):
		return self.lines_list[line_num]


class NumBlock(object):
	"""Block of values for one year in .out file

	Attr:
		num_list: List of the values in a data block of .out file
		columns: Number of columns in data block of .out file
			double the number of categories in data block (for M/F)
		rows = Number of rows ' ' - corresponds to number of age ranges
	"""
	rows = 6


	def __init__(self,lines_list):
		self.num_list=[]
		self._parse_block(lines_list)
		self.columns = len(self.num_list)//self.rows

	def _parse_block(self,lines):
		for line in lines:
			split_line = line.split()
			#ignore age range
			self.num_list += [num for num in split_line[1:]]

	def reorder_block(self):
		"""Puts block in desired order for printing"""
		reordered = []
		for i in range(self.columns):
			for j in range(self.rows):
				reordered.append(self.num_list[i + self.columns*j])
		self.num_list = reordered

	def get_list(self):
		return self.num_list


if __name__ == '__main__':
	# debug
	os.chdir(r"C:\Users\rdboylan\Documents\KBD\A. Mod91_mexPA_MCs_06.28.2019\intermediate0")
	
	main()
