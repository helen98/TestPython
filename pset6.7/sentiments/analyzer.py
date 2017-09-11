import nltk

class Analyzer():
    """Implements sentiment analysis."""

    def __init__(self, positives, negatives):
        """Initialize Analyzer."""

        self.positives = set()
        self.negatives = set()

        file = open(positives, "r")
        for line in file:
            if not line.startswith(";"):
                self.positives.add(line.rstrip())
        file.close()

        file = open(negatives, "r")
        for line in file:
            if not line.startswith(";"):
                self.negatives.add(line.rstrip())
        file.close()

    def analyze(self, text):
        """Analyze text for sentiment, returning its score."""

        if text.lower() in self.positives:
            return 1
        elif text.lower() in self.negatives:
            return -1
        else:
            return 0
