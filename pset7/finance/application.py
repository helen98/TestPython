from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    # select information about all the stocks user bought from portfolio
    try:
        stocks = db.execute("SELECT * FROM portfolio WHERE id = :user_id", user_id=session["user_id"])

        total_price = 0

        # iterate over stocks, lookup current price for stocks, how many shares of each stock were bought and their sum
        for stock in stocks:
            stock["stockPrice"] = lookup(stock["symbol"])["price"]
            shares = stock["shares"]
            stock["TOTAL"] = float(stock["stockPrice"]) * float(shares)
            stock["TOTAL"] = usd(stock["TOTAL"])
            stock["stockPrice"] = usd(stock["stockPrice"])

        # check amount of cash left
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])
        cash = float(cash[0]["cash"])

        grand_price = total_price + cash

        # display user's portfolio
        return render_template("index.html", stocks = stocks, cash = usd(cash), total_price = usd(grand_price))

    except RuntimeError:
        print ('error________________________')
        return render_template("index.html", stocks = [], cash = usd(10000), total_price = usd(10000))





@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure stockname was input
        if not request.form.get("stock"):
            return apology("must provide stockname")

        # call lookup to see the price of the stock
        stock = lookup(request.form.get("stock"))

        # ensure stockname is valid
        if stock == None:
            return apology("stockname is not valid")

        # ensure number of shares is input
        if not request.form.get("number"):
            return apology("must provide number of shares")
        number = int(request.form.get("number"))

        # ensure number of shares is not a negative integer
        if number <= 0:
            return apology("number of shares is not valid")

        # remember user id
        id = session["user_id"]

        # remember stock symbol
        symbol = request.form.get("stock")

        # select name and price information from lookup result
        price = float(stock["price"])
        name = stock["name"]

         # check current amount of cash
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=id)
        cash = float(cash[0]["cash"])
        print(cash)

        # ensure user can afford purchase
        total_price = price * number
        if total_price > cash:
            return apology("not enough cash")

        # update cash amount
        cash = cash - price * number

        # check if user has already bought this stock before
        check_shares = db.execute("SELECT shares FROM portfolio WHERE id = :user_id and symbol = :symbol", user_id=id, symbol=symbol)
        if check_shares == []:
            db.execute("INSERT INTO portfolio (id, symbol, name, shares, price, TOTAL) VALUES (:userid, :symbol, :name, :shares, :price, :TOTAL)", userid=id, symbol=symbol, name=name, shares=number, price=price, TOTAL=total_price)
            # update history information
            db.execute("INSERT INTO history (id, symbol, shares, price) VALUES (:userid, :symbol, :shares, :price)", userid=id, symbol=symbol, shares=number, price=price)
            # update amount of cash user has
            db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash=cash, user_id=id)

        else:
            check_shares = int(check_shares[0]["shares"])
            # update number of shares in user's profile
            shares = check_shares + number
            check_TOTAL = db.execute("SELECT TOTAL FROM portfolio WHERE id = :user_id and symbol = :symbol", user_id=id, symbol=symbol)
            check_TOTAL = float(check_TOTAL[0]["TOTAL"])
            # update TOTAL in user's profile
            TOTAL = check_TOTAL + number * price
            db.execute("UPDATE portfolio SET shares = :shares WHERE id = :user_id and symbol = :symbol", shares=shares, user_id=id, symbol=symbol)
            db.execute("UPDATE portfolio SET TOTAL = :TOTAL WHERE id = :user_id and symbol = :symbol", TOTAL=TOTAL, user_id=id, symbol=symbol)
            # update history information
            db.execute("INSERT INTO history (id, symbol, shares, price) VALUES (:userid, :symbol, :shares, :price)", userid=id, symbol=symbol, shares=number, price=price)
            # update amount of cash user has
            db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash=cash, user_id=id)


       # display user's portfolio
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    # select information from history
    stocks = db.execute("SELECT * FROM history WHERE id = :user_id", user_id=session["user_id"])
    for stock in stocks:
        stock["price"] = usd(stock["price"])

    # display user's history
    return render_template("history.html", stocks=stocks)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure stockname was input
        if request.form["stock"] == "":
            return apology("must provide stock's symbol")
        # call function lookup
        quote = lookup(request.form.get("stock"))

        # check if stock symbol exists
        if quote == None:
            return apology("stock is not valid")
        else:
            price = usd(quote["price"])
            name = quote["name"]
            return render_template("quoted.html", name = name, price = price, symbol = request.form.get("stock"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    return render_template("quote.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username and password was input and passwords match
        if request.form["username"] == "":
            return apology("must provide username")
        if request.form["password"] == "":
            return apology("must provide password")
        if request.form["confirm_password"] == "":
            return apology("confirm your password")
        if not request.form["password"] == request.form["confirm_password"]:
            return apology("passwords do not match")

        # insert user in database
        hash = pwd_context.hash(request.form.get("password"))
        result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :password)", username=request.form.get("username"), password=hash)

        # check if this username is available
        if not result:
            return apology("this username already exists")

        else:
            session ["user_id"] = db.execute("SELECT id FROM users WHERE username = :username", username=request.form.get("username"))

            # redirect user to home page
            return redirect(url_for("login"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure stockname was input
        if not request.form.get("stock"):
            return apology("must provide stockname")

        # call lookup to see the price of the stock
        stock = lookup(request.form.get("stock"))

        # ensure stockname is valid
        if stock == None:
            return apology("stockname is not valid")

        # ensure number of shares is input
        if not request.form.get("number"):
            return apology("must provide number of shares")
        number = int(request.form.get("number"))

        # ensure number of shares is not a negative integer
        if number <= 0:
            return apology("number of shares is not valid")

        # remember user id
        id = session["user_id"]

        # remember stock symbol
        symbol = request.form.get("stock")

        # select name and price information from lookup result
        price = float(stock["price"])
        name = stock["name"]



        # check if user has this stock
        check_shares = db.execute("SELECT shares FROM portfolio WHERE id = :user_id and symbol = :symbol", user_id=id, symbol=symbol)
        if check_shares == []:
            return apology("you don't have this stock")
        else:
            check_shares = int(check_shares[0]["shares"])
            if check_shares < number:
                return apology("you don't have that many")
            else:
                # update number of shares in user's profile
                number = 0 - number
                # check current amount of cash
                cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=id)
                cash = float(cash[0]["cash"])
                # update cash amount
                cash = cash - price * number
                shares = check_shares + number
                check_TOTAL = db.execute("SELECT TOTAL FROM portfolio WHERE id = :user_id and symbol = :symbol", user_id=id, symbol=symbol)
                check_TOTAL = float(check_TOTAL[0]["TOTAL"])
                # update TOTAL in user's profile
                TOTAL = check_TOTAL + number * price
                db.execute("UPDATE portfolio SET shares = :shares WHERE id = :user_id and symbol = :symbol", shares=shares, user_id=id, symbol=symbol)
                db.execute("UPDATE portfolio SET TOTAL = :TOTAL WHERE id = :user_id and symbol = :symbol", TOTAL=TOTAL, user_id=id, symbol=symbol)
                # update history information
                db.execute("INSERT INTO history (id, symbol, shares, price) VALUES (:userid, :symbol, :shares, :price)", userid=id, symbol=symbol, shares=number, price=price)
                # update amount of cash user has
                db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash=cash, user_id=id)


       # display user's portfolio
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("sell.html")

@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Change user's password."""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure old password was submitted
        if not request.form.get("password_old") or not request.form.get("password_new"):
            return apology("must provide password")
        else:
            # query database for old password
            rows = db.execute("SELECT hash FROM users WHERE id = :id", id=session["user_id"])
            # check if password input by user matches the db password
            if not pwd_context.verify(request.form.get("password_old"), rows[0]["hash"]):
                return apology("password is not valid")
            # change password
            hash = pwd_context.hash(request.form.get("password_new"))
            result = db.execute("UPDATE users SET hash = :password WHERE id = :id", password=hash, id=session["user_id"])
            # display user's portfolio
            return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("password.html")


