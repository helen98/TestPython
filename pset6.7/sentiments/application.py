from flask import Flask, redirect, render_template, request, url_for

import helpers
import os
import sys
import nltk
from analyzer import Analyzer

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search")
def search():

    # validate screen_name
    screen_name = request.args.get("screen_name", "")
    if not screen_name:
        return redirect(url_for("index"))

    # get screen_name's tweets
    tweets = helpers.get_user_timeline(screen_name)

    # check if screen name exists and is not private
    if tweets != None:

        # absolute paths to lists
        positives = os.path.join(sys.path[0], "positive-words.txt")
        negatives = os.path.join(sys.path[0], "negative-words.txt")

        # instantiate analyzer
        analyzer = Analyzer(positives, negatives)

        # analyze tweets
        positive = 0
        negative = 0
        neutral = 0
        for line in tweets:
            # separate tweets
            if not line.startswith(","):
                tweet_new = line
                tokenizer = nltk.tokenize.TweetTokenizer()
                tokens = tokenizer.tokenize(tweet_new)
                score = 0;
                for line in tokens:
                    # calculate the sentiment for entire tweet
                    score = score + analyzer.analyze(line)

                # calculate positive, negative and neutral tweets
                if score > 0.0:
                    positive = positive + 1
                elif score < 0.0:
                    negative = negative + 1
                else:
                    neutral = neutral + 1

    else:
        return redirect(url_for("index"))


    # generate chart
    chart = helpers.chart(positive, negative, neutral)

    # render results
    return render_template("search.html", chart=chart, screen_name=screen_name)
