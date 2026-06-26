# BudgetEase - Budget Tracking System

FinTrack is a full-stack web application designed for comprehensive budget management. It features a modern dark/light mode interface and a robust MySQL backend that tracks incomes, expenses, categories, and budgets, with automatic transaction logging via SQL triggers.

## 🛠️ Technology Stack
*   **Backend:** Python 3, Flask
*   **Database:** MySQL
*   **Frontend:** HTML5, Vanilla CSS (CSS Variables), Vanilla JS

## 🚀 Setup & Execution Instructions

### 1. Database Setup
1. Make sure you have **MySQL Server** installed and running on your machine.
2. Open your MySQL client (e.g., MySQL Workbench or terminal) and execute the SQL script provided in `database/setup.sql`.
   ```bash
   mysql -u root -p < database/setup.sql
   ```
   *Note: The script will automatically create the database `budget_tracking_db`, necessary tables, relationships, triggers, and sample data.*

### 2. Environment Variables Configuration
1. In the root directory, create a `.env` file (if one doesn't exist).
2. Configure your MySQL credentials:
   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=budget_tracking_db
   SECRET_KEY=your_secure_flask_key
   ```

### 3. Python Setup
1. It is recommended to create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate   # On Windows
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 4. Running the Application
1. Start the Flask application:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to: `http://127.0.0.1:5000`

### 5. Using the App
*   **Sample Accounts**: You can log in using the sample accounts created in `setup.sql` (if you run it), but since passwords need hashing, it's highly recommended to **Register a new account** via the web interface.
*   Once logged in, you can manage your categories, add incomes/expenses, and view your remaining balance and active budgets on the Dashboard.

## 🌟 Advanced Features Implemented
*   **SQL Triggers:** Automatically creates a transaction record when an Income or Expense is added.
*   **Budget Alerts:** A global context processor warns users if they exceed or near their category budget limits.
*   **Modern UI:** Responsive grid layout, dark/light theme toggle, glassmorphism panel effects, and micro-animations.
