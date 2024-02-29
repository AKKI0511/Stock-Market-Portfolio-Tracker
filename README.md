# Stock Market Portfolio Tracker

A web application to manage and track your stock market portfolio. Buy and sell stocks, view your portfolio's current value, and track transaction history.

## Table of Contents
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)

## Features
- **Portfolio Overview:** View your stock portfolio's current value.
- **Buy and Sell Stocks:** Easily buy and sell stocks, updating your portfolio in real-time.
- **Transaction History:** Track all your stock transactions with details like symbol, price, and quantity.
- **Stock Quote Lookup:** Get real-time stock quotes by entering a stock symbol.

## Technologies Used
- **Flask:** Web framework for building the application.
- **SQLite:** Database to store user and stock information.
- **CS50 Library:** Used for database operations.
- **HTML, CSS, Bootstrap:** Frontend design and styling.
- **Python:** Core language for application logic.
- **Werkzeug:** Password hashing and security.
- **Yahoo Finance API:** Used to fetch real-time stock quotes.

## Getting Started
1. Clone the repository: `git clone https://github.com/yourusername/stock-portfolio-tracker.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Set up the database: `flask initdb`
4. Configure API key: Obtain a Yahoo Finance API key and set it as an environment variable `API_KEY`.
5. Run the application: `flask run`

## Usage
1. Navigate to [http://localhost:5000](http://localhost:5000) in your web browser.
2. Register a new account or log in with existing credentials.
3. Start managing your stock portfolio!

## Contributing
Contributions are welcome! Feel free to submit issues and pull requests.

## License
This project is licensed under the [MIT License](LICENSE).
