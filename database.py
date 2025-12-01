import sqlite3
import pandas as pd
import os

DB_NAME = "pharmabot.db"

def init_db():
    """Initialize the database with tables."""
    # Check if DB exists to handle migration (simple drop for MVP prototype if schema changes drastically)
    # For a real app, we'd use Alembic. Here we might just create new tables if not exist.
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Shops table
    c.execute('''CREATE TABLE IF NOT EXISTS shops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    shop_id INTEGER,
                    FOREIGN KEY(shop_id) REFERENCES shops(id)
                )''')
    
    # Medicines table (Scoped to shop)
    c.execute('''CREATE TABLE IF NOT EXISTS medicines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    FOREIGN KEY(shop_id) REFERENCES shops(id),
                    UNIQUE(shop_id, name)
                )''')

    # Locations table (Scoped to shop)
    c.execute('''CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id INTEGER,
                    name TEXT NOT NULL,
                    FOREIGN KEY(shop_id) REFERENCES shops(id),
                    UNIQUE(shop_id, name)
                )''')

    # Inventory table
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id INTEGER,
                    medicine_id INTEGER,
                    location_id INTEGER,
                    quantity INTEGER,
                    expiry_date TEXT,
                    FOREIGN KEY(shop_id) REFERENCES shops(id),
                    FOREIGN KEY(medicine_id) REFERENCES medicines(id),
                    FOREIGN KEY(location_id) REFERENCES locations(id)
                )''')
    
    conn.commit()
    conn.close()

def add_medicine(shop_id, name, description=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT OR IGNORE INTO medicines (shop_id, name, description) VALUES (?, ?, ?)", (shop_id, name, description))
        conn.commit()
    finally:
        conn.close()

def add_location(shop_id, name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT OR IGNORE INTO locations (shop_id, name) VALUES (?, ?)", (shop_id, name))
        conn.commit()
    finally:
        conn.close()

def update_stock(shop_id, medicine_name, location_name, quantity, expiry_date=None):
    """Update stock for a medicine at a location for a specific shop."""
    
    # Ensure medicine and location exist for this shop
    add_medicine(shop_id, medicine_name)
    add_location(shop_id, location_name)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Get IDs
    c.execute("SELECT id FROM medicines WHERE name = ? AND shop_id = ?", (medicine_name, shop_id))
    med_row = c.fetchone()
    if not med_row: return "Error: Medicine not found" # Should not happen due to add_medicine
    med_id = med_row[0]
    
    c.execute("SELECT id FROM locations WHERE name = ? AND shop_id = ?", (location_name, shop_id))
    loc_row = c.fetchone()
    if not loc_row: return "Error: Location not found"
    loc_id = loc_row[0]
    
    # Check if inventory record exists
    c.execute("SELECT id, quantity FROM inventory WHERE medicine_id = ? AND location_id = ? AND shop_id = ?", (med_id, loc_id, shop_id))
    row = c.fetchone()
    
    if row:
        new_qty = row[1] + quantity
        if new_qty < 0: new_qty = 0
        c.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_qty, row[0]))
    else:
        if quantity < 0: quantity = 0
        c.execute("INSERT INTO inventory (shop_id, medicine_id, location_id, quantity, expiry_date) VALUES (?, ?, ?, ?, ?)", 
                  (shop_id, med_id, loc_id, quantity, expiry_date))
    
    conn.commit()
    conn.close()
    return f"Updated {medicine_name} at {location_name}. New Quantity: {quantity if not row else row[1] + quantity}"

def find_medicine(shop_id, name):
    """Find a medicine and return its locations and quantities for a specific shop."""
    conn = sqlite3.connect(DB_NAME)
    query = '''
        SELECT m.name as medicine, l.name as location, i.quantity, i.expiry_date
        FROM inventory i
        JOIN medicines m ON i.medicine_id = m.id
        JOIN locations l ON i.location_id = l.id
        WHERE m.name LIKE ? AND i.shop_id = ?
    '''
    df = pd.read_sql_query(query, conn, params=(f"%{name}%", shop_id))
    conn.close()
    return df

def get_all_inventory(shop_id):
    conn = sqlite3.connect(DB_NAME)
    query = '''
        SELECT m.name as Medicine, l.name as Location, i.quantity as Quantity, i.expiry_date as Expiry
        FROM inventory i
        JOIN medicines m ON i.medicine_id = m.id
        JOIN locations l ON i.location_id = l.id
        WHERE i.shop_id = ?
    '''
    df = pd.read_sql_query(query, conn, params=(shop_id,))
    conn.close()
    return df

# Auth related DB functions
def create_shop(name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO shops (name) VALUES (?)", (name,))
        shop_id = c.lastrowid
        conn.commit()
        return shop_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def create_user(username, password_hash, shop_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash, shop_id) VALUES (?, ?, ?)", (username, password_hash, shop_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash, shop_id FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user
