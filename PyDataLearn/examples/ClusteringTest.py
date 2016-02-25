import sys
sys.path.append("../")

import Clustering
import argparse
import Dendrogram

"""
generate word counts or other metrics via feedvector.py and pip the resulting file through here
"""


def readfile(filename):
	lines = [line for line in open(filename)]

	colnames = lines[0].strip().split('\t')[1:]
	rownames = []
	data = []
	for line in lines[1:]:
		p = line.strip().split('\t')
		rownames.append(p[0]) #name of the source
		data.append([float(x) for x in p[1:]]) #append column names

	return rownames, colnames, data




if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Clusters word rss feeds by word counts. Uses hcluster unless specified otherwise')
	parser.add_argument('file',
	                   help='a singe filename to read from (can be compiled using feedvector)')
	parser.add_argument("--draw", "-d",
						help='this outputs a dendrogram jpg for hclusters and a 2d map for kclusters', action="store_true")
	parser.add_argument("--rotate", "-r",
						help='flip the rows and colums', action="store_true")
	parser.add_argument("--kcluster", "-k",
					    help="uses a kcluster instead of an hcluster", action="store_true")
	parser.add_argument("--scaledown", "-s",
						help="uses scaling algorithm for clustering display", action="store_true")

	args = parser.parse_args()

	blognames, words, data = readfile(str(args.file))

	if args.rotate:
		data = Clustering.rotatematrix(data)
		print "data rotated"

	if args.kcluster:
		clust = Clustering.hcluster(data)
	else:
		clust = Clustering.hcluster(data)

	if args.rotate:
		Clustering.printclust(clust, labels=words)
	else:
		Clustering.printclust(clust, labels=blognames)

	if(args.draw):
		if args.kcluster:
			print repr(kcluster)
		elif args.scaledown:
			coords = Clustering.scaledown(data)
			Dendrogram.draw2d(coords, blognames)
		else:
			Dendrogram.drawdendrogram(clust, blognames, jpeg='blogclust.jpg')
