from math import tanh
from pysqlite2 import dbapi2 as sqlite

def dtanh(y):
	#this effectively creates a smaller change multiplier when the value is closest to 0 (when the slope is steepest) P_D controller?
	return 1.0-y*y

class SearchNet:
	def __init__(self, dbname):
		self.con = sqlite.connect(dbname)

	def __del__(self):
		self.con.close()

	def maketables(self):
		self.con.execute('create table hiddennode(create_key)')
		self.con.execute('create table wordhidden(fromid, toid, strength)')
		self.con.execute('create table hiddenurl(fromid, toid, strength)')
		self.con.commit()

	def getstrength(self, fromid, toid, layer):
		#returns strength of connection from fromid to toid
		#layer specifies the table, whether dendrites connecting input to hidden or hidden to output
		if layer == 0: table = 'wordhidden'
		else: table = 'hiddenurl'
		res = self.con.execute('select strength from %s where fromid=%d and toid=%d' % (table, fromid, toid)).fetchone()
		if res == None:
			if layer == 0: return -0.2 #if extra word, we want negative effects
			if layer == 1: return 0

		return res[0]

	def setstrength(self, fromid, toid, layer, strength):
		if layer == 0: table = 'wordhidden'
		else: table = 'hiddenurl'
		res = self.con.execute('select rowid from %s where fromid=%d and toid=%d' % (table, fromid, toid)).fetchone()
		if res == None: 
			#we generate nodes as we need them/use them
			self.con.execute('insert into %s (fromid,toid,strength) values (%d,%d,%f)' % (table, fromid, toid, strength))
		else:
			rowid = res[0]
			self.con.execute('update %s set strength=%f where rowid=%d' % (table, strength, rowid))

	def generatehiddennode(self, wordids, urls):
		#generates new nodes for searches we haven't done yet
		if len(wordids) > 3: return None
		#check to see if we've created a node for this set of words
		createkey = '_'.join(sorted([str(wi) for wi in wordids])) #sorting ensures any combination of these words
		res = self.con.execute("select rowid from hiddennode where create_key='%s'" % createkey).fetchone()

		#if we haven't seen this set of words
		if res == None:
			cur = self.con.execute("insert into hiddennode (create_key) values ('%s')" % createkey)
			hiddenid = cur.lastrowid
			for wordid in wordids:
				self.setstrength(wordid, hiddenid, 0, 1.0/len(wordids))
			for urlid in urls:
				self.setstrength(hiddenid, urlid, 1, 0.1)
			self.con.commit()


	def getallhiddenids(self, wordids, urlids):
		l1 = {}
		for wordid in wordids:
			cur = self.con.execute('select toid from wordhidden where fromid=%d' % wordid)
			for row in cur: l1[row[0]] = 1
		for urlid in urlids:
			cur = self.con.execute('select fromid from hiddenurl where toid=%d' % urlid)
			for row in cur: l1[row[0]] = 1
		return l1.keys()

	#load weights into memory for speeeed
	def setupnetwork(self, wordids, urlids):
		#values lists
		self.wordids = wordids #current list of words we're searching for
		self.hiddenids = self.getallhiddenids(wordids, urlids) #current list of hidden ids relevant to our input wordids and urlids
		self.urlids = urlids 

		#node outputs
		self.ai = [1.0]*len(self.wordids)  #input layer outputs for each word
		self.ah = [1.0]*len(self.hiddenids) #hidden layer outputs 
		self.ao = [1.0]*len(self.urlids) #output layer outputs

		#create weights matrix
		self.wi = [[self.getstrength(wordid, hiddenid, 0)  #2d array of weights between input array and hidden array
					for hiddenid in self.hiddenids]		  #for each word what are the weights of all relevant hidden neurons
					for wordid in self.wordids]
		self.wo = [[self.getstrength(hiddenid, urlid, 1) #same as wi, but from hidden layer to output layer
					for urlid in self.urlids]
					for hiddenid in self.hiddenids]

	def feedforward(self):
		#only query words for inputs
		for i in xrange(len(self.wordids)): #reset input layer values to 1
			self.ai[i] = 1.0

		#hidden activations
		for j in xrange(len(self.hiddenids)):
			tot = 0.0
			for i in xrange(len(self.wordids)): #iterate through weights 2d array and apply to input layer strength
				tot += self.ai[i]*self.wi[i][j]
			self.ah[j] = tanh(tot) #set hidden layer outputs to tanh of sum of input weights axon=tanh(sum(dendrites))

		#output activations (feed forward from hidden layer)
		for k in xrange(len(self.urlids)):
			tot = 0.0
			for j in xrange(len(self.hiddenids)): 
				tot += self.ah[j]*self.wo[j][k]
			self.ao[k] = tanh(tot)

		#return the outputs of the output layer
		return self.ao[:]

	def backpropagate(self, targets, N=0.5):
		#calcuate all errors for output
		output_deltas = [0.0] * len(self.urlids)
		for k in xrange(len(self.urlids)):
			error = targets[k] - self.ao[k]
			output_deltas[k] = dtanh(self.ao[k]) * error

		#do the same for hiden layer
		hidden_deltas = [0.0] * len(self.hiddenids)
		for j in xrange(len(self.hiddenids)):
			error = 0.0
			for k in xrange(len(self.urlids)):
				error += output_deltas[k]*self.wo[j][k]
			hidden_deltas[j] = dtanh(self.ah[j])*error

		#update the weights
		for j in xrange(len(self.hiddenids)):
			for k in xrange(len(self.urlids)):
				change = output_deltas[k]*self.ah[j]
				self.wo[j][k] = self.wo[j][k] + N*change

		#update input weights
		for j in xrange(len(self.wordids)):
			for k in xrange(len(self.hiddenids)):
				change = hidden_deltas[k]*self.ai[j]
				self.wi[j][k] = self.wi[j][k] + N*change

	def trainquery(self, wordids, urlids, selectedurl):
		#generate the hidden nodes if we have new words
		self.generatehiddennode(wordids, urlids)

		self.setupnetwork(wordids, urlids)
		self.feedforward()
		targets = [0.0]*len(urlids)
		targets[urlids.index(selectedurl)] = 1.0
		self.backpropagate(targets)
		self.updatedatabase()

	def updatedatabase(self):
		#save our instance variables into the database
		for i in xrange(len(self.wordids)):
			for j in xrange(len(self.hiddenids)):
				self.setstrength(self.wordids[i], self.hiddenids[j], 0, self.wi[i][j])

		for i in xrange(len(self.hiddenids)):
			for j in xrange(len(self.urlids)):
				self.setstrength(self.hiddenids[i],self.urlids[j], 1, self.wo[i][j])
		self.con.commit()


	def getresult(self, wordids, urlids):
		self.setupnetwork(wordids, urlids)
		return self.feedforward()

