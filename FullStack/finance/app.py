import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# my addition
from datetime import datetime

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # check if user is logged in
    if not session["user_id"]:
        # go to login screen
        return redirect("/login")
    # if user is logged in
    else:
        # get users's cash reserves
        userID = session["user_id"]
        CASH = db.execute("SELECT * FROM users WHERE id = ?", userID)
        name = CASH[0]['username']
        CASH = int(CASH[0]['cash'])

        PORTFOLIO = computePortfolio(name)

        # compute total value(stock+cash)
        STOCKVAL = 0
        for row in PORTFOLIO:
            STOCKVAL += (float(row['pps']) * float(row['quantity']))
        TOTALVAL = CASH + STOCKVAL
        return render_template("portfolio.html", portfolio=PORTFOLIO, cash=CASH, totalVal=TOTALVAL,)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # if Acessed through get(click)
    if request.method == "GET":
        return render_template("buy.html")
    # if accessed through post(buying)
    if request.method == "POST":

        # get info and make sure it's not blank
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Symbol cannot be blank", 400)
        quantity = request.form.get("shares")
        if not quantity:
            return apology("Quantity cannot be blank", 400)

        # check to make sure the symbol exists
        quote = lookup(symbol)
        if not quote:
            return apology("Symbol does not exist", 400)
        # check to make sure the quantity is not alphabetical
        if quantity.isalpha():
            return apology("Quantity must be a number", 400)
        elif not quantity.isdigit():
            return apology("Quantity must be an integer", 400)
        elif int(quantity) < 1:
            return apology("Quantity must be a positive integer", 400)

        # _______________________________________________________________________

        # calculate the total price
        price = float(quantity) * float(quote['price'])

        # check if the user can afford it
        userID = session["user_id"]
        userBalance = db.execute("SELECT cash FROM users WHERE id = ?", userID)
        userBalance = float(userBalance[0]['cash'])
        if (userBalance - price) < 0:
            return apology("insufficient funds", 400)
        # update user's total
        userBalance = userBalance - price
        db.execute("UPDATE users SET cash = ? WHERE id= ?", userBalance, userID)
        # add entry to history table showing user, stock, qty, date
        date = datetime.now()
        user = db.execute("SELECT username FROM users WHERE id = ?", userID)
        user = user[0]['username']
        db.execute("INSERT INTO history (username, stock, quantity, pps, date, type) VALUES(?, ?, ?, ?, ?, 'B')",
                   user, quote['symbol'], quantity, quote['price'], date)

        # redirect back to home
        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    HISTORY = db.execute("SELECT * FROM history")
    return render_template("history.html", history=HISTORY)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    #  If reached by get, show the templatw
    if request.method == "GET":
        return render_template("quote.html")

    # If reached by post, get the info
    if request.method == "POST":
        # do lookup??
        stockSymbol = request.form.get("symbol")
        if not stockSymbol:
            return apology("Enter a Symbol", 400)

        # STOCK = {'name': string, 'price': number, 'symbol': 'string'}
        QUOTE = lookup(stockSymbol)

        # check if symbol is invalid
        if not QUOTE:
            return apology("Invalid symbol", 400)
        else:
            # render quotes with the lookup values
            # TEST RENDER THE VALUE AS USD
            # QUOTE['price'] = usd(QUOTE['price'])
            return render_template("quoted.html", quote=QUOTE)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    #  If user reached by get??
    if request.method == "POST":

        # capture the username as variable
        name = request.form.get("username")

        # make sure the username is not blank
        if not name:
            return apology("Username cannot be blank", 400)

        # check to make sure username doesnt already exist
        rows = db.execute("SELECT * FROM users WHERE username = ?", name)
        if (len(rows) != 0):
            return apology("Username already exists", 400)

        # check to make sure the username doesnt already exist
        pwd = request.form.get("password")
        confirmPWD = request.form.get("confirmation")

        if not pwd:
            return apology("Password cannot be blank", 400)
        if not confirmPWD:
            return apology("Retype password to confirm", 400)

        # check to make sure password matches confirm
        if pwd != confirmPWD:
            return apology("Password and confirmation must match")

         # put it in the db
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", name, generate_password_hash(pwd))
        return redirect("/")

    # User clicked a link??
    if request.method == "GET":
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # If acessed by POST(input)
    if request.method == "POST":
        # get the info
        symbol = request.form.get("symbol")
        qty = int(request.form.get("shares"))
        quote = lookup(symbol)

        # check symbol for blank and validity
        if not symbol:
            return apology("Please enter a symbol", 400)
        elif not quote:
            return apology("Invalid symbol", 400)

        # check quantity for blank and validity
        if not qty:
            return apology("Please enter a quantity", 400)
        elif (int(qty) < 1):
            return apology("Quantity must be a nonzero positive", 400)

        # sell the stock
        userID = session["user_id"]
        user = db.execute("SELECT * FROM users WHERE id = ?", userID)
        # compute portfolio
        PORTFOLIO = computePortfolio(user[0]['username'])

        # verify quantity
        for d in PORTFOLIO:
            if not any(f['stock'] == symbol for f in PORTFOLIO):
                return apology("you do not any of that stock", 400)
            # find the specified stock
            if d['stock'] == symbol:
                # check if the quantity is correct
                if d['quantity'] > qty:
                    # compute how much money is made
                    newCash = d['pps'] * qty
                    # remove stocks
                    d['quantity'] -= qty
                    # update history and current balance
                    db.execute("UPDATE users SET cash = ? WHERE id= ?", user[0]['cash'] + newCash, userID)
                    db.execute("INSERT INTO history (username, stock, quantity, pps, date, type) VALUES (?, ?, ?, ?, ?, 'S')",
                               user[0]['username'], symbol, qty, quote['price'], datetime.now())
                else:
                    return apology("You do not have that much to sell", 400)

    # If accessed by GET(click)
    if request.method == "GET":
        # display the template for selling
        return render_template("sell.html")
    return redirect("/")


def computePortfolio(name):
    # get record of user's transactions
    history = db.execute("SELECT * FROM history WHERE username = ?", name)

    # update the price per share
    for row in history:
        val = lookup(row['stock'])
        row['pps'] = val['price']

    # build up the portfolio based on buys and sells
    PORTFOLIO = []
    for row in history:
        # check if already present
        if not any(d['stock'] == row['stock'] for d in PORTFOLIO):
            # not found
            PORTFOLIO.append(row)

        else:
            # already found
            for d in PORTFOLIO:
                # for every matching element
                if d['stock'] == row['stock']:
                    # if it has been bought, increase quantity
                    if row['type'] == 'B':
                        d['quantity'] = int(d['quantity']) + int(row['quantity'])

                    # if it has been sold, decrease quantity
                    if row['type'] == 'S':
                        d['quantity'] = int(d['quantity']) - int(row['quantity'])
    return PORTFOLIO


@app.route("/addCash", methods=["GET", "POST"])
@login_required
def addCash():
    # if clicked on(GET)
    if request.method == "GET":
        return render_template("addCash.html")
    # if submitted(POST)
    if request.method == "POST":
        newCash = int(request.form.get("cashAmount"))
        if (newCash < 0):
            return apology("cash must be positive", 403)
        else:
            userID = session["user_id"]
            user = db.execute("SELECT * FROM users WHERE id = ?", userID)
            db.execute("UPDATE users SET cash = ? WHERE id = ?", int(user[0]['cash']) + newCash, userID)
            return redirect("/")
