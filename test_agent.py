from agent import PharmaAgent
import database
import auth
import os

def test_agent():
    # Initialize DB
    database.init_db()

    # Setup Test Data
    print("Setting up test shop...")
    shop_name = "Test Shop"
    user_name = "testadmin"
    password = "password123"
    
    # Register if not exists (or just create shop directly via DB for testing speed, but let's use auth)
    # Since we deleted DB, we need to register.
    auth.register_shop(shop_name, user_name, password)
    user = auth.login_user(user_name, password)
    shop_id = user['shop_id']
    print(f"Logged in as {user_name} (Shop ID: {shop_id})")

    agent = PharmaAgent(shop_id)
    
    print("Testing ADD intent...")
    response = agent.process_query("Add 50 Paracetamol to Shelf A")
    print(f"Response: {response}")
    assert "Updated Paracetamol" in response or "Updated" in response
    
    print("\nTesting SEARCH intent...")
    response = agent.process_query("Where is Paracetamol?")
    print(f"Response: {response}")
    assert "found 'paracetamol'" in response.lower()
    
    print("\nTesting UPDATE intent (Add more)...")
    response = agent.process_query("Add 20 Paracetamol to Shelf A")
    print(f"Response: {response}")
    # Should be 70 now
    
    print("\nTesting SEARCH intent again...")
    response = agent.process_query("Find Paracetamol")
    print(f"Response: {response}")
    assert "70 units" in response
    
    print("\nTesting Data Isolation (New Shop)...")
    auth.register_shop("Other Shop", "otheradmin", "password")
    other_user = auth.login_user("otheradmin", "password")
    other_agent = PharmaAgent(other_user['shop_id'])
    
    response = other_agent.process_query("Where is Paracetamol?")
    print(f"Other Shop Response: {response}")
    assert "couldn't find" in response.lower()

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_agent()
