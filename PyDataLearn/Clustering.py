from math import sqrt


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

	pSum = sum([v1[i]*v2[i] for i in range(len(v1))])

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
			for j in xrange(i + 1, len(clust)):
				if(clust[i].id, clust[j].id) not in distances:
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
	for i in range(n): print ' ',
	if clust.id < 0:
		#negative id means that this is a branch
		print '-'
	else:
		#positive id means this is an endnode
		if labels == None: print clust.id
		else: print labels[clust.id]

	if clust.left != None: printclust(clust.left, labels=labels, n=n+1)
	if clust.right != None: printclust(clust.right, labels=labels, n=n+1)

class bicluster:
	def __init__(self, vec, left=None, right=None, distance=0.0, ID=None):
		self.left = left
		self.right = right
		self.vec = vec
		self.id = ID
		self.distance = distance

