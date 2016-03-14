from pysqlite2 import dbapi2 as sqlite
import argparse


class Searcher:
	def __init__(self, dbname):
		self.con = sqlite.connect(dbname)
	def __del__(self):
		self.con.close()

	def getmatchrows(self, q):
		#finds all urls containing the searched for words q
		#create a reference to the wordlocation table for each word in the list and join them on the url ID's
		fieldlist = 'w0.urlid'
		tablelist = ''
		clauselist = ''
		wordids = []

		wordcount = 0

		words = q.split(' ')
		tablenumber = 0
		for word in words:
			# get the word ID
			wordrow = self.con.execute("select rowid from wordlist where word='%s'" % word).fetchone()
			if wordrow != None:
				wordcount += 1
				wordid = wordrow[0]
				wordids.append(wordid)
				if tablenumber > 0:
					tablelist += ','
					clauselist += ' and '
					clauselist += 'w%d.urlid=w%d.urlid and ' % (tablenumber - 1, tablenumber)
				fieldlist += ',w%d.location' % tablenumber
				tablelist += 'wordlocation w%d' % tablenumber
				clauselist += 'w%d.wordid=%d' % (tablenumber, wordid)
				tablenumber += 1

		if wordcount == 0: return 0, 0
		fullquery = 'select %s from %s where %s' % (fieldlist, tablelist, clauselist)
		cur = self.con.execute(fullquery)
		rows = [row for row in cur]

		return rows, wordids #returns [(urlid, word0 location, word1 location, ... wordn location) ...] [word0 id ... wordn id]

	def getscoredlist(self, rows, wordids):
		totalscores = dict([(row[0], 0) for row in rows])

		weights = [(1.0, self.locationscore(rows)), (1.5, self.locationscore(rows)), (0.5, self.distancescore(rows))]

		for (weight, scores) in weights:
			for url in totalscores:
				totalscores[url] += weight*scores[url]

		return totalscores

	def normalizescores(self, scores, smallIsBetter=False):
		vsmall = 0.00001
		if smallIsBetter:
			minscore = min(scores.values())
			return dict([(u, float(minscore)/max(vsmall, l)) for (u,l) in scores.items()])
		else:
			maxscore = max(scores.values())
			if maxscore == 0: maxscore = vsmall
			return dict([(u, float(c)/maxscore) for (u,c) in scores.items()])

	def frequencyscore(self, rows):
		counts = dict([(row[0], 0) for row in rows])
		for row in rows: counts[row[0]] += 1
		return self.normalizescores(counts)

	def locationscore(self, rows):
		locations = dict([(row[0], 1000000) for row in rows])
		for row in rows:
			loc = sum(row[1:])
			if loc < locations[row[0]]: locations[row[0]] = loc

		return self.normalizescores(locations, smallIsBetter=True)

	def distancescore(self, rows):
		if len(rows[0]) <= 2: return dict([(row[0], 1.0) for row in rows])

		mindistance = dict([(row[0], 1000000) for row in rows])

		for row in rows:
			dist = sum([abs(row[i] - row[i - 1]) for i in range(2, len(row))])
			if dist < mindistance[row[0]]: mindistance[row[0]] = dist

		return self.normalizescores(mindistance, smallIsBetter=True)

	def geturlname(self, ID):
		return self.con.execute("select url from urllist where rowid=%d" % ID).fetchone()[0]

	def query(self, q):
		rows, wordids = self.getmatchrows(q)
		scores = self.getscoredlist(rows, wordids)
		rankedscores = sorted([(score, url) for (url, score) in scores.items()], reverse=1)
		for (score, urlid) in rankedscores[0:10]:
			print '%f\t%s' % (score, self.geturlname(urlid))

def main():
	parser = argparse.ArgumentParser(description='web searching platform using various metrics')
	parser.add_argument('search',
	                   help='a string to search for in the compiled index')

	args = parser.parse_args()

	searcher = Searcher('searchindex.db')
	searcher.query(args.search)

if __name__ == "__main__":
	main()