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
parser.add_argument('--filter-texts', help='only process texts from given sources (such as fiction,non-fiction,journal)', default=None)
parser.add_argument('--ignore-punctuation', help='ignore punctuation within words', default=True)
parser.add_argument('--strip-accents', help='strip accents from letters in a word', default=True)
parser.add_argument('--output', help='output csv filename', default=None)
parser.add_argument('--stat-table', help='filename for a csv table of Z scores', default=None)
parser.add_argument('--scatter-plot', help='filename for a csv table of first and third letter scores', default=None)
parser.add_argument('--trials', help='number of trials', default=100)
parser.add_argument('--count-types', help='output the tokens of the given type (KNOW,LIKE)', default=None)
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
	if args.filter_texts != None:
		filters = args.filter_texts.split(',')
		for filter in filters:
			if filter in file:
				return True
		return False
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

def list_words(file, dictionary):
	word_list = []
	with open(file, 'r', encoding='utf8') as text_file:
		for line in text_file:
			for word in line.split():
				if args.ignore_punctuation:
					word = ''.join(filter(lambda c: c.isalnum(), word)).upper()
				else:
					word = word.strip('\\/-.,;:?!()\'"`—“”’').upper()
				if args.strip_accents:
					word = strip_accents(word)
				if valid_word(word, dictionary):
					word_list.append(word)
	return word_list

def sample_words(file, dictionary):
	sample_list = []
	word_list = list_words(file, dictionary)
	word_sample_count = int(args.word_sample_count)
	start = len(word_list) - word_sample_count if args.bias_to_front else len(word_list)
	if start >= 0:
		pos = 0 if start == 0 else random.randrange(start)
		count = 0
		while count < int(args.word_sample_count) and pos < len(word_list):
			sample_list.append(word_list[pos])
			pos += 1
			count += 1
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

def load_types_and_tokens(source, valid_words):
	counter = Counter()
	if source == 'norvig':
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
			sample_list = list_words(file, valid_words)
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
	counter = load_types_and_tokens(args.source, valid_words)
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
elif args.scatter_plot:
	with open(f'{args.scatter_plot}.csv', 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(['Sample', 'First', 'Third'])
		writer.writerow(['Mayzner & Tresselt 1965', 152, 221])
		writer.writerow(['Norvig 2012', 124, 149])
		for trial in range(int(args.trials)):
			letter_position_count = generate_table(valid_words, counter, headers)
			first = 0
			third = 0
			for position in range(3, 8):
				first += letter_position_count['K'][column(position, 0)]
				third += letter_position_count['K'][column(position, 2)]
			writer.writerow([f'Trial-{trial}', first, third])
elif not counter == None:
	first = 0
	third = 0
	total = 0
	digrams = Counter()
	types = 0
	words = []
	common = Counter()
	if args.count_types != None:
		words = args.count_types.split(',')
	for type, token in counter.items():
		types += 1
		total += token
		if type[0] == 'K':
			first += token
		if type[2] == 'K':
			third += token
		if len(type) == 4 and (type[0] == 'K' or type[2] == 'K'):
			common[type] += token
		for word in words:
			if len(type) == len(word):
				for letter in range(len(word) - 1):
					if type[letter] == word[letter] and type[letter+1] == word[letter+1]:
						digrams[word[letter:letter+2]] += token
	sample_size = int(args.word_sample_count) * int(args.source_count)
	scale = sample_size / total
	if args.count_types:
		for word in words:
			print(f'{word} {round(counter[word] * scale)}')
			for letter in range(len(word) - 1):
				digram = word[letter:letter+2]
				print(f'{digram} {round(digrams[digram] * scale)}')
	for (type, token) in common.most_common(10):
		print(f'{type} {round(token * scale)}')
	print(f'Total types: {types} tokens: {total} Sample size {sample_size} First letter is K: {round(first * scale)}, Third letter is K: {round(third * scale)}')
