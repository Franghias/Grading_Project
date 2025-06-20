# =========================
# Signup Page
# =========================
# This file implements the signup page for new users (students and professors).
# It handles user input, validation, and account creation via the backend API.

import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time
import base64

# =========================
# Environment and API Setup
# =========================

# Load environment variables
load_dotenv()
API_URL = os.getenv('API_URL', 'http://localhost:8000')

# =========================
# Page Configuration and Sidebar
# =========================

# Page configuration
st.set_page_config(
    page_title="CS 1111 Sign Up",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide default sidebar
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# =========================
# Custom CSS Styling
# =========================

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

# =========================
# Sidebar Navigation (if logged in)
# =========================

if 'user' in st.session_state:
    if st.session_state.user.get('is_professor'):
        with st.sidebar:
            st.title('Professor Menu')
            st.page_link('pages/2_Professor_View.py', label='Professor View', icon='👨‍🏫')
            st.page_link('pages/5_Prompt_Management.py', label='Prompt Management', icon='📝')
            st.page_link('pages/create_class.py', label='Create Class', icon='➕')
            st.page_link('pages/4_Grades_View.py', label='Grades View', icon='📊')
            st.page_link('pages/6_Assignment_Management.py', label='Assignment Management', icon='🗂️')
            st.page_link('login.py', label='Logout', icon='🚪')
    else:
        with st.sidebar:
            st.title('Student Menu')
            st.page_link('pages/3_Student_View.py', label='Student View', icon='👨‍🎓')
            st.page_link('pages/1_Home.py', label='Home', icon='🏠')
            st.page_link('pages/4_Grades_View.py', label='Grades View', icon='📊')
            st.page_link('login.py', label='Logout', icon='🚪')

# =========================
# Header and Main Content
# =========================

# Header
st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown('<h1>CS 1111 Grading System</h1>', unsafe_allow_html=True)
st.markdown('<p>Create your account</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Main content container
st.markdown('<div class="container mx-auto px-4 py-8">', unsafe_allow_html=True)

# Signup form card
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<h2 class="text-xl font-medium mb-6">Sign Up</h2>', unsafe_allow_html=True)

# Add requirements information
st.markdown("""
    <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.375rem; margin-bottom: 1rem;">
        <h3 style="color: #2d3748; margin-bottom: 0.5rem;">Requirements:</h3>
        <ul style="color: #4a5568; margin: 0; padding-left: 1.5rem;">
            <li>ID must be exactly 8 digits</li>
            <li>Email must be valid</li>
            <li>Password must be at least 8 characters long</li>
        </ul>
    </div>
""", unsafe_allow_html=True)

# -------------------------
# Signup Form Logic
# -------------------------
with st.form("signup_form"):
    name = st.text_input("Full Name", placeholder="Enter your full name")
    user_id = st.text_input("ID", placeholder="Enter your 8-digit ID")
    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
    
    # Add role selection
    role = st.radio(
        "Select your role",
        ["Student", "Professor"],
        help="Professors can create custom grading code and grade submissions"
    )
    
    submit_button = st.form_submit_button("Sign Up")

    if submit_button:
        if name and user_id and email and password and confirm_password:
            # Validate user ID
            if not user_id.isdecimal() or len(user_id) != 8:
                st.error("ID must be exactly 8 digits")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                try:
                    signup_data = {
                        "name": name,
                        "user_id": user_id,
                        "email": email,
                        "password": password,
                        "is_professor": role == "Professor"  # Set is_professor based on role selection
                    }
                    print(f"Sending signup request with data: {signup_data}")
                    response = requests.post(
                        f"{API_URL}/auth/signup",
                        json=signup_data
                    )
                    print(f"Response status code: {response.status_code}")
                    print(f"Response content: {response.text}")
                    response.raise_for_status()
                    result = response.json()
                    
                    st.success("Account created successfully! Please login.")
                    # Redirect to login page
                    st.switch_page("login.py")
                except requests.RequestException as e:
                    error_msg = str(e)
                    if "User ID already registered" in error_msg:
                        st.error("This ID is already registered")
                    elif "Email already registered" in error_msg:
                        st.error("This email is already registered")
                    else:
                        st.error(f"Signup failed: {error_msg}")
        else:
            st.error("Please fill in all fields")

# -------------------------
# Login Link
# -------------------------

st.markdown('<div class="mt-4">', unsafe_allow_html=True)

if st.button("Go to Login Page"):
        st.switch_page("login.py")

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) 