#!/usr/bin/env python3

#
# isbn.py
#
# Author       : Finn Rayment <finn@rayment.fr>
# Date created : 12/12/2021
#

import argparse
import json
from sys import exit
import urllib.request

API_URL = 'https://openlibrary.org/api/volumes/brief/isbn/'
JUSTIFY = 10
LINE_LEN = 80 # chars per line
MAX_SUBJECT_LINES = 3

LANGS = {
	'ara': 'Arabic',
	'chi': 'Chinese',
	'cze': 'Czech',
	'dan': 'Danish',
	'dut': 'Dutch',
	'eng': 'English',
	'fin': 'Finnish',
	'fre': 'French',
	'ger': 'German',
	'gre': 'Greek',
	'hin': 'Hindi',
	'ita': 'Italian',
	'jpn': 'Japanese',
	'lat': 'Latin',
	'pol': 'Polish',
	'por': 'Portuguese',
	'rus': 'Russian',
	'spa': 'Spanish',
	'swe': 'Swedish',
	'tur': 'Turkish'
}

argp = argparse.ArgumentParser()
argp.add_argument('isbn',
                  help='SBN, ISBN-10 or ISBN-13 number to search',
                  type=str)
args = argp.parse_args()

def sanitise_isbn(isbn):
	return ''.join(i for i in str(isbn) if i.isdigit())

def check_isbn(isbn):
	if len(isbn) == 9:
		# convert SBN to ISBN-10
		isbn = '0' + isbn
	if len(isbn) == 10:
		# ISBN-10
		s = 0
		t = 0
		for i in range(10):
			t += int(isbn[i])
			s += t
		return s % 11 == 0
	elif len(isbn) == 13:
		# ISBN-13
		o = [int(i) for i in isbn[::2]]
		e = [int(i)*3 for i in isbn[1::2]]
		return (sum(o)+sum(e)) % 10 == 0
	else:
		return False

isbn = sanitise_isbn(args.isbn)
if (len(isbn) != 10 and len(isbn) != 13) or not check_isbn(isbn):
	print('error: not a valid SBN, ISBN-10 or ISBN-13 number')
	exit(1)

def fetch_isbn(isbn):
	try:
		url = API_URL + str(isbn) + '.json'
		data = json.load(urllib.request.urlopen(url))
		return list(data['records'].values())[0]
	except TypeError:
		# when the JSON is empty, return an error that invokes a 'not found' msg
		raise KeyError

def print_align(header, data):
	align = ''.ljust(JUSTIFY)
	if not isinstance(data, list):
		data = [data]
	for idx,i in enumerate(data):
		if idx == 0:
			print(header.ljust(JUSTIFY), ':', str(i).strip())
		else:
			print(align + '  ', i.strip())

def print_key(details, header, key):
	try:
		val = details[key]
		if isinstance(val, str):
			val = val.capitalize()
		print_align(header, val)
	except KeyError:
		pass

def print_title(details):
	print_key(details, 'Title', 'title')

def print_subtitle(details):
	subtitle = []
	try:
		subtitle.append(details['subtitle'])
	except KeyError:
		pass
	try:
		subtitle.extend(details['by_statement'].split(' ;'))
	except KeyError:
		pass
	if len(subtitle) > 0:
		print_align('Subtitle', subtitle)

def print_author(data, details):
	try:
		authors = [j['name'] for j in [i for i in details['authors']]]
	except KeyError:
		try:
			authors = [j['name'] for j in [i for i in data['data']['authors']]]
		except KeyError:
			return
	print_align('Author', authors)

def print_edition(details):
	print_key(details, 'Edition', 'edition_name')

def print_format(details):
	print_key(details, 'Format', 'physical_format')

def print_pages(details):
	print_key(details, 'Pages', 'number_of_pages')

def print_weight(details):
	print_key(details, 'Weight', 'weight')

def print_date(details):
	print_key(details, 'Date', 'publish_date')

def print_publisher(details):
	print_key(details, 'Publisher', 'publishers')

def print_series(details):
	print_key(details, 'Series', 'series')

def print_location(details):
	print_key(details, 'Location', 'publish_places')

def print_revision(details):
	try:
		revision = details['revision']
	except KeyError:
		try:
			revision = details['latest_revision']
		except KeyError:
			return
	print_align('Revision', revision)

def print_language(details):
	try:
		langs = [i['key'] for i in details['languages']]
		langs = [i.split('/')[-1].capitalize() for i in langs]
		expand_langs = []
		for i in langs:
			try:
				expand_langs.append(LANGS[i.lower()])
			except KeyError:
				expand_langs.append(i)
		print_align('Language', expand_langs)
	except KeyError:
		pass

def print_subjects(data, details):
	try:
		subjects = details['subjects']
	except KeyError:
		try:
			subjects = [i['name'] for i in data['data']['subjects']]
		except KeyError:
			return
	subjects = sorted(subjects, key=len)
	# group subjects into lines
	line_len = LINE_LEN - len('Subject'.ljust(JUSTIFY) + ' : ')
	lines = []
	lineidx = 0
	for i in subjects:
		if len(i) >= line_len:
			i = i[0:line_len-3] + '...'
		if len(lines) == 0:
			# first entry
			lines.append(i)
			continue
		if len(', '.join([lines[lineidx], i])) >= line_len:
			# no more room, next line
			lineidx += 1
			if lineidx >= MAX_SUBJECT_LINES:
				# no more lines
				break
			lines.append(i)
		else:
			# join to the end of the string
			lines[lineidx] = ', '.join([lines[lineidx], i])
	print_align('Subject', lines)

def print_isbn(isbn, data):
	isbns = data['isbns']
	if isbn not in isbns:
		isbns.append(isbn)
	isbns = sorted(isbns, key=len)
	for i in isbns:
		if len(i) == 9:
			print('SBN        : ' + i)
		elif len(i) == 10:
			print('ISBN-10    : ' + i)
		elif len(i) == 13:
			print('ISBN-13    : ' + i)

try:
	data = fetch_isbn(isbn)
	details = data['details']['details']
	print_title(details)
	print_subtitle(details)
	print_author(data, details)
	print_language(details)
	print_format(details)
	print_pages(details)
	print_weight(details)
	print_location(details)
	print_date(details)
	print_publisher(details)
	print_edition(details)
	print_series(details)
	print_revision(details)
	print_subjects(data, details)
	print_isbn(isbn, data)
except urllib.error.URLError as e:
	err = str(e)
	print('error: unable to fetch entry')
	if len(err) > 0:
		print('\tURLError: ' + err)
	exit(1)
except KeyError as e:
	err = str(e)
	print('error: unable to find entry')
	if len(err) > 0:
		print('\tKeyError: ' + err)
	exit(1)
except Exception as e:
	err = str(e)
	print('error: unexpected error')
	if len(err) > 0:
		print('\tException: ' + err)
	exit(1)

