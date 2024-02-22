import os
import urllib.parse

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

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


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]

    if request.method == "POST":
        symbol_buy_sell = request.form.get("symbol_buy/sell")
        num_of_shares = int(request.form.get("buy_sell"))

        if not symbol_buy_sell or num_of_shares < 1:
            return apology("Invalid input")

        stock_buy_sell = lookup(symbol_buy_sell)

        if stock_buy_sell is None:
            return apology("Invalid symbol")

        if "buy" in request.form:
            # Buy the stock
            stock_info = lookup(symbol_buy_sell)
            if stock_info is None:
                return apology("Invalid symbol")

            price_per_share = stock_info["price"]
            total_cost = price_per_share * num_of_shares

            # Check if the user has enough cash to buy the stock
            cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
            if cash < total_cost:
                return apology("Not enough cash")

            # Update the user's cash balance
            db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", total_cost, user_id)

            # Update the stocks table
            existing_stock = db.execute("SELECT * FROM Stocks WHERE username_id = ? AND symbol = ?", user_id, symbol_buy_sell)
            if existing_stock:
                db.execute("UPDATE Stocks SET quantity = quantity + ? WHERE username_id = ? AND symbol = ?",
                           num_of_shares, user_id, symbol_buy_sell)
            else:
                db.execute("INSERT INTO Stocks (symbol, quantity, price, purchase_date, username_id) VALUES (?, ?, ?, ?, ?)",
                           symbol_buy_sell, num_of_shares, price_per_share, datetime.now(), user_id)

        elif "sell" in request.form:
            # Sell the stock
            existing_stock = db.execute("SELECT * FROM Stocks WHERE username_id = ? AND symbol = ?", user_id, symbol_buy_sell)
            if not existing_stock:
                return apology("You don't own any shares of this stock")

            current_quantity = existing_stock[0]["quantity"]
            if num_of_shares > current_quantity:
                return apology("Not enough shares to sell")

            stock_info = lookup(symbol_buy_sell)
            if stock_info is None:
                return apology("Invalid symbol")

            price_per_share = stock_info["price"]
            total_sale_value = price_per_share * num_of_shares

            # Update the user's cash balance
            db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", total_sale_value, user_id)

            # Update the stocks table
            if num_of_shares == current_quantity:
                db.execute("DELETE FROM Stocks WHERE username_id = ? AND symbol = ?", user_id, symbol_buy_sell)
            else:
                db.execute("UPDATE Stocks SET quantity = quantity - ? WHERE username_id = ? AND symbol = ?",
                           num_of_shares, user_id, symbol_buy_sell)

        return redirect("/")

    else:
        # Retrieve the current stock prices from the API
        rows = db.execute("SELECT symbol, SUM(quantity) AS total_quantity FROM Stocks WHERE username_id = ? GROUP BY symbol", user_id)
        stocks = []
        total_stocks_value = 0
        for stock in rows:
            symbol = stock["symbol"]
            quantity = stock["total_quantity"]
            stock_info = lookup(symbol)
            if stock_info is not None:
                price = stock_info["price"]
                total_value = price * quantity
                total_stocks_value += total_value
                stocks.append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": price,
                    "total_value": total_value
                })

        # Retrieve the current cash balance of the user
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

        # Calculate the grand total
        grand_total = total_stocks_value + cash

        return render_template("index.html", stocks=stocks, cash=cash, grand_total=grand_total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # Retrieve symbol, shares, and stock information
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        stock = lookup(symbol)

        # Check if the user already owns the stock
        user_id = session["user_id"]
        existing_stock = db.execute("SELECT * FROM Stocks WHERE username_id = ? AND symbol = ?", user_id, symbol)

        if existing_stock:
            # Update the existing stock entry with the latest price and quantity
            db.execute("UPDATE Stocks SET quantity = quantity + ?, price = ? WHERE username_id = ? AND symbol = ?",
                       shares, stock["price"], user_id, symbol)
        else:
            # Insert a new stock entry for the user
            db.execute("INSERT INTO Stocks (symbol, quantity, price, purchase_date, username_id) VALUES (?, ?, ?, ?, ?)",
                       symbol, shares, stock["price"], datetime.now(), user_id)

        # Deduct the total cost from the user's cash balance
        total_cost = stock["price"] * shares
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", total_cost, user_id)

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    transactions = db.execute("SELECT symbol, price, purchase_date, quantity FROM Stocks WHERE username_id = ?", user_id)
    return render_template("history.html", transactions=transactions)


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
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("symbol not found", 400)
        symbol = request.form.get("symbol")
        stock = lookup(symbol)
        return render_template("quoted.html", stock=stock)

    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        elif request.form.get("password") != request.form.get("confirmation") or not request.form.get("confirmation"):
            return apology("password does not match", 403)

        password = request.form.get("password")
        password_hash = generate_password_hash(password)

        db.execute("INSERT INTO users(username, hash) VALUES(?, ?)", request.form.get("username"), password_hash)

    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session["user_id"]

    if request.method == "POST":
        symbol_for_sell = request.form.get("symbol")
        shares_to_sell = int(request.form.get("shares"))

        if not symbol_for_sell or not shares_to_sell:
            return apology("Please provide all details")

        stock = lookup(symbol_for_sell)

        if not stock:
            return apology("Invalid symbol")

        original_num_of_stocks = db.execute("SELECT SUM(quantity) as total_quantity FROM Stocks WHERE username_id = ? AND symbol = ? GROUP BY symbol", user_id, symbol_for_sell)

        if not original_num_of_stocks or original_num_of_stocks[0]["total_quantity"] is None:
            return apology("You don't own any shares of this stock")

        original_num_of_stocks = original_num_of_stocks[0]["total_quantity"]

        if shares_to_sell < 1 or shares_to_sell > original_num_of_stocks:
            return apology("Invalid number of shares")

        sell_price = stock["price"]
        total_sell_value = sell_price * shares_to_sell

        # Update the user's cash balance
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", total_sell_value, user_id)

        # Update the stocks table by subtracting the sold shares
        db.execute("INSERT INTO Stocks (symbol, quantity, price, purchase_date, username_id) VALUES (?, ?, ?, ?, ?)",
                   symbol_for_sell, -shares_to_sell, sell_price, datetime.now(), user_id)

        # Check if the user has completely sold all shares of the stock
        remaining_shares = original_num_of_stocks - shares_to_sell
        if remaining_shares == 0:
            db.execute("DELETE FROM Stocks WHERE username_id = ? AND symbol = ?", user_id, symbol_for_sell)

        return redirect("/")
    else:
        # Fetch the symbols of stocks owned by the user
        symbols = db.execute("SELECT DISTINCT symbol FROM Stocks WHERE username_id = ?", user_id)
        return render_template("sell.html", symbols=symbols)
