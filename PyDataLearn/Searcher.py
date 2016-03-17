from pysqlite2 import dbapi2 as sqlite
import argparse

import NeuralNet

class Searcher:
	def __init__(self, dbname):
		self.con = sqlite.connect(dbname)
		self.net = NeuralNet.SearchNet('nn.db')

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

		weights = [(1.5, self.frequencyscore(rows)), 
				   (1.5, self.locationscore(rows)), 
				   (0.5, self.distancescore(rows)),
				   (0.5, self.inboundlinksscore(rows)),
				   (0.5, self.pagerankscore(rows)),
				   (1.0, self.linktextscore(rows, wordids))]

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
		print "calculating frquencies"
		counts = dict([(row[0], 0) for row in rows])
		for row in rows: counts[row[0]] += 1
		return self.normalizescores(counts)

	def locationscore(self, rows):
		print "calculating by location"
		locations = dict([(row[0], 1000000) for row in rows])
		for row in rows:
			loc = sum(row[1:])
			if loc < locations[row[0]]: locations[row[0]] = loc

		return self.normalizescores(locations, smallIsBetter=True)

	def inboundlinksscore(self, rows):
		print "calculating by inbound links"
		uniqueurls = set([row[0] for row in rows])
		inboundcount = dict([(u, self.con.execute('select count(*) from link where toid=%d' % u).fetchone()[0]) \
			for u in uniqueurls])
		return self.normalizescores(inboundcount)

	def distancescore(self, rows):
		print "calculating by word distance"
		if len(rows[0]) <= 2: return dict([(row[0], 1.0) for row in rows])

		mindistance = dict([(row[0], 1000000) for row in rows])

		for row in rows:
			dist = sum([abs(row[i] - row[i - 1]) for i in range(2, len(row))])
			if dist < mindistance[row[0]]: mindistance[row[0]] = dist

		return self.normalizescores(mindistance, smallIsBetter=True)

	def pagerankscore(self, rows):
		print "calculting by pageranks"
		pageranks = dict([(row[0], self.con.execute('select score from pagerank where urlid=%d' % row[0]).fetchone()[0]) for row in rows])
		maxrank = max(pageranks.values())
		normalizedscores = dict([(u, float(l)/maxrank) for (u,l) in pageranks.items()])
		return normalizedscores

	#logic checks out, but it won't find links between pages
	def linktextscore(self, rows, wordids):
		print "calculating by link text"
		linkscores = dict([(row[0], 0) for row in rows])
		print linkscores
		for wordid in wordids:
			#find all link text containing the words we're looking for
			cur = self.con.execute('select link.fromid,link.toid from linkwords,link where wordid=%d and linkwords.linkid=link.rowid' % wordid)
			for (fromid, toid) in cur:
				print fromid, toid
				if toid in linkscores:
					pr = self.con.execute('select score from pagerank where urlid=%d' % fromid).fetchone()[0]
					linkscores[toid] += pr

		maxscore = max(linkscores.values())
		if maxscore == 0: return normalizedscores
		normalizedscores = dict([(u, float(l)/maxscore) for (u,l) in linkscores.items()])
		return normalizedscores

	def nnscore(self, rows, wordids):
		#must train the Neural net first
		urlids = [urlid for urlid in set([row[0] for row in rows])]
		nnres = net.getresult(wordids, urlids)
		scores = dict([(urlids[i], nnres[i]) for i in range(len(urlids))])
		return self.normalizescores(scores)

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