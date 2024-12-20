import argparse
import math
import random
import csv
from statistics import mean, stdev
import unicodedata
from collections import Counter

parser = argparse.ArgumentParser(prog='count.py', description='counts the letter frequency for letter positions within a text')
parser.add_argument('--source', help='source of text: oanc, norvig, oanc-list', default='oanc')
parser.add_argument('--source-count', help='sources to sample', default=100)
parser.add_argument('--word-sample-count', help='number of words to collect from a source', default=200)
parser.add_argument('--bias-to-front', help='bias the random starting point towards the front of the article', default=True)
parser.add_argument('--word-list', help='restrict acceptable words Scrabble, common', default=None)
parser.add_argument('--written-only', help='only process written texts', action='store_true')
parser.add_argument('--ignore-punctuation', help='ignore punctuation within words', default=True)
parser.add_argument('--strip-accents', help='strip accents from letters in a word', default=True)
parser.add_argument('--output', help='output csv filename', default=None)
parser.add_argument('--stat-table', help='filename for a csv table of K counts', default=None)

args = parser.parse_args()

alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def load_valid_words(filename):
	words = set()
	with open (filename, 'r') as file:
		for line in file:
			word = line.split()[0]
			words.add(word)
	return words

def strip_accents(s):
	return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def files_in_directory(directory):
	import os
	files = []
	for root, _, filenames in os.walk(directory):
		for filename in filenames:
			if filename.endswith('.txt'):
				files.append(os.path.join(root, filename))
	return files

def alphabetical(word):
	for letter in word:
		if letter not in alphabet:
			return False
	return True

def valid_word(word, dictionary):
	if len(word) >= 3 and len(word) <= 7:
		return alphabetical(word) and (dictionary == None or word in dictionary)

def column(length, position):
	return f"{length} / {position+1}"

def filter_file(file):
	if args.written_only:
		return 'spoken' not in file
	else:
		return True

def create_headers():
	headers = ['']
	for l in range(3, 8):
		for p in range(l):
			headers.append(f"{column(l, p)}")
	headers.append('T')
	return headers

def convert_to_types(sample_list):
	types = {}
	for word in sample_list:
		length = len(word)
		if length not in types:
			types[length] = Counter()
		types[length][word] += 1
	return types

def sample_words(file, dictionary):
	sample_list = []
	with open(file, 'r', encoding='utf8') as text_file:
		word_list = []
		for line in text_file:
			for word in line.split():
				word_list.append(word)

		count = 0
		word_sample_count = int(args.word_sample_count)
		start = len(word_list) - word_sample_count if args.bias_to_front else len(word_list)
		if start >= 0:
			pos = random.randrange(start)
			while count < int(args.word_sample_count) and pos < len(word_list):
				word = word_list[pos]
				if args.ignore_punctuation:
					word = ''.join(filter(lambda c: c.isalnum(), word)).upper()
				else:
					word = word.strip('\\/-.,;:?!()\'"`—“”’').upper()
				if args.strip_accents:
					word = strip_accents(word)
				if valid_word(word, dictionary):
					sample_list.append(word)
					count += 1
				pos += 1
	return sample_list


def collect_sample(valid_words):
	files = files_in_directory('OANC-GrAF')
	sources = list(filter(lambda file: filter_file(file), files))
	random.shuffle(sources)
	samples = 0
	file_number = 0
	collection = []
	while samples < int(args.source_count) and file_number < len(sources):
		file = sources[file_number]
		sample_list = sample_words(file, valid_words)
		if len(sample_list) == int(args.word_sample_count):
			collection.extend(sample_list)
			samples += 1
		file_number += 1

	if samples < int(args.source_count):
		print(f'not enough sources to collect {args.word_sample_count} words from {args.source_count} sources, only got {samples}')

	return collection

def create_frequency_table():
	letter_position_count = {}
	for letter in alphabet:
		letter_position_count[letter] = Counter()
	return letter_position_count

def create_frequency_distribution_table(headers):
	letter_position_distribution = {}
	for letter in alphabet:
		letter_position_distribution[letter] = {}
		for col in headers:
			letter_position_distribution[letter][col] = []
	return letter_position_distribution

def letter_frequency_count(types):
	letter_position_count = create_frequency_table()
	for length in range(3, 8):
		token_count = 0
		for word, tokens in types[length].items():
			token_count += tokens
			for p in range(length):
				col = column(length, p)
				letter_position_count[word[p]][col] += tokens
				letter_position_count[word[p]]['T'] += tokens

	return letter_position_count

def display_count(count):
	return f'{count}' if count != 0 else ''

