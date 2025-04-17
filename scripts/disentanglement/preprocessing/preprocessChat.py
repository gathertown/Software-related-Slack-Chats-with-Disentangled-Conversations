#!python3
###############################################################################
# preprocessChat.py
# Author: Leighanne Hsu
# Modified By: Kosta Damevski
#
# This script takes XML-formatted chat and converts it to the format used by
# Charniak and Elsner 2008, that is
# timestamp name : comment
# Currently, actions (timestamp name * action) are not handled
#
# Requires Python 3 environment
# Execute as	python preprocessChat.py input.xml > output.txt
# or			py preprocessChat.py input.xml > output.txt
# The latter will automatically pick up and use Python 3 as long as Python 3.4
# or newer is installed.
###############################################################################

import xml.etree.ElementTree as ET
import sys
import re
import string
from datetime import datetime
import argparse

def removeUrls(text):
	urlPattern = r'(?P<url>https?://[^\s]+)'
	while re.search(urlPattern,text,flags=re.DOTALL):
		indexStart = re.search(urlPattern,text,flags=re.DOTALL).span()[0]
		indexEnd = re.search(urlPattern,text,flags=re.DOTALL).span()[1]
		text = text[:indexStart] + '__URLREMOVED__' + text[indexEnd:]	
	return text

def removeEmojis(text):
	emojiPattern = r':\w+:'
	text = re.sub(emojiPattern, ' ', text)
	return text

def removeNewlines(text):
	punct = '\n\r'
	translator = str.maketrans(punct, ' ' * len(punct))
	text = text.translate(translator)
	return text

def removePunctuation(text):
	punct = '\n\r`",;(){}[]+-=*\\/?<>'
	translator = str.maketrans(punct, ' ' * len(punct))
	text = text.translate(translator)
	return text

def replaceMentions(text):
	mentionPattern = r'<@\w+>'
	while re.search(mentionPattern,text):
		indexStart = re.search(mentionPattern,text).span()[0]
		indexEnd = re.search(mentionPattern,text).span()[1]
		mentionName = text[indexStart+2:indexEnd-1]
		text = text[:indexStart] + " " + text[indexEnd:]
		text = mentionName + ": " + text
	return text

def removePreformattedBlocks(text):
	blockPattern = r'```.+```'
	while re.search(blockPattern,text,flags=re.DOTALL):
		indexStart = re.search(blockPattern,text,flags=re.DOTALL).span()[0]
		indexEnd = re.search(blockPattern,text,flags=re.DOTALL).span()[1]
		text = text[:indexStart] + '__BLOCKREMOVED__' + text[indexEnd:]
	return text



if __name__ == "__main__":

	parser = argparse.ArgumentParser()

	parser.add_argument('-o', '--outputfile', nargs=1, help='output file', required=True)
	parser.add_argument('-i', '--inputfile', nargs=1, help='input xml file', required=True)
	parser.add_argument('--namesonly', action='store_true', help='leave messages as is, with names only added', required=False)

	args = parser.parse_args()

	chatFileName = args.inputfile[0]

	if chatFileName[-4:] != '.xml':
		chatFileName += '.xml'

	print("\nReading " + chatFileName + "\n", file=sys.stderr)

	with open(chatFileName, 'r', encoding='utf-8') as f:
		content = f.read()
	root = ET.fromstring(content)
	print("File read successfully\n\n", file=sys.stderr)

	# first 4 elements are the team, channel, start date/time, and end date/time
	info = root[:4]

	# the remaining elements are the messages
	messages = root[4:]

	with open(args.outputfile[0],'w') as outfile:
		TSfmt = '%Y-%m-%dT%H:%M:%S.%f'	# 24-hour time format
		starttime = datetime.strptime(messages[0][0].text, TSfmt)
		print("Total messages: " + str(len(messages)) + "\n", file=sys.stderr)
		for child in messages:

			timestamp = child[0].text
			tdelta = datetime.strptime(timestamp, TSfmt) - starttime
			secondsFromStart = round(tdelta.total_seconds())

			user = child[1].text

			# ignore extra empty <text/> tag before the actual text in some messages
			text = child[-1].text
			
			if text is not None: # Not all messages have any text, for some reason
				if args.namesonly:
					text = replaceMentions(text)
					text = removeNewlines(text)
				else:
					text = replaceMentions(text)
					#text = removeUrls(text)
					text = removePreformattedBlocks(text)
					text = removeEmojis(text)
					text = removeNewlines(text)
					#text = removePunctuation(text)

				if 'conversation_id' not in child.attrib:
					toFmtStr = "T1234 " + str(secondsFromStart) + " " + user + " :  " + text + "\n"
				else: 
					toFmtStr = "T" + child.attrib['conversation_id'] + " " + str(secondsFromStart) + " " + user + " :  " + text + "\n"


				outfile.write(toFmtStr)
