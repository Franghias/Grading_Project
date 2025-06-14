import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
API_URL = os.getenv('API_URL', 'http://localhost:3000')

# Page configuration
st.set_page_config(
    page_title="CS 1111 Login",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        /* Theme variables */
        :root {
            --bg-color: #f7f3e3;
            --text-color: #1a202c;
            --card-bg: #f7fafc;
            --primary-bg: #4a9a9b;
            --primary-hover: #3d8283;
            --border-color: #e2e8f0;
            --input-bg: #ffffff;
            --input-border: #cbd5e0;
            --success-bg: #e6fffa;
            --success-text: #2d3748;
            --error-bg: #fee2e2;
            --error-text: #702020;
        }

        /* Apply theme */
        html, body, .stApp {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 16px;
            line-height: 1.5;
        }

        /* Header styling */
        .header {
            background-color: #4a9a9b;
            padding: 2rem;
            text-align: center;
            position: relative;
            overflow: hidden;
            min-height: 200px;
            color: #ffffff;
        }

        /* Card styling */
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            padding: 1.5rem;
            text-align: center;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        /* Button styling */
        .stButton > button {
            background-color: var(--primary-bg);
            color: white;
            border-radius: 0.375rem;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: background-color 0.2s ease;
        }

        .stButton > button:hover {
            background-color: var(--primary-hover);
        }

        /* Input styling */
        .stTextInput > div > div > input {
            background-color: var(--input-bg);
            color: var(--text-color);
            border: 1px solid var(--input-border);
            border-radius: 0.375rem;
            padding: 0.5rem;
        }

        /* Success and error messages */
        .success, .error {
            padding: 1rem;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
        }

        .success { background-color: var(--success-bg); color: var(--success-text); }
        .error { background-color: var(--error-bg); color: var(--error-text); }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown('<h1>CS 1111 Grading System</h1>', unsafe_allow_html=True)
st.markdown('<p>Welcome back! Please login to continue</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Main content
st.markdown('<div class="container mx-auto px-4 py-8">', unsafe_allow_html=True)

# Login form
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<h2 class="text-xl font-medium mb-6">Login</h2>', unsafe_allow_html=True)

with st.form("login_form"):
    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    submit_button = st.form_submit_button("Login")

    if submit_button:
        if email and password:
            try:
                response = requests.post(
                    f"{API_URL}/auth/login",
                    data={
                        "username": email,  # OAuth2 expects username field
                        "password": password
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Store token and user info in session state
                st.session_state.token = result["access_token"]
                st.session_state.user = result["user"]  # Store the complete user object
                
                st.success("Login successful!")
                # Redirect to main app
                st.switch_page("pages/1_Home.py")
            except requests.RequestException as e:
                st.error(f"Login failed: {str(e)}")
        else:
            st.error("Please fill in all fields")

# Signup button
st.markdown('<div class="mt-4">', unsafe_allow_html=True)
if st.button("Sign up here"):
    st.switch_page("pages/1_Signup.py")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) 