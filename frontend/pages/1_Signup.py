# =========================
# Signup Page
# =========================
import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time
from pathlib import Path

# =========================
# Environment and API Setup
# =========================
# Load environment variables
load_dotenv()
API_URL = os.getenv('API_URL', 'http://localhost:8000').strip()

# =========================
# Page Configuration
# =========================
st.set_page_config(
    page_title="CS 1111 Sign Up",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# UNIFIED CSS (WITH MARGIN FIX)
# =========================
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* --- Animation Keyframes --- */
        @keyframes fadeInScaleUp {
            from {
                opacity: 0;
                transform: scale(0.95);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }

        /* --- Hide Streamlit Elements --- */
        [data-testid="stHeader"], [data-testid="stSidebarNav"] {
            display: none;
        }
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }

        /* --- Theme & Styles --- */
        :root {
            --primary-color: #4a9a9b; /* Teal */
            --primary-hover-color: #3d8283; /* Darker Teal */
            --background-color: #f0f2f6; /* Light Gray */
            --card-background-color: #ffffff; /* White */
            --text-color: #262730; /* Dark Gray */
            --subtle-text-color: #5E5E5E;
            --border-color: #e0e0e0;
        }
        .stApp {
            background-color: var(--background-color);
            font-family: 'Inter', sans-serif;
        }

        /* --- Main Container with corrected margin --- */
        .login-container {
            background-color: var(--card-background-color);
            padding: 2.5rem;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--border-color);
            max-width: 450px;
            margin: 2rem auto; /* Reduced vertical margin to prevent scrolling */
            text-align: center;
            animation: fadeInScaleUp 0.5s ease-in-out forwards;
        }
        .login-container h1 {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        .login-container p {
            color: var(--subtle-text-color);
            margin-bottom: 1.5rem;
        }

        /* --- Input and Button Styling --- */
        .stTextInput > div > div > input {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            background-color: #f9f9f9;
            transition: all 0.2s ease-in-out;
        }
        .stTextInput > div > div > input:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(74, 154, 155, 0.2);
        }

        .stButton > button {
            background-color: var(--primary-color);
            color: white;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-weight: 600;
            width: 100%;
            border: none;
            transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover {
            background-color: var(--primary-hover-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        /* --- Requirements Box --- */
        .requirements-box {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            text-align: left;
        }
        .requirements-box h3 {
            color: var(--text-color);
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .requirements-box ul {
            color: var(--subtle-text-color);
            margin: 0;
            padding-left: 1.5rem;
        }
        
        /* --- Login Link --- */
        .login-link {
            margin-top: 1.5rem;
        }
    </style>
""", unsafe_allow_html=True)


# =========================
# Main Content
# =========================
col1, col2, col3 = st.columns([1, 1.5, 1])

with col2:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    st.markdown('<h1>Create Your Account</h1>', unsafe_allow_html=True)
    st.markdown('<p>Join the CS 1111 Grading System</p>', unsafe_allow_html=True)

    # Requirements information
    st.markdown("""
        <div class="requirements-box">
            <h3>Requirements:</h3>
            <ul>
                <li>ID must be exactly 8 digits</li>
                <li>Email must be valid</li>
                <li><b>Password must be at least 8 characters long</b></li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    # Signup Form Logic
    with st.form("signup_form"):
        name = st.text_input("Full Name", placeholder="Enter your full name")
        user_id = st.text_input("ID", placeholder="Enter your 8-digit ID")
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        role = st.radio(
            "Select your role",
            ["Student", "Professor"],
            horizontal=True,
            help="Professors can create custom grading code and grade submissions"
        )
        
        submit_button = st.form_submit_button("Create Account")
        
        if submit_button:
            if not all([name, user_id, email, password, confirm_password]):
                st.error("Please fill in all fields.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                with st.spinner("Creating account..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/auth/signup",
                            json={
                                "name": name,
                                "user_id": user_id,
                                "email": email,
                                "password": password,
                                "is_professor": role == "Professor"
                            }
                        )
                        response.raise_for_status()
                        st.success("Account created successfully! Redirecting to login...")
                        time.sleep(2)
                        st.switch_page("login.py")
                    except requests.RequestException as e:
                        try:
                            error_msg = response.json().get("detail", str(e))
                        except Exception:
                            error_msg = str(e)
                        st.error(f"Signup failed: {error_msg}")

    # Login Link
    st.markdown('<div class="login-link">', unsafe_allow_html=True)
    st.markdown("<p>Already have an account?</p>", unsafe_allow_html=True)
    if st.button("Go to Login Page"):
        st.switch_page("login.py")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # Close login-container