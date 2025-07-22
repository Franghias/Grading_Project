import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time
import sys
from pathlib import Path

# Load environment variables
load_dotenv()
API_URL = os.getenv('API_URL', 'http://localhost:8000').strip()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Grading System Login",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- UNIFIED CSS WITH TRANSITIONS ---
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
            /* New Earthy Palette */
            --primary-color: #d4a373;         /* Tan (for headings and primary actions) */
            --background-color: #e9edc9;      /* Pale Green/Yellow (main background) */
            --card-background-color: #fefae0; /* Creamy Yellow (card background) */
            --button-color: #d4a373;          /* Tan (primary buttons) */
            --button-hover-color: #faedcd;    /* Sandy Beige (button hover) */
            --input-background: #fefae0;      /* Creamy Yellow (input boxes) */
            --border-color: #ccd5ae;          /* Muted Earthy Green (borders) */
            --subtle-text-color: #ccd5ae;     /* Muted Earthy Green (for subtle text) */
            
            /* Text colors for readability */
            --dark-text-color: #5d4037;       /* Dark Brown for main text */
            --light-text-color: #fefae0;      /* Creamy Yellow for text on dark backgrounds */
        }
        .stApp {
            background-color: var(--background-color);
            font-family: 'Inter', sans-serif;
        }
        /* --- Main Login Container with Transition --- */
        .login-container {
            background-color: var(--card-background-color);
            padding: 2.5rem;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(212, 163, 115, 0.1);
            border: 1.5px solid var(--border-color);
            max-width: 450px;
            margin: 4rem auto;
            text-align: center;
            animation: fadeInScaleUp 0.5s ease-in-out forwards;
        }
        .login-container h1 {
            font-size: 2rem;
            font-weight: 700;
            color: var(--dark-text-color);
            margin-bottom: 0.5rem;
            letter-spacing: 1px;
        }
        .login-container p {
            color: var(--dark-text-color); /* A slightly darker gray for paragraph text */
            margin-bottom: 2rem;
        }
        /* --- Input and Button Styling with Transitions --- */
        .stTextInput > div > div > input {
            border: 1.5px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            background-color: var(--input-background);
            color: var(--dark-text-color);
            font-weight: 500;
            transition: all 0.2s ease-in-out;
        }
        .stTextInput > div > div > input:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(212, 163, 115, 0.2);
        }
        .stTextInput > div > div > input::placeholder {
            color: var(--subtle-text-color) !important;
            opacity: 1;
        }
        .stTextInput > label {
            color: var(--text-color) !important;
            font-weight: 600 !important;
        }
        /* --- Button Styling --- */
        .stButton > button {
            background-color: var(--button-color);
            color: var(--dark-text-color) !important;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-weight: 600;
            width: 100%;
            border: none;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 0 8px rgba(212, 163, 115, 0.1);
        }
        .stButton > button:hover {
            background-color: var(--button-hover-color);
            color: var(--dark-text-color) !important;
            box-shadow: 0 4px 16px rgba(212, 163, 115, 0.2);
        }
        /* --- Signup Prompt --- */
        .signup-prompt {
            margin-top: 1.5rem;
            color: var(--dark-text-color);
        }
        /* --- Spinner --- */
        .stSpinner > div > div {
            border-top-color: var(--primary-color);
        }
        /* --- Alerts and Error Messages --- */
        .stAlert {
            border-radius: 8px;
            border: 1px solid #e63946;
        }
        .stAlert, .stAlert * {
            color: #e63946 !important;
        }
        /* --- Headings --- */
        h1, h2, h3, h4, h5, h6 {
            color: var(--dark-text-color) !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0
if 'last_attempt_time' not in st.session_state:
    st.session_state.last_attempt_time = 0

# --- LOGIN FORM LAYOUT ---
col1, col2, col3 = st.columns([1, 1.5, 1])

with col2:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h1>🎓 Welcome to Grading Project AI Assistant </h1>', unsafe_allow_html=True)
    st.markdown('<p>Welcome back! Please sign in to continue.</p>', unsafe_allow_html=True)

    # --- RATE LIMITING LOGIC ---
    current_time = time.time()
    if st.session_state.login_attempts >= 5 and current_time - st.session_state.last_attempt_time < 120:
        remaining_time = int(120 - (current_time - st.session_state.last_attempt_time))
        st.error(f"Too many attempts. Please wait {remaining_time} seconds.")
        st.stop()

    # --- LOGIN FORM ---
    with st.form("login_form"):
        email = st.text_input(
            "Email",
            placeholder="e.g., user@example.com",
            key="login_email"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )
        submit_button = st.form_submit_button("Sign In")

        if submit_button:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                st.session_state.login_attempts += 1
                st.session_state.last_attempt_time = current_time

                with st.spinner("Authenticating..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/auth/login",
                            data={"username": email, "password": password},
                            timeout=10
                        )
                        response.raise_for_status()

                        result = response.json()
                        st.session_state.login_attempts = 0
                        st.session_state.token = result.get("access_token")
                        st.session_state.user = result.get("user")
                        
                        st.success("Login successful! Redirecting...")
                        time.sleep(1)

                        if st.session_state.user.get("is_professor"):
                            st.switch_page("pages/2_Professor_View.py")
                        else:
                            st.switch_page("pages/3_Student_View.py")

                    except requests.Timeout:
                        st.error("Connection timed out. Please try again.")
                    except requests.HTTPError as e:
                        if e.response.status_code == 401:
                             st.error("Incorrect email or password.")
                        else:
                             st.error(f"An error occurred: Status {e.response.status_code}")
                    except requests.RequestException:
                        st.error("Failed to connect to the server. Please check your connection.")
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {e}")

    # --- SIGN-UP BUTTON ---
    st.markdown('<p class="signup-prompt">Don\'t have an account?</p>', unsafe_allow_html=True)
    signup_btn = st.button("Sign up here", key="signup_btn")
    # Add a custom class to the last rendered button (Sign up here)
    st.markdown("""
        <style>
        div.stButton > button#signup_btn {
            background-color: transparent;
            color: var(--primary-color) !important;
            border: 2px solid var(--primary-color);
            box-shadow: none;
        }
        div.stButton > button#signup_btn:hover {
            background-color: var(--button-hover-color);
            color: var(--dark-text-color) !important;
            border-color: var(--button-hover-color);
        }
        </style>
    """, unsafe_allow_html=True)
    if signup_btn:
        st.switch_page("pages/1_Signup.py")

    st.markdown('</div>', unsafe_allow_html=True)