import math

#collaborative filter for small data sets (i.e. < ~20,000)


class CollaborativeFilter:
	def __init__(self):
		self.rawData = {}

	#takes a dictionary of dictionaries of format {id: {rating1: rating, rating2: rating ...}...}
	def loadDataFromDict(self, dataDict):
		self.rawData = dataDict

	#general d^2 = x^2 + y^2 + z^2 + ... formula for distance.
	#takes 2 dictionaries of format {rating1: rating, rating2: rating ...}
	def euclideanDistance(self, rater1, rater2):
		si = {}
		for item in rater1:
			if item in rater2:
				si[item] = 1

		#if they have no matching items
		if len(si) == 0: return 0

		sum_of_squares = sum([(rater1[item] - rater2[item])**2 for item in si])
		return 1/(1 + sqrt(sum_of_squares)) #higher number for more similar people

	#essentially the covariance of the data.
	#takes 2 dictionaries of format {rating1: rating, rating2: rating ...}
	def pearsonCorrelation(self, rater1, rater2):
		si = {}
		for item in rater1:
			if item in rater2:
				si[item] = 1

		n = len(si)

		if n == 0: return 0

		sum1 = sum([rater1[item] for item in si])
		sum2 = sum([rater2[item] for item in si])

		sum1Sq = sum([rater1[item]**2.0 for item in si])
		sum2Sq = sum([rater2[item]**2.0 for item in si])

		pSum = sum([rater1[item]*rater2[item] for item in si])

		#this is all stastical modelling.  The fit is the width of the covariance

		num = pSum - (sum1*sum2/n)
		den = math.sqrt((sum1Sq - math.pow(sum1,2)/n)*(sum2Sq - math.pow(sum2,2)/n))

		if den == 0: return 0

		return num/den
		

	def topMatches(self, person, n=5, similarity=None):
		similarity = similarity or self.pearsonCorrelation
		scores = [(similarity(self.rawData[person], self.rawData[other]),other) for other in self.rawData if other!=person]
		lists = [other for other in self.rawData if other!=person]
		scores.sort()
		scores.reverse()
		return scores[0:n]

	def getRecommendations(self, person, similarity=None):
		similarity = similarity or self.pearsonCorrelation
		totals = {}
		simSums = {}
		for other in self.rawData:
			if other == person: continue
			sim = similarity(self.rawData[person], self.rawData[other])

			if sim <= 0: continue

			for item in self.rawData[other]:
				if item not in self.rawData[person] or self.rawData[person][item] == 0:
					totals.setdefault(item, 0)
					totals[item] += self.rawData[other][item]*sim

					simSums.setdefault(item, 0)
					simSums[item] += sim

		rankings = [(total/simSums[item], item) for item,total, in totals.items()]
		rankings.sort()
		rankings.reverse()

		return rankings


