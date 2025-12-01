import streamlit as st
import pandas as pd
from agent import PharmaAgent
import database
import auth

st.set_page_config(page_title="PharmaBot SaaS", page_icon="💊", layout="wide")

# Initialize DB
database.init_db()

# Initialize Session State
if "user" not in st.session_state:
    st.session_state.user = None

def login_page():
    st.title("🔐 PharmaBot Login")
    
    tab1, tab2 = st.tabs(["Login", "Register New Shop"])
    
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = auth.login_user(username, password)
            if user:
                st.session_state.user = user
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    with tab2:
        st.subheader("Register Your Shop")
        new_shop = st.text_input("Shop Name")
        new_user = st.text_input("Admin Username")
        new_pass = st.text_input("Admin Password", type="password")
        
        if st.button("Register"):
            if new_shop and new_user and new_pass:
                success, msg = auth.register_shop(new_shop, new_user, new_pass)
                if success:
                    st.success("Registration successful! Please login.")
                else:
                    st.error(f"Error: {msg}")
            else:
                st.warning("Please fill all fields")

def main_app():
    user = st.session_state.user
    st.sidebar.title(f"🏥 {user['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.messages = [] # Clear chat on logout
        st.rerun()

    # Initialize Agent with Shop ID
    if "agent" not in st.session_state or getattr(st.session_state.agent, 'shop_id', None) != user['shop_id']:
        st.session_state.agent = PharmaAgent(user['shop_id'])

    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm PharmaBot. I can help you find medicines or update stock.\n\nTry saying: *'Where is Crocin?'* or *'Add 10 Aspirin to Shelf A'*."}
        ]

    # Sidebar - Inventory Overview
    with st.sidebar:
        st.header("📦 Inventory Overview")
        if st.button("Refresh Inventory"):
            st.rerun()
        
        df = database.get_all_inventory(user['shop_id'])
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Inventory is empty.")

    # Main Chat Interface
    st.title("💊 PharmaBot: Intelligent Inventory Assistant")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask about medicines..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.agent.process_query(prompt)
                
                # If response is a DataFrame (for "list all"), display it nicely
                if isinstance(response, pd.DataFrame):
                    st.dataframe(response)
                    st.session_state.messages.append({"role": "assistant", "content": "Here is the inventory list:"})
                else:
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

if st.session_state.user:
    main_app()
else:
    login_page()
