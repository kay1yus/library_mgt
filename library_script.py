import sqlite3

# Function to create the library database and tables
def create_database():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()

    # Create books table
    c.execute('''CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    total_copies INTEGER NOT NULL,
                    available_copies INTEGER NOT NULL
                )''')

    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    is_admin INTEGER NOT NULL DEFAULT 0
                )''')

    # Create borrowed_books table
    c.execute('''CREATE TABLE IF NOT EXISTS borrowed_books (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    book_id INTEGER NOT NULL,
                    borrow_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    returned INTEGER NOT NULL DEFAULT 0,
                    fine INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (book_id) REFERENCES books(id)
                )''')

    # Create fines table
    c.execute('''CREATE TABLE IF NOT EXISTS fines (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )''')

    # Insert sample data into books table
    books_data = [
        ('Book 1', 'Author 1', 5, 5),
        ('Book 2', 'Author 2', 3, 3),
        ('Book 3', 'Author 3', 7, 7)
    ]
    c.executemany('INSERT INTO books (title, author, total_copies, available_copies) VALUES (?, ?, ?, ?)', books_data)

    # Insert sample data into users table
    users_data = [
        ('admin', 'adminpassword', 1),
        ('user1', 'user1password', 0),
        ('user2', 'user2password', 0)
    ]
    c.executemany('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)', users_data)

    # Insert sample data into borrowed_books table
    borrowed_books_data = [
        (2, 1, '2024-04-10', '2024-04-17'),
        (3, 2, '2024-04-08', '2024-04-15')
    ]
    c.executemany('INSERT INTO borrowed_books (user_id, book_id, borrow_date, due_date) VALUES (?, ?, ?, ?)', borrowed_books_data)

    # Insert sample data into fines table
    fines_data = [
        (2, 10),
        (3, 5)
    ]
    c.executemany('INSERT INTO fines (user_id, amount) VALUES (?, ?)', fines_data)

    conn.commit()
    conn.close()

# Run the function to create the database and populate it with sample data
create_database()