def output_table(filename, headers, letter_position_count):
	with open(filename, 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(headers)
		for letter in alphabet:
			row = [f'{letter}']
			for l in range(3, 8):
				for p in range(l):
					col = column(l, p)
					row.append(display_count(letter_position_count[letter][col]))
			row.append(display_count(letter_position_count[letter]['T']))
			writer.writerow(row)

def load_types_and_tokens(valid_words):
	counter = Counter()
	if args.source == 'norvig':
		with open ('google-books-common-words.txt', 'r') as file:
			for line in file:
				word, frequency = line.split()
				if len(word) >= 3 and len(word) <= 7:
					if valid_words == None or valid_word(word, valid_words):
						counter[word] = int(frequency)
	else:
		files = files_in_directory('OANC-GrAF')
		sources = list(filter(lambda file: filter_file(file), files))
		for file in sources:
			sample_list = sample_words(file, valid_words)
			counter.update(sample_list)

	return counter

def generate_table(valid_words, counter, headers):
	if counter == None:
		word_sample = collect_sample(valid_words)
	else:
		word_sample = random.choices(list(counter.keys()), list(counter.values()), k=int(args.word_sample_count) * int(args.source_count))

	types = convert_to_types(word_sample)
	letter_position_count = letter_frequency_count(types)
	if args.output:
		output_table(f'{args.output}.csv', headers, letter_position_count)
	return letter_position_count

def open_table(filename, headers):
	letter_position_count = create_frequency_table()
	with open(filename, newline='') as file:
		reader = csv.reader(file)
		for row in reader:
			letter = row[0]
			if letter != '':
				for i in range(1, len(row)):
					if i < len(headers):
						letter_position_count[letter][headers[i]] = 0 if row[i] == '' else int(row[i])
	return letter_position_count

valid_words = None
headers = create_headers()
match args.word_list:
	case 'Scrabble':
		valid_words = load_valid_words('Scrabble-dictionary.txt')
	case 'common':
		valid_words = load_valid_words('google-books-common-words.txt')
	case _:
		valid_words = None
counter = None
if args.source == 'norvig' or args.source == 'oanc-list':
	counter = load_types_and_tokens(valid_words)
if args.output:
	generate_table(valid_words, counter, headers)
elif args.stat_table:
	stat_table = open_table(f'{args.stat_table}.csv', headers)
	letter_position_distribution = create_frequency_distribution_table(headers)
	letter_position_z_score = create_frequency_table()
	for trial in range (100):
		letter_position_count = generate_table(valid_words, counter, headers)
		for letter in alphabet:
			for col in headers:
				letter_position_distribution[letter][col].append(letter_position_count[letter][col])
	stddev4 = 0
	total = 0
	for letter in alphabet:
		for col in headers:
			average = mean(letter_position_distribution[letter][col])
			stddev = stdev(letter_position_distribution[letter][col])
			z = 0 if stddev == 0 else (stat_table[letter][col] - average) / stddev
			letter_position_z_score[letter][col] = z
			if abs(z) < 2:
				stddev4 += 1
			total += 1
	print(f'{int(stddev4 * 100 / total)}% are less than 2 standard deviations from the mean')
	output_table(f'{args.stat_table}-z.csv', headers, letter_position_z_score)


# def calculate_k_first():
# 	letter_position_count = generate_table()
# 	sum_k_1st = 0
# 	for length in range(3, 8):
# 		sum_k_1st += letter_position_count['K'][column(length, 0)]
# 	return sum_k_1st

# for i in range(10):
# 	trials = []
# 	for i in range(100):
# 		trials.append(calculate_k_first())
# 	z = (152 - mean(trials)) / stdev(trials)
# 	root2 = 2**0.5
# 	probability = 0.5 * (1 + math.erf(z / root2))
# 	print(f'Probability of finding 152 or less words beginning with K in 20,000 is approximately {round(probability * 100, sigfigs=1)}%')

# def generate_letter_position_count_array(headers):
# 	letter_position_count_array = {}
# 	for letter in alphabet:
# 		letter_position_count_array[letter] = {}
# 		for col in headers:
# 			letter_position_count_array[letter][col] = []
# 	return letter_position_count_array

# def calculate_z_score(letter_position_count_array, headers):
# 	letter_position_z_score = create_frequency_table(headers)
# 	with open('run2.csv', newline='') as file:
# 		reader = csv.reader(file)
# 		for row in reader:
# 			letter = row[0]
# 			if letter in letter_position_count_array:
# 				for i in range(1, len(row)):
# 					if i < len(headers):
# 						x = int(0 if row[i] == '' else row[i])
# 						#x = letter_position_count_array[letter][headers[i]][0]
# 						mu = mean(letter_position_count_array[letter][headers[i]])
# 						sigma = math.sqrt(variance(letter_position_count_array[letter][headers[i]], mu))
# 						z = 0 if sigma == 0 else (x - mu) / sigma
# 						letter_position_z_score[letter][headers[i]] = f'{z:.2f}' if abs(z) > 2 else '' # {mu}+/-{sigma*2:.2f}'
# 	return letter_position_z_score


# headers = create_headers()
# letter_position_count_array = generate_letter_position_count_array(headers)
# for i in range(100):
# 	letter_position_count = generate_table(headers)
# 	for letter in alphabet:
# 		for col in headers:
# 			letter_position_count_array[letter][col].append(letter_position_count[letter][col])
# letter_position_z_score = calculate_z_score(letter_position_count_array, headers)
# if args.output:
# 	output_table(headers, letter_position_z_score)

# with open('MayznerTresselt1965.csv', newline='') as file:
# 	reader = csv.reader(file)
# 	for row in reader:
# 		letter = row[0].lower()
# 		if letter in letter_position_count:
# 			for i in range(1, len(row)):
# 				if i < len(headers):
# 					#x = int(0 if row[i] == '' else row[i])
# 					x = letter_position_count[letter][headers[i]][0]
# 					mu = mean(letter_position_count[letter][headers[i]])
# 					sigma = sqrt(variance(letter_position_count[letter][headers[i]], mu))
# 					z = 0 if sigma == 0 else (x - mu) / sigma
# 					cv = 0 if mu == 0 else sigma / mu
# 					letter_position_count[letter][headers[i]] = abs(z)
