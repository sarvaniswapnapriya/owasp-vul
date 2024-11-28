from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import hashlib
import time

app = Flask(__name__)
app.config.from_object('config')

users_db = {
    "user1": {"password": hashlib.md5("user1password".encode()).hexdigest(), "balance": "5000", "bank_account": "123-456-7890"},
    "user2": {"password": hashlib.md5("user2password".encode()).hexdigest(), "balance": "3000", "bank_account": "987-654-3210"},
    "admin": {"password": hashlib.md5("admin123".encode()).hexdigest(), "balance": "1000000", "bank_account": "111-222-3333"}
}

def get_db():
    return sqlite3.connect('financial_data.db')

def create_db():
    conn = get_db()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, balance TEXT, bank_account TEXT)')
    conn.commit()
    conn.close()

create_db()

login_attempts = {}

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    hashed_password = hashlib.md5(password.encode()).hexdigest()

    if username in users_db and users_db[username]["password"] == hashed_password:
        session["user"] = username
        if username == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("dashboard"))
    
    if username in login_attempts:
        login_attempts[username] += 1
    else:
        login_attempts[username] = 1
    
    if login_attempts[username] > 5:
        return "Too many login attempts, try again later.", 429  

    return "Invalid credentials", 401

@app.route("/dashboard")
def dashboard():
    if "user" in session:
        username = session["user"]
        user_data = users_db[username]
        return render_template("dashboard.html", username=username, balance=user_data["balance"], bank_account=user_data["bank_account"])
    return redirect(url_for("home"))

@app.route("/admin_dashboard")
def admin_dashboard():
    if "user" in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        conn.close()
        return render_template("admin_dashboard.html", results=results)
    return redirect(url_for("home"))

@app.route("/search")
def search():
    search_query = request.args.get('query', '')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE username = '{search_query}'")
    results = cursor.fetchall()
    conn.close()
    return jsonify(results)

@app.route("/update_balance", methods=["POST"])
def update_balance():
    username = request.form["username"]
    new_balance = request.form["balance"]
    
    if username in users_db:
        users_db[username]["balance"] = new_balance
        return "Balance updated successfully!"
    return "User not found", 404

@app.route("/change_password", methods=["POST"])
def change_password():
    username = request.form["username"]
    password = request.form["password"]
    
    if username in users_db:
        users_db[username]["password"] = hashlib.md5(password.encode()).hexdigest()  
        return "Password changed!"
    return "User not found", 404

if __name__ == "__main__":
    app.run(debug=True)  
