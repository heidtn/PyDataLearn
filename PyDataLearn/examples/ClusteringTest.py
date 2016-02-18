import sys
sys.path.append("../")

import Clustering
import argparse


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
	parser = argparse.ArgumentParser(description='Clusters word rss feeds by word counts.')
	parser.add_argument('file',
	                   help='a singe filename to read from (can be compiled using feedvector)')

	args = parser.parse_args()

	blognames, words, data = readfile(str(args.file))

	clust = Clustering.hcluster(data)

	Clustering.printclust(clust, labels=blognames)
