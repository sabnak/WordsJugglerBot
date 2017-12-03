import re
from collections import OrderedDict
from numpy import array
from numpy.random import choice


def addDict(filePath):
	words = []
	rebuildedDict = filePath.replace('.txt', '_reb.txt')
	with open(filePath, "r") as f:
		for line in f:
			word = re.search(r"^[\s]+([А-ЯЁ]{3,})", line)
			if not word:
				continue
			words.append(word.groups(0))
	with open(rebuildedDict, "w") as f:
		for word in words:
			f.write("%s\n" % word)


def splitList(l, n):
	n = max(1, n)
	return [l[i:i+n] for i in range(0, len(l), n)]


def simpleDictMerge(x, y):
	z = x.copy()
	z.update(y)
	return z


def bestOfMultiple(words, weights, maxWeight=.80, percentPerPoint=5):
	weightsDict = OrderedDict([words[x], [x, y]] for x, y in enumerate([1 / len(words)] * len(words)))
	pointsDict = dict()
	minWeight = (1 - maxWeight) / (len(words) - 1)
	response = []
	for author, weightsParsed in weights.items():
		for word, weight in weightsParsed:
			if word not in pointsDict:
				pointsDict[word] = 0
			pointsDict[word] += int(weight)
			for w, k in weightsDict.items():
				if w == word:
					weightsDict[word][1] += percentPerPoint * int(weight) / 100
				else:
					weightsDict[w][1] -= percentPerPoint * int(weight) / 100 / (len(words) - 1)
	weights = array([x[1] for x in weightsDict.values()])
	for i, weight in enumerate(weights):
		# weights[i] += weights[i]/100*100
		if weight > maxWeight: weights[i] = maxWeight
		if weight < minWeight: weights[i] = minWeight
	weights /= weights.sum()
	response.append("Баллы:\n%s" % "\n".join(["%d: %s" % (p, w) for w, p in pointsDict.items()]))
	response.append("Вероятности:\n%s" % "\n".join(["%.2f: %s" % (p[1], w) for w, p in weightsDict.items()]))
	winner = choice(words, p=weights, replace=False)
	response.append("Слово-победитель: <b>%s</b>" % winner)
	return winner, dict(words=words, points=pointsDict, weights=weightsDict)
