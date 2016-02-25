from math import sqrt
import random

#Hierarchical clustering
#pearson can work with different size blogs (i.e. more words overrall)
#I bet zipf lives here.  In the future lets check for disparity
def pearson(v1, v2):
	if len(v1) != len(v2):
		raise Exception("v1 not equal to v2, check the array generation")
	sum1 = sum(v1)
	sum2 = sum(v2)

	#again find the covariance
	sum1Sq = sum([pow(v, 2) for v in v1])
	sum2Sq = sum([pow(v, 2) for v in v2])

	pSum = sum([v1[i]*v2[i] for i in xrange(len(v1))])

	num = pSum - (sum1*sum2/len(v1))
	den = sqrt((sum1Sq - pow(sum1, 2)/len(v1)) * (sum2Sq - pow(sum2, 2)/len(v1)))
	if den == 0: return 0

	return 1.0 - num/den

def hcluster(rows, distance=pearson):
	distances = {}
	currentclustid = -1

	#clusters start as the rows of the dataset
	clust = [bicluster(rows[i], ID=i) for i in xrange(len(rows))]

	while len(clust) > 1:
		lowestpair = (0, 1)
		closest = distance(clust[0].vec, clust[1].vec)

		#find the next smallest distance
		for i in xrange(len(clust)):
			#print i, "/", len(clust) 
			for j in xrange(i + 1, len(clust)):
				if (clust[i].id, clust[j].id) not in distances:
					distances[(clust[i].id, clust[j].id)] = distance(clust[i].vec, clust[j].vec)

				d = distances[(clust[i].id, clust[j].id)]

				if d < closest:
					closest = d
					lowestpair = (i, j)

		#calculate the average of 2 clusters
		mergevec = [(clust[lowestpair[0]].vec[i] + clust[lowestpair[1]].vec[i])/2.0 for i in xrange(len(clust[0].vec))]

		#create the new cluster
		newcluster = bicluster(mergevec, left=clust[lowestpair[0]], right=clust[lowestpair[1]], distance=closest, ID=currentclustid)

		currentclustid -= 1

		#when we pass clust to bicluster, new instances are created so we are safe to delete the old ones.
		del clust[lowestpair[1]]
		del clust[lowestpair[0]]

		print "cluster now of size: ", len(clust)

		clust.append(newcluster)

	return clust[0]

#OH GREAT, LOOK, RECURSION (fortunately it's tail recursion...)
def printclust(clust, labels=None, n=0):
	#hieracy layout indentation!
	for i in xrange(n): print ' ',
	if clust.id < 0:
		#negative id means that this is a branch
		print '-'
	else:
		#positive id means this is an endnode
		if labels == None: print clust.id
		else: print labels[clust.id]

	if clust.left != None: printclust(clust.left, labels=labels, n=n+1)
	if clust.right != None: printclust(clust.right, labels=labels, n=n+1)


#K-means clustering
def kcluster(rows, distance=pearson, k=4):
	#determine the min and max values for each point
	ranges = [(min([row[i] for row in rows]), max([row[i] for row in rows])) for i in xrange(len(rows))]

	#create the centroids
	clusters = []
	for i in xrange(k):
		mx = ranges[i][1]
		mn = ranges[i][0]
		clusters.append([random.random()*(mx - mn) + mn for i in xrange(len(rows[0]))])

	lastmatches = None
	for t in xrange(100):
		print 'iteratiion %d' %t
		bestmatches = [[] for i in xrange(k)]

		#find which centroid is the closes to each row
		for j in xrange(len(rows)):
			row = rows[j]
			bestmatch = 0
			for i in xrange(k):
				d = distance(clusters[i], row)
				if d < distance(clusters[bestmatch], row): bestmatch = i
			bestmatches[bestmatch].append(j)

		if bestmatches == lastmatches: break
		lastmatches = bestmatches

		#move the centroids to the average
		for i in xrange(k):
			avgs = [0.0]*len(rows[0])
			if len(bestmatches[i]) > 0:
				for rowid in bestmatches[i]:
					for m in xrange(len(rows[rowid])):
						avgs[m] += rows[rowid][m]
				for j in xrange(len(avgs)):
					avgs[j] /= len(bestmatches[i])
				clusters[i] = avgs

	return bestmatches

def tanimoto(v1, v2):
	c1, c2, shr=0, 0, 0
	for i in xrange(len(v1)):
		if v1[i] != 0: c1 += 1
		if v2[i] != 0: c2 += 1
		if v1[i] != 0 and v2[i] != 0: shr += 1

	return 1.0 - (float(shr)/(c1 + c2 - shr))

# This is for 2D cluster display
def scaledown(data, distance=pearson, rate=0.01):
	n = len(data)

	#distance between every pair of items
	realdist = [[distance(data[i], data[j]) for j in xrange(n)] for i in xrange(0, n)]

	outersum = 0.0 

	#randomly initialize the starting xy locations
	loc = [[random.random(), random.random()] for i in xrange(n)]
	fakedist = [[0.0 for j in xrange(n)] for i in xrange(n)]

	lasterror = None

	for m in xrange(0, 1000):
		#Find projected distances
		for i in xrange(n):
			for j in xrange(n):
				fakedist[i][j] = sqrt(sum([pow(loc[i][x] - loc[j][x], 2) for x in xrange(len(loc[i]))]))

		grad = [[0.0, 0.0] for i in xrange(n)]

		totalerror=0
		for k in xrange(n):
			for j in xrange(n):
				if j==k: continue
				#error is percent difference between distances
				errorterm = (fakedist[j][k] - realdist[j][k])/realdist[j][k]

				#each point needs to be moved away from or towards the other in proportion to how much error it has
				grad[k][0] += ((loc[k][0] - loc[j][0]) / fakedist[j][k])*errorterm
				grad[k][1] += ((loc[k][1] - loc[j][1]) / fakedist[j][k])*errorterm

				totalerror += abs(errorterm)

		print "total error: ", totalerror

		if lasterror and lasterror < totalerror: break
		lasterror = totalerror

		for k in xrange(n):
			loc[k][0] -= rate*grad[k][0]
			loc[k][1] -= rate*grad[k][1]

	return loc

def rotatematrix(data):
	newdata = []
	for i in xrange(len(data[0])):
		newrow = [data[j][i] for j in xrange(len(data))]
		newdata.append(newrow)
	return newdata

class bicluster:
	def __init__(self, vec, left=None, right=None, distance=0.0, ID=None):
		self.left = left
		self.right = right
		self.vec = vec
		self.id = ID
		self.distance = distance

