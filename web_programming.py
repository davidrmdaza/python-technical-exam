from typing import List
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "davidraphaeldaza-filcan"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stocks.db'  # Database file
db = SQLAlchemy(app)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    def __init__(self, stock_id: int, name: str, price: float)  -> None:
        self.id = stock_id
        self.name = name
        self.price = price

    def __str__(self) -> str:
        return self.name + " : $" + str(self.price)

    def to_dict(self):
        """Converts stock data into a dictionary."""
        return {"stock_id": self.id, "name": self.name, "price": self.price}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float, default=0.0)
    def __init__(self,id:int) -> None:
        self.id = id
        self.stocks = {}
        self.balance = 0.0
    def adjust_stock_quantity(self, stock_id: int, quantity: float) -> None:
        result = self.stocks.get(stock_id,0.0) + quantity
        if (result) > 0:
            self.stocks[stock_id] = result
        else:
            raise ValueError("Stock quantity insufficient")
    def adjust_balance(self, balance: float) -> None:
        result = self.balance + balance
        if(result>0):
            self.balance = result
        else:
            raise ValueError("User balance insufficient")
    def get_stock_quantity(self, stock_id: int) -> int:
        return self.stocks.get(stock_id,0)
    def get_stocks(self) -> dict:
        return self.stocks
    def get_balance(self) -> float:
        return self.balance
    def get_id(self) -> int:
        return self.id
    def to_dict(self):
        return {
        "user_id": self.id,
        "balance": self.balance,
        "stocks": {s.stock_id: s.quantity for s in self.stocks}
        }

with app.app_context():
    db.create_all()

@app.route('/get-stock', methods=['GET'])
def get_stock():
    stock_id = request.args.get("stock_id", type=int)
    stock = Stock.query.get(stock_id)
    
    if not stock:
        return jsonify({"error": "Stock not found"}), 404
    
    return jsonify({"stock_id": stock.id, "name": stock.name, "price": stock.price})

@app.route('/get-user', methods=['GET'])
def get_user():
    user_id = request.args.get("user_id", type=int)
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"user_id": user.id, "balance": user.balance})

def get_user_stock_value(user_id: int, stock_id: int) -> (float, str):
    user = get_user(user_id)
    stock = get_stock(stock_id)
    user_quantity = user.get_stock_quantity(stock_id)
    return user_quantity*stock.price, stock.__str__(), user_quantity

def get_user_portfolio_total(user: User) -> (float, List[str]):
    total = 0
    report = []
    for stock_id in user.get_stocks():
        value, stock_info, stock_total = get_user_stock_value(user, stock_id)
        total += value
        report.append(stock_info + " | " + str(stock_total) + " units with total value: " + str(value))
    
    return total, report


def buy_stock(user_id: int, stock_id: int, quantity) -> None:
    stock = get_stock(stock_id)
    user = get_user(user_id)
    if (quantity<0):
        raise ValueError("Negative quantity provided.")
    if (stock.price*quantity > user.get_balance()):
        raise ValueError("Insufficient balance.")
    else:
        user.adjust_stock_quantity(stock_id, quantity)
        user.adjust_balance(-stock.price*quantity)

def sell_stock(user_id: int, stock_id: int, quantity) -> None:
    stock = get_stock(stock_id)
    user = get_user(user_id)
    if (quantity<0):
        raise ValueError("Negative quantity provided.")
    else:
        user.adjust_stock_quantity(stock_id, -quantity)
        user.adjust_balance(stock.price*quantity)




@app.before_request
def initialize_data():
    if not hasattr(app, 'data_initialized'):
        session['stocks'] = [
            Stock(1, "A", 1.23).to_dict(),
            Stock(2, "B", 4.56).to_dict(),
            Stock(3, "C", 0.90).to_dict(),
            Stock(4, "D", 1.03).to_dict(),
            Stock(5, "E", 3.23).to_dict()
        ]
        user = User(1)
        user.adjust_balance(10000)
        user.adjust_stock_quantity(1, 100)
        user.adjust_stock_quantity(2, 100)
        user.adjust_stock_quantity(3, 100)
        user.adjust_stock_quantity(4, 100)
        user.adjust_stock_quantity(5, 100)
        session['users'] = [user.to_dict()]
        app.data_initialized = True  # Prevents multiple executions
        print("Session data initialized!")

@app.post("/buy-stock")
def user_buy_stock():
    user_id = request.args.get("user_id", type=int)
    stock_id = request.args.get("stock_id", type=int)
    qty = request.args.get("qty", type=float)
    try:
        buy_stock(user_id, stock_id, qty)
        return jsonify({"stock": stock_id, "quantity": qty}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

        
@app.post("/sell-stock")
def user_sell_stock():
    user_id = request.args.get("user_id", type=int)
    stock_id = request.args.get("stock_id", type=int)
    qty = request.args.get("qty", type=float)
    try:
        sell_stock(user_id, stock_id,qty)
        return jsonify({"stock": stock_id, "quantity": qty}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    
@app.get("/get-portfolio")
def user_get_portfolio():
    

    for u in AVAILABLE_USERS:
        print(u.get_id())
    for s in AVAILABLE_STOCKS:
        print (s)
    try:
        user_id = request.args.get("user_id", type=int)
        user = get_user(1)
        result = get_user_portfolio_total(user)
        return jsonify({"result": result,})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
        
    
@app.get("/get-user-stock")
def user_get_stock():
    try:
        user_id = request.args.get("user_id", type=int)
        stock_id = request.args.get("stock_id", type=int)
        user = get_user(user_id)
        result = get_user_stock_value(user, stock_id)
        return jsonify({"result": result,})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
        

if __name__ == '__main__':
    app.debug = True
    app.run()
