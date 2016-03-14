import urllib2
from BeautifulSoup import *
from urlparse import urljoin

from pysqlite2 import dbapi2 as sqlite

import re

ignorewords = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it'])

class Crawler:
	def __init__(self, dbname):
		self.con = sqlite.connect(dbname)
		pass

	def __del__(self):
		self.con.close()
		pass

	def dbcommit(self):
		self.con.commit()
		pass	

	def getentryid(self, table, field, value, createnew=True):
		cur = self.con.execute("select rowid from %s where %s='%s'" % (table, field, value))
		res = cur.fetchone()
		if res == None:
			cur = self.con.execute("insert into %s (%s) values ('%s')" % (table, field, value))
			return cur.lastrowid
		else:
			return res[0]

	#adds whole page of words to db and specifies the location by the words count from the start
	def addtoindex(self, url, soup):
		if self.isindexed(url): return
		print 'Indexing %s' % url

		#get individual words
		text = self.gettextonly(soup)
		words = self.separatewords(text)

		#get url ID
		urlid = self.getentryid('urllist', 'url', url)

		#link each word to this url
		for i in xrange(len(words)):
			word = words[i]
			if word in ignorewords: continue
			wordid = self.getentryid('wordlist', 'word', word)
			self.con.execute("insert into wordlocation(urlid, wordid, location) values (%d, %d, %d)" % (urlid, wordid, i))


	def gettextonly(self, soup):
		v = soup.string #purely text portion between tags
		if v == None:
			c = soup.contents #nested elements of a tag
			resulttext = ''
			for t in c:
				subtext = self.gettextonly(t) #...recursion...
				resulttext += subtext + '\n'
			return resulttext
		else:
			return v.strip()

	def separatewords(self, text):
		splitter = re.compile('\\W*') #finds anything that isn't a letter or a number
		return [s.lower() for s in splitter.split(text) if s != '']
		#look into stemming suffixes

	def isindexed(self, url):
		#this checks to see if it's been crawled and if so whether there are any words associated with it
		#could cause issues on pages that are empty of text (rare, but possible)
		u = self.con.execute("select rowid from urllist where url='%s'" % url).fetchone()
		if u != None: 
			v = self.con.execute('select * from wordlocation where urlid=%d' % u[0]).fetchone()
			if v != None: return True
		return False

	def addlinkref(self, urlFrom, urlTo, linkText):
		words = self.separatewords(linkText)
		fromid = self.getentryid('urllist', 'url', urlFrom)
		toid = self.getentryid('urllist', 'url', urlTo)
		if fromid == toid: return
		cur = self.con.execute("insert into link(fromid, toid) values (%d, %d)" % (fromid, toid))
		linkid = cur.lastrowid
		for word in words:
			if word in ignorewords: continue
			wordid = self.getentryid('wordlist', 'word', word)
			self.con.execute("insert into linkwords(linkid, wordid) values (%d, %d)" % (linkid, wordid))
		pass

	def createindextables(self):
		self.con.execute('create table urllist(url)')
		self.con.execute('create table wordlist(word)')
		self.con.execute('create table wordlocation(urlid, wordid, location)')
		self.con.execute('create table link(fromid integer, toid integer)')
		self.con.execute('create table linkwords(wordid, linkid)')
		self.con.execute('create index wordidx on wordlist(word)')
		self.con.execute('create index urlidx on urllist(url)')
		self.con.execute('create index wordurlidx on wordlocation(wordid)')
		self.con.execute('create index urltoidx on link(toid)')
		self.con.execute('create index urlfromidx on link(fromid)')
		self.dbcommit()
		pass	

	def crawl(self, pages, depth=2):
		for i in xrange(depth):
			newpages = set()
			for page in pages:
				try:
					c = urllib2.urlopen(page)
				except:
					print "couldn't open %s" % page
					continue
				soup = BeautifulSoup(c.read())
				self.addtoindex(page, soup)

				links = soup('a')
				for link in links:
					if 'href' in dict(link.attrs):
						url = urljoin(page, link['href'])
						if url.find("'") != -1: continue #we don't want errant quotes
						url = url.split('#')[0] # we want whole page
						if url[0:4]=='http' and not self.isindexed(url): 
							newpages.add(url)
						linkText = self.gettextonly(link)
						self.addlinkref(page, url, linkText)
				self.dbcommit()

			pages = newpages


def main():
	print "all these positions crawl"
	pagelist = ['http://www.hackaday.com']
	crawler = Crawler('searchindex.db')

	"""
		crawler.createindextables()
	"""		

	crawler.crawl(pagelist)

if __name__ == "__main__":
	main()