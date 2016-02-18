import feedparser
import re
import argparse

def getwordcounts(url):
	d = feedparser.parse(url)
	wc = {}

	if not hasattr(d.feed, 'title'):
		return None, None
	#all entries in feed of RSS or Atom feed
	for e in d.entries:
		if 'summary' in e: summary=e.summary
		else: summary=e.description

		#list of words
		words = getwords(e.title + ' ' + summary)
		for word in words:
			wc.setdefault(word, 0) #if the word isn't in the dict, create an instance for it
			wc[word] += 1


	return d.feed.title, wc

def getwords(html):
	#remove all HTML tags 
	txt = re.compile(r'<[^>]+>').sub('', html)

	#split up the words
	words = re.compile(r'[^A-Z^a-z]+').split(txt)

	#make standard
	return [word.lower() for word in words if word != '']

def getlist(index, filt=None, filewrite=None, verbose=False):
	apcount = {} # number of blogs a word appears in {word: #blogs ... } 
	wordcounts = {} #blog: {word: #appearance, word2: #appearance, ... }

	f = open(index)
	for feedurl in f:
		if verbose: print("getting info for: ", feedurl)
		title, wc = getwordcounts(feedurl)
		if title is None: continue
		wordcounts[title] = wc
		for word, count in wc.items():
			apcount.setdefault(word, 0)
			if count > 1:
				apcount[word] += 1

	#optionally filter words by frequency
	wordlist = []
	for w, bc in apcount.items(): #w is word bc is count
		if filt is None:
			wordlist.append(w)
		else:
			frac = float(bc)/len(apcount.items())
			if frac > float(filt[0]) and frac < float(filt[1]): wordlist.append(w)

	#optionally write to a file
	if filewrite is not None:
		print "writing to file"
		writetofile(filewrite, wordlist, wordcounts)

def writetofile(filename, wordlist, wordcounts):
	out = file(filename, 'w')
	out.write('Source')
	for word in wordlist: out.write('\t%s' % word)
	out.write('\n')
	for blog, wc in wordcounts.items():
		out.write(repr(blog))
		for word in wordlist:
			if word in wc: out.write('\t%d' % wc[word])
			else: out.write('\t0')
		out.write('\n')

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Parses the rss feeds in the given file and provides word counts for each one')
	parser.add_argument('file',
	                   help='List of urls to read from')
	parser.add_argument('--ofile', 
						help='file to write to')
	parser.add_argument('--filter', 
						help='density range of words to return in form \'lowest, highest\' from 0.0 to 1.0')

	args = parser.parse_args()

	if not args.ofile:
		outfile = "sourcedata.csv"
	else:
		outfile = args.ofile

	if args.filter:
		filt = (args.filter).split(',')
	else:
		filt = None

	getlist(args.file, filt=filt, filewrite=outfile, verbose=True)