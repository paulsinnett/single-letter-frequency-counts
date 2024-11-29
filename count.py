import argparse
import random
import csv
import unicodedata

parser = argparse.ArgumentParser(prog='count.py', description='counts the letter frequency for letter positions within a text')
parser.add_argument('--source', help='source documents directory', default='OANC-GrAF')
parser.add_argument('--source-count', help='sources to sample', default=100)
parser.add_argument('--word-sample-count', help='number of words to collect from a source', default=200)
parser.add_argument('--bias-to-front', help='bias the random starting point towards the front of the article', default=True)
parser.add_argument('--word-list', help='restrict acceptable words Scrabble, common', default=None)
parser.add_argument('--written-only', help='only process written texts', action='store_true')
parser.add_argument('--ignore-punctuation', help='ignore punctuation within words', default=True)
parser.add_argument('--strip-accents', help='strip accents from letters in a word', default=True)
parser.add_argument('--output', help='output cvs filename', default='output')

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
			types[length] = {}
		
		if word in types[length]:
			types[length][word] += 1
		else:
			types[length][word] = 1
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

def collect_sample():
	valid_words = None
	match args.word_list:
		case 'Scrabble':
			print('loading Scrabble dictionary')
			valid_words = load_valid_words('Scrabble-dictionary.txt')
		case 'common':
			print('loading common words dictionary')
			valid_words = load_valid_words('google-books-common-words.txt')
		case _:
			valid_words = None
	files = files_in_directory(args.source)
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

	return convert_to_types(collection)

def letter_frequency_count(headers, types):
	letter_position_count = {}
	for letter in alphabet:
		letter_position_count[letter] = {}
		for col in headers:
			letter_position_count[letter][col] = 0

	for length in range(3, 8):
		type_count = len(types[length])
		token_count = 0
		for word, tokens in types[length].items():
			token_count += tokens
			for p in range(length):
				col = column(length, p)
				letter_position_count[word[p]][col] += tokens
				letter_position_count[word[p]]['T'] += tokens
		print(f'{length} letter words, {token_count} tokens, {type_count} types;')

	return letter_position_count

def display_count(count):
	return f'{count}' if count > 0 else ''

def output_table(headers, letter_position_count):
	with open(f'{args.output}.csv', 'w', newline='') as file:
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

headers = create_headers()
types = collect_sample()
letter_position_count = letter_frequency_count(headers, types)
output_table(headers, letter_position_count)
sum_1st = 0
sum_3rd = 0
for length in range(3, 8):
	sum_1st += letter_position_count['K'][column(length, 0)]
	sum_3rd += letter_position_count['K'][column(length, 2)]

print(f'Ratio of words with K as 3rd letter {sum_3rd} : words beginning with K {sum_1st} is {sum_3rd / sum_1st:.2f} : 1')
