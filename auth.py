import bcrypt
import database

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(stored_hash, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_hash.encode('utf-8'))

def login_user(username, password):
    user = database.get_user(username)
    if user and verify_password(user[2], password):
        return {"id": user[0], "username": user[1], "shop_id": user[3]}
    return None

def register_shop(shop_name, username, password):
    # Check if user exists
    if database.get_user(username):
        return False, "Username already exists"
    
    # Create Shop
    shop_id = database.create_shop(shop_name)
    if not shop_id:
        return False, "Shop name already exists"
    
    # Create Admin User
    pwd_hash = hash_password(password)
    if database.create_user(username, pwd_hash, shop_id):
        return True, "Registration successful"
    else:
        return False, "Failed to create user"
