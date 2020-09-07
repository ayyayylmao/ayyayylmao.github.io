import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
#set iur api ke for the stock quote engine
    try:
        os.environ["API_KEY"] = [pk_0910c087cae64aff9941f96298530e11 ]
    except:
        raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
        if request.method =="GET":
        
            portfolio = db.execute("SELECT * FROM portfolio WHERE id = :userID", userID=session["user_id"])
            cash = db.execute("SELECT cash FROM users WHERE id = :userID", userID=session["user_id"])
            USD = cash[0]["cash"]
            userportfolio = []
            for stock in portfolio:
                symbol = stock["symbol"]
                current = lookup(symbol)
                shares = int(stock["shares"])
                currentprice = float(current["price"])
                userportfolio.append({"symbol":symbol, "shares":shares,  "currentprice":currentprice,})

            return render_template("index.html", userportfolio=userportfolio, cash=usd(USD))
        else:
            return apology("Uh oh")



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
        if request.method =="POST":
            ticker = request.form.get("ticker")
            shares = request.form.get("shares")
            row = db.execute("SELECT cash FROM users WHERE id = :userID", userID=session["user_id"])
            account = row[0]["cash"]
            stock = lookup(ticker)
            price = stock["price"]
            transaction = (float(price)*int(shares))
            if (transaction > float(account)):
                return render_template("nocash.html")
            else:
                if (int(shares) < 1):
                    return render_template("sharesinvalid.html", shares=shares)
                else:
                    if (lookup(ticker) == None):
                        return render_template("nobuystock.html", ticker=ticker)
                    else:
                        symbol = stock["symbol"]
                        
                        if db.execute("SELECT shares FROM portfolio WHERE id = :userID AND symbol = :symbol", userID = session["user_id"], symbol=symbol):
                            db.execute("UPDATE portfolio SET shares = shares + :q WHERE id = :userID AND symbol = :symbol", userID = session['user_id'], symbol=symbol, q = shares)
                        else:
                            db.execute("INSERT INTO portfolio (id, symbol, shares, position) VALUES ( :userID, :symbol, :shares, :position)", userID = session["user_id"], symbol=symbol, shares=shares, position=transaction)
                            
                        db.execute("UPDATE users SET cash = cash - :p WHERE id = :userID", userID = session['user_id'], p = transaction)
                        db.execute("INSERT INTO history (id, symbol, shares, price) VALUES ( :userID, :symbol, :shares, :price)", userID = session["user_id"], symbol=symbol, shares=shares, price=price)
                        return render_template("bought.html", shares=shares, symbol=ticker, price=price)
                
        else:
            return render_template("buy.html")


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    if request.method =="GET":
        
        history = db.execute("SELECT * FROM history WHERE id = :userID", userID=session["user_id"])
        userhistory = []
        for stock in history:
            symbol = stock["symbol"]
            shares = stock["shares"]
            price = stock["price"]
            total = abs(shares * price)
            transacted = stock["transacted"]
            userhistory.append({"symbol":symbol, "shares":shares, "price":price, "total":total,  "transacted":transacted})
        
        return render_template("history.html", userhistory=userhistory)
    else:
        return apology("Uh oh")
    


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

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
    if request.method == "GET":
        return render_template("quote.html")
    else:
        return render_template("quoted.html")
    return apology("TODO")

@app.route("/quoted", methods=["GET", "POST"])
@login_required
def quoted():
    if request.method =="POST":
        ticker = request.form.get("symbol")
        if (lookup(ticker) == None):
            return render_template("nostock.html", ticker=ticker)
        else:
            stock = lookup(ticker)
            name = stock["name"]
            symbol = stock["symbol"]
            price = stock["price"]
            return render_template("quoted.html", name=name, symbol=symbol, price=price)
    else:
        return render_template("quoted.html", name=name, symbol=symbol, price=price)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html") 
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmpassword = request.form.get("confirmpassword")

        if password == confirmpassword:
            passwordHash = generate_password_hash(request.form.get("password"))
        else:
            return apology("Passwords do not match")        
                
        if not username:
            return apology("You must provide a username")
        if not password:
            return apology("You must provide a password")
            
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :passwordHash)", username=username, passwordHash=passwordHash)
        return render_template("login.html")
    return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
            userStocks = db.execute("SELECT symbol FROM portfolio where id = :userID", userID = session['user_id'])
            if request.method =="POST":
                ticker = request.form.get("symbol")
                shares = int(request.form.get("shares"))
                row = db.execute("SELECT shares FROM portfolio WHERE id = :userID AND symbol= :symbol", userID=session["user_id"], symbol=ticker)
                account = row[0]["shares"]
                stock = lookup(ticker)
                price = stock["price"]
                transaction = (float(price)*int(shares))
                if (int(shares) > int(account)):
                    return render_template("noshares.html",userStocks=userStocks)
                else:
                    if (int(shares) < 1):
                        return render_template("moreshares.html",userStocks=userStocks, shares=shares)
                    symbol = stock["symbol"]
                    

                    db.execute("UPDATE portfolio SET shares = shares - :q WHERE id = :userID AND symbol = :symbol", userID = session['user_id'], symbol=symbol, q = int(shares))
                    row = db.execute("SELECT shares FROM portfolio WHERE id = :userID AND symbol= :symbol", userID=session["user_id"], symbol=ticker)
                    account = row[0]["shares"]
                    if account == 0:
                        db.execute("DELETE FROM portfolio WHERE id = :userID AND symbol = :symbol", userID = session['user_id'], symbol=symbol)
                            
                    db.execute("UPDATE users SET cash = cash + :p WHERE id = :userID", userID = session['user_id'], p = transaction)
                    db.execute("INSERT INTO history (id, symbol, shares, price) VALUES ( :userID, :symbol, :shares, :price)", userID = session["user_id"], symbol=symbol, shares=-shares, price=price)
                    return render_template("sold.html",userStocks=userStocks, shares=shares, symbol=ticker, price=price)
                
            else:
                return render_template("sell.html", userStocks=userStocks)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
