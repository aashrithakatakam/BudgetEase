-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS budget_tracking_db;
USE budget_tracking_db;

-- 1. User Table
CREATE TABLE IF NOT EXISTS User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- 2. Category Table
CREATE TABLE IF NOT EXISTS Category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    type ENUM('Income', 'Expense') NOT NULL
);

-- 3. Income Table
CREATE TABLE IF NOT EXISTS Income (
    income_id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10, 2) NOT NULL,
    date DATE NOT NULL,
    source VARCHAR(255) NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- 4. Expense Table
CREATE TABLE IF NOT EXISTS Expense (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10, 2) NOT NULL,
    date DATE NOT NULL,
    description VARCHAR(255),
    category_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES Category(category_id) ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- 5. Transaction Table
CREATE TABLE IF NOT EXISTS Transaction (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10, 2) NOT NULL,
    date DATE NOT NULL,
    type ENUM('Income', 'Expense') NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- 6. Budget Table
CREATE TABLE IF NOT EXISTS Budget (
    budget_id INT AUTO_INCREMENT PRIMARY KEY,
    limit_amount DECIMAL(10, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    category_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES Category(category_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- ==============================================
-- TRIGGERS for Automatic Transaction Creation
-- ==============================================
DELIMITER //

-- Trigger for Income Insertion
CREATE TRIGGER after_income_insert
AFTER INSERT ON Income
FOR EACH ROW
BEGIN
    INSERT INTO Transaction (amount, date, type, user_id)
    VALUES (NEW.amount, NEW.date, 'Income', NEW.user_id);
END //

-- Trigger for Expense Insertion
CREATE TRIGGER after_expense_insert
AFTER INSERT ON Expense
FOR EACH ROW
BEGIN
    INSERT INTO Transaction (amount, date, type, user_id)
    VALUES (NEW.amount, NEW.date, 'Expense', NEW.user_id);
END //

DELIMITER ;

-- ==============================================
-- SAMPLE DATA
-- ==============================================
-- Insert dummy users (Passwords are intentionally plain here for testing, but application uses hashing)
INSERT IGNORE INTO User (name, email, password) VALUES 
('Admin User', 'admin@example.com', 'scrypt:32768:8:1$7bOqz3K6W6rC7M8X$286e680a13c3b0dfb7245b0c79133a870d0a514d2a13f7041ab6c9c6f2a67e0e7a2b0e6c5f0a7b45c3d2e1f0'), -- pwd: admin
('Test User', 'user@example.com', 'scrypt:32768:8:1$7bOqz3K6W6rC7M8X$286e680a13c3b0dfb7245b0c79133a870d0a514d2a13f7041ab6c9c6f2a67e0e7a2b0e6c5f0a7b45c3d2e1f0'); -- pwd: admin

-- Insert Categories
INSERT IGNORE INTO Category (category_name, type) VALUES 
('Salary', 'Income'),
('Freelance', 'Income'),
('Food & Dining', 'Expense'),
('Rent', 'Expense'),
('Utilities', 'Expense'),
('Entertainment', 'Expense'),
('Transportation', 'Expense');

-- Insert Sample Income (This will also trigger transaction creation)
-- NOTE: Assuming user_id 1 is Admin, user_id 2 is Test User
INSERT INTO Income (amount, date, source, user_id) VALUES 
(5000.00, '2023-10-01', 'Monthly Salary', 1),
(800.00, '2023-10-15', 'Freelance Project', 1);

-- Insert Sample Expenses (This will also trigger transaction creation)
INSERT INTO Expense (amount, date, description, category_id, user_id) VALUES 
(1200.00, '2023-10-02', 'October Rent', 4, 1),
(150.00, '2023-10-05', 'Electricity Bill', 5, 1),
(300.00, '2023-10-10', 'Groceries', 3, 1),
(100.00, '2023-10-12', 'Movie Tickets', 6, 1);

-- Insert Sample Budget
INSERT INTO Budget (limit_amount, start_date, end_date, category_id, user_id) VALUES 
(400.00, '2023-10-01', '2023-10-31', 3, 1), -- Food & Dining Limit 400
(1500.00, '2023-10-01', '2023-10-31', 4, 1); -- Rent Limit 1500
