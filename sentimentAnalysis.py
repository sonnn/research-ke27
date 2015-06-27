#sentiment analysis using TextBlob
from utils import Utils
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from textblob.taggers import NLTKTagger
from nltk.corpus import stopwords

import sys

class Sentiment():
	#constructor
	def __init__(self, options):
		self.utils = Utils(options)
		self.options = options

    #posts' sentiment analysis
	def analyze(self):
		#step 1: get post contents
		postContents = self.utils.get_post(self.options)

		#step 2: calculate polarity
		posTotal = posCount = negTotal = negCount = neuCount = 0
		maxPos = maxNeg = maxPosId = maxNegId = 0
		maxPosAuthor = maxNegAuthor = ""
		for content in postContents:
			tempString = self.removeStopWords(content[2])
			tempPolarity = tempString.sentiment.polarity
			if tempPolarity > 0:
				posTotal += tempPolarity
				posCount += 1
				if maxPos < tempPolarity:
					maxPos = tempPolarity
					maxPosId = content[0]
					maxPosAuthor = content[1]
			elif tempPolarity < 0:
				negTotal += tempPolarity
				negCount += 1
				if maxNeg > tempPolarity:
					maxNeg = tempPolarity
					maxNegId = content[0]
					maxNegAuthor = content[1]
			else:
				neuCount += 1

		print "Total post: " + str(len(postContents))
		print "Number of positive post: " + str(posCount)
		if posCount > 0:
			print " average polarity: " + str(posTotal / posCount)
			print " most positive: post " + str(maxPosId) + " of " + str(maxPosAuthor)
		print "Number of negative post: " + str(negCount)
		if negCount > 0:
			print " average polarity: " + str(negTotal / negCount)
			print " most negative: post " + str(maxNegId) + " of " + str(maxNegAuthor)
		print "Number of neutral post: " + str(neuCount)
		
		#considering step
		#machine learning: Naive Bayes classifier
		'''
		if 1 == 0:
			posCount = negCount = neuCount = 0
			for content in postContents:
				tempString = TextBlob(content, analyzer = NaiveBayesAnalyzer())
				classification = tempString.sentiment.classification
				if classification == "pos":
					posCount += 1
				elif classification == "neg":
					negCount += 1
				else:
					neuCount += 1
			print "(positive: " + str(posCount) + ", neutral: " + str(neuCount) + ", negative: " + str(negCount) + ")"

		#tokenize words -> remove stopwords -> combine to one words set
		if 1 == 0:
			finalWords = []
			for content in postContents:
				tempString = TextBlob(content)
				finalWords += [word for word in tempString.words if word.lower() not in stopwords]
			tempString.words = finalWords
			tempString.words = tempString.ngrams(n=2)
			print tempString.words
			print tempString.sentiment
		

	def testFunc(self):
		test = TextBlob(postContents[0])
		#word segmentation/tokenization
		if 1 == 0:
			print test.words

		#sentence tokenization
		if 1 == 0:
			print test.sentences
			print test.sentences[0].sentiment

		#Part-Of-Speech tagging
		if 1 == 0:
			print test.tags #default tagger is based on pattern
			#tag by NTLK Treebank
			test2 = TextBlob(postContents[0], pos_tagger=NLTKTagger())
			print test2.pos_tags
			print test.tags == test2.pos_tagger

		#noun phrases extraction
		if 1 == 0:
			print test.noun_phrases

		#spelling correction
		if 1 == 0:
			print test.correct()

		#lemmatization
		if 1 == 0:
			print test.words.lemmatize()

		#n-grams
		if 1 == 0:
			print test.ngrams(n=2)

		#stop-words
		if 1 == 0:
			print stopwords.words("english")
			content = [w for w in test.words if w.lower() not in stopwords.words("english")]
			print content
			print len(content)
			print len(test.words)
		'''
	#return TextBlob Word object after remove stopwords
	def removeStopWords(self, string):
		tempString = TextBlob(string)
		tempString.words = [word for word in tempString.words if word.lower() not in stopwords]
		return tempString

if __name__ == '__main__':
	try:
		threadId = sys.argv[1]
		main = Sentiment({'thread_id': threadId})
		stopwords = stopwords.words("english")
		main.analyze()
	except IndexError:
		print "No thread id"