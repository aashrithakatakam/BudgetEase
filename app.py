import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables (DB credentials)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'super_secret_budget_key')

# Database connection helper
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'budget_tracking_db')
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Context processor to make total expenses and budget alerts available to all templates
@app.context_processor
def inject_alerts():
    if 'user_id' not in session:
        return dict(alerts=[])
    
    conn = get_db_connection()
    if not conn:
        return dict(alerts=[])
        
    cursor = conn.cursor(dictionary=True)
    user_id = session['user_id']
    
    # Check for budget overruns
    alerts = []
    try:
        # Get all budgets for user and total spent per category in the budget timeframe
        cursor.execute("""
            SELECT b.budget_id, b.limit_amount, c.category_name,
                   IFNULL(SUM(e.amount), 0) as total_spent
            FROM Budget b
            JOIN Category c ON b.category_id = c.category_id
            LEFT JOIN Expense e ON b.category_id = e.category_id 
                AND e.user_id = %s 
                AND e.date >= b.start_date 
                AND e.date <= b.end_date
            WHERE b.user_id = %s
            GROUP BY b.budget_id, b.limit_amount, c.category_name
        """, (user_id, user_id))
        
        budgets = cursor.fetchall()
        for b in budgets:
            if b['total_spent'] > b['limit_amount']:
                alerts.append(f"Warning: You have exceeded your budget for {b['category_name']}! (Limit: ${b['limit_amount']}, Spent: ${b['total_spent']})")
            elif b['total_spent'] > (b['limit_amount'] * 0.9):
                alerts.append(f"Notice: You are nearing your budget limit for {b['category_name']}. (Limit: ${b['limit_amount']}, Spent: ${b['total_spent']})")
                
    except Exception as e:
        print(f"Error checking alerts: {e}")
    finally:
        cursor.close()
        conn.close()
        
    return dict(alerts=alerts)

# --- Authentication Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        if conn is None:
            flash("Database connection error. Please try again later.", "danger")
            return redirect(url_for('register'))
            
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO User (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash("Email already exists.", "danger")
        finally:
            cursor.close()
            conn.close()
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn is None:
            flash("Database connection error. Please try again later.", "danger")
            return redirect(url_for('login'))
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM User WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# --- Decorator for protecting routes ---
from functools import wraps
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Core Routes ---
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Total Income
    cursor.execute("SELECT IFNULL(SUM(amount), 0) as total_income FROM Income WHERE user_id = %s", (user_id,))
    total_income = cursor.fetchone()['total_income']
    
    # Total Expense
    cursor.execute("SELECT IFNULL(SUM(amount), 0) as total_expense FROM Expense WHERE user_id = %s", (user_id,))
    total_expense = cursor.fetchone()['total_expense']
    
    # Remaining Balance
    remaining_balance = total_income - total_expense
    
    # Recent Transactions (Join with User not strictly necessary since filtered by user, but doing it to demonstrate JOIN)
    cursor.execute("""
        SELECT t.*, u.name as user_name 
        FROM Transaction t 
        JOIN User u ON t.user_id = u.user_id
        WHERE t.user_id = %s 
        ORDER BY date DESC LIMIT 5
    """, (user_id,))
    recent_transactions = cursor.fetchall()
    
    # Category-wise spending
    cursor.execute("""
        SELECT c.category_name, IFNULL(SUM(e.amount), 0) as amount 
        FROM Category c 
        LEFT JOIN Expense e ON c.category_id = e.category_id AND e.user_id = %s
        WHERE c.type = 'Expense'
        GROUP BY c.category_id
        HAVING amount > 0
    """, (user_id,))
    category_spending = cursor.fetchall()
    
    # Find highest spending category
    highest_category = None
    if category_spending:
        highest_category = max(category_spending, key=lambda x: x['amount'])

    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', 
                           total_income=total_income, 
                           total_expense=total_expense, 
                           remaining_balance=remaining_balance,
                           recent_transactions=recent_transactions,
                           category_spending=category_spending,
                           highest_category=highest_category)

@app.route('/income', methods=['GET', 'POST'])
@login_required
def manage_income():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        amount = request.form['amount']
        date = request.form['date']
        source = request.form['source']
        
        cursor.execute("INSERT INTO Income (amount, date, source, user_id) VALUES (%s, %s, %s, %s)", 
                       (amount, date, source, user_id))
        conn.commit()
        flash("Income added successfully! (Transaction auto-generated via trigger)", "success")
        return redirect(url_for('manage_income'))
        
    cursor.execute("SELECT * FROM Income WHERE user_id = %s ORDER BY date DESC", (user_id,))
    incomes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('income.html', incomes=incomes)

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def manage_expenses():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        amount = request.form['amount']
        date = request.form['date']
        description = request.form['description']
        category_id = request.form['category_id']
        
        cursor.execute("INSERT INTO Expense (amount, date, description, category_id, user_id) VALUES (%s, %s, %s, %s, %s)", 
                       (amount, date, description, category_id, user_id))
        conn.commit()
        flash("Expense added successfully! (Transaction auto-generated via trigger)", "success")
        return redirect(url_for('manage_expenses'))
        
    # Get expenses with category name (JOIN)
    cursor.execute("""
        SELECT e.*, c.category_name 
        FROM Expense e 
        JOIN Category c ON e.category_id = c.category_id 
        WHERE e.user_id = %s 
        ORDER BY date DESC
    """, (user_id,))
    expenses = cursor.fetchall()
    
    # Get expense categories for the dropdown
    cursor.execute("SELECT * FROM Category WHERE type = 'Expense'")
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('expenses.html', expenses=expenses, categories=categories)

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        category_name = request.form['category_name']
        type_val = request.form['type']
        
        cursor.execute("INSERT INTO Category (category_name, type) VALUES (%s, %s)", (category_name, type_val))
        conn.commit()
        flash("Category added successfully!", "success")
        return redirect(url_for('manage_categories'))
        
    cursor.execute("SELECT * FROM Category")
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('categories.html', categories=categories)

@app.route('/budget', methods=['GET', 'POST'])
@login_required
def manage_budget():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        limit_amount = request.form['limit_amount']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        category_id = request.form['category_id']
        
        cursor.execute("INSERT INTO Budget (limit_amount, start_date, end_date, category_id, user_id) VALUES (%s, %s, %s, %s, %s)", 
                       (limit_amount, start_date, end_date, category_id, user_id))
        conn.commit()
        flash("Budget set successfully!", "success")
        return redirect(url_for('manage_budget'))
        
    # Get Budgets with Category and spent amount (Advanced JOIN / Subquery concept)
    cursor.execute("""
        SELECT b.*, c.category_name,
               (SELECT IFNULL(SUM(amount), 0) FROM Expense e 
                WHERE e.category_id = b.category_id AND e.user_id = b.user_id 
                AND e.date >= b.start_date AND e.date <= b.end_date) as amount_spent
        FROM Budget b
        JOIN Category c ON b.category_id = c.category_id
        WHERE b.user_id = %s
    """, (user_id,))
    budgets = cursor.fetchall()
    
    cursor.execute("SELECT * FROM Category WHERE type = 'Expense'")
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('budget.html', budgets=budgets, categories=categories)

@app.route('/transactions')
@login_required
def view_transactions():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Filter functionality
    type_filter = request.args.get('type')
    
    query = "SELECT * FROM Transaction WHERE user_id = %s"
    params = [user_id]
    
    if type_filter and type_filter in ['Income', 'Expense']:
        query += " AND type = %s"
        params.append(type_filter)
        
    query += " ORDER BY date DESC"
    
    cursor.execute(query, tuple(params))
    transactions = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('transactions.html', transactions=transactions, current_filter=type_filter)

if __name__ == '__main__':
    app.run(debug=True)
