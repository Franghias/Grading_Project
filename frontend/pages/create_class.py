# =========================
# Create Class Page
# =========================
# This file implements the class creation interface for professors.
# Professors can create a new class, set its details, and automatically generate default assignments.
# Includes form validation, API calls, and sidebar navigation.

import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time

# =========================
# Environment and API Setup
# =========================
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'

# Load environment variables from .env file
load_dotenv(dotenv_path=env_path)

API_URL = os.getenv('API_URL', 'http://localhost:8000').strip()

# =========================
# Default Assignments
# =========================

DEFAULT_ASSIGNMENTS = [
    {
        "name": "Hello World",
        "description": "Write a program that prints 'Hello, World!' to the console."
    },
    {
        "name": "Print",
        "description": "Practice using the print() function with different types of data."
    },
    {
        "name": "Variable Definition and How to Use It",
        "description": "Create and use variables of different types (string, integer, float, boolean)."
    },
    {
        "name": "If Else Statement",
        "description": "Write a program that uses if-else statements to make decisions."
    },
    {
        "name": "For Loop",
        "description": "Practice using for loops to iterate over sequences and ranges."
    }
]

# =========================
# Page Configuration and Sidebar
# =========================

st.set_page_config(
    page_title="Create Class",
    page_icon="➕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Custom CSS Styling (Consistent with new theme)
# =========================
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* --- Animation Keyframes --- */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* --- Hide default sidebar --- */
        [data-testid="stSidebarNav"] {display: none;}

        /* --- Theme & Base Styles --- */
        :root {
            --primary-color: #d4a373;         /* Tan (for headings and primary actions) */
            --primary-hover-color: #faedcd;    /* Sandy Beige (for button hover) */
            --background-color: #e9edc9;      /* Pale Green/Yellow (main background) */
            --card-background-color: #fefae0; /* Creamy Yellow (card background) */
            --text-color: #5d4037;            /* Dark Brown for main text */
            --subtle-text-color: #8a817c;      /* Muted gray-brown for paragraphs */
            --border-color: #ccd5ae;          /* Muted Earthy Green (borders) */
        }
        .stApp {
            background-color: var(--background-color);
            font-family: 'Inter', sans-serif;
            color: var(--text-color);
        }
        .main .block-container {
            padding: 2rem;
            animation: fadeIn 0.5s ease-in-out forwards;
        }

        /* --- Header Styling --- */
        .st-emotion-cache-10trblm { /* This targets st.title */
            color: var(--text-color);
            padding-bottom: 1rem;
        }
        h2, h3 { /* This targets st.subheader */
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 0.5rem;
            color: var(--text-color);
        }

        /* --- Button Styling --- */
        .stButton > button {
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
            background-color: var(--primary-color);
            color: var(--text-color);
            border: 1px solid var(--primary-color);
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            background-color: var(--primary-hover-color);
            border-color: var(--primary-hover-color);
            box-shadow: 0 4px 12px rgba(212, 163, 115, 0.15);
        }
            
        .stSelectbox > label {
            color: var(--text-color) !important;
            font-weight: 600 !important;
        }

        .stTextInput > label {
            color: var(--text-color) !important;
            font-weight: 600 !important;
        }
            
        /* --- Form & Input Styling --- */
        .stTextInput > div > div > input, .stTextArea > div > textarea {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            background-color: var(--card-background-color);
            color: var(--text-color);
        }
        .stForm {
            background-color: var(--card-background-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 12px rgba(212, 163, 115, 0.05);
        }
        
        /* --- Progress bar styling --- */
        .stProgress > div > div > div > div {
            background-color: var(--primary-color) !important;
        }
    </style>
""", unsafe_allow_html=True)


# =========================
# Sidebar Navigation
# =========================
if 'user' in st.session_state:
    if st.session_state.user.get('is_professor'):
        with st.sidebar:
            st.title("👨‍🏫 Professor Menu")
            st.page_link('pages/2_Professor_View.py', label='Professor View', icon='📝')
            st.page_link('pages/5_Prompt_Management.py', label='Prompt Management', icon='🧠')
            st.page_link('pages/6_Assignment_Management.py', label='Assignment Management', icon='🗂️')
            st.page_link('pages/create_class.py', label='Create a New Class', icon='➕')
            st.page_link('pages/7_Class_Statistics.py', label='Class Statistics', icon='📊')
            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.switch_page("login.py")
    else:
        with st.sidebar:
            st.title('Student Menu')
            st.page_link('pages/3_Student_View.py', label='Student View', icon='👨‍🎓')
            st.page_link('pages/1_Home.py', label='Home', icon='🏠')
            st.page_link('pages/4_Grades_View.py', label='Grades View', icon='📊')
            st.page_link('login.py', label='Logout', icon='🚪')

# =========================
# Header and Access Control
# =========================
st.title("➕ Create a New Class")
st.write("Use this form to add a new class to the system. Required fields are marked with an asterisk (*).")
st.markdown("---")

# Check if user is logged in and is a professor
if 'user' not in st.session_state:
    st.switch_page("login.py")

if not st.session_state.user.get('is_professor'):
    st.error("This page is for professors only.")
    st.stop()

# =========================
# Create Class Form
# =========================

with st.form("create_class_form"):
    st.subheader("Class Details")
    
    # Class name and code in columns
    col1, col2 = st.columns(2)
    with col1:
        class_name = st.text_input(
            "Class Name*",
            placeholder="e.g., Introduction to Python",
            help="Enter the full name of your class"
        )
    with col2:
        class_code = st.text_input(
            "Class Code*",
            placeholder="e.g., CS1111",
            help="Enter a unique code for your class (e.g., CS1111)"
        )
    
    # Class description
    class_description = st.text_area(
        "Class Description",
        placeholder="Enter a detailed description of your class, its objectives, and any other relevant information...",
        help="A good description helps students understand the course.",
        height=150
    )
    
    st.subheader("Additional Information (Optional)")
    
    # Prerequisites and Learning objectives in columns
    col3, col4 = st.columns(2)
    with col3:
        prerequisites = st.text_area(
            "Prerequisites",
            placeholder="e.g., Basic computer literacy",
            help="Enter any prerequisites or recommended background knowledge.",
            height=100
        )
    with col4:
        learning_objectives = st.text_area(
            "Learning Objectives",
            placeholder="e.g., Students will be able to write simple Python scripts.",
            help="Enter what students will be able to do after this class.",
            height=100
        )
    
    st.markdown("---")
    
    # Submit button
    submit_button = st.form_submit_button("🚀 Create Class and Add Default Assignments")

    if submit_button:
        if not class_name or not class_code:
            st.error("Please fill in the required fields (Class Name and Class Code).")
        else:
            try:
                # Create the class
                class_data = {
                    "name": class_name,
                    "code": class_code,
                    "description": class_description if class_description else None,
                    "prerequisites": prerequisites if prerequisites else None,
                    "learning_objectives": learning_objectives if learning_objectives else None
                }
                
                response = requests.post(
                    f"{API_URL}/classes/",
                    headers={"Authorization": f"Bearer {st.session_state.token}", "Content-Type": "application/json"},
                    json=class_data
                )
                response.raise_for_status()
                
                created_class = response.json()
                st.success(f"Class '{created_class['name']}' created successfully!")
                
                # Add the current user as a professor of the class
                professor_id = str(st.session_state.user['user_id'])
                response = requests.post(
                    f"{API_URL}/classes/{created_class['id']}/add-professor/{professor_id}",
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                response.raise_for_status()
                st.success("You have been assigned as a professor for this class!")

                # Create default assignments
                st.info("Creating default assignments...")
                progress_bar = st.progress(0)
                
                for i, assignment in enumerate(DEFAULT_ASSIGNMENTS):
                    try:
                        assignment_data = {
                            "name": assignment["name"],
                            "description": assignment["description"],
                            "class_id": created_class['id']
                        }
                        response = requests.post(
                            f"{API_URL}/classes/{created_class['id']}/assignments/",
                            headers={"Authorization": f"Bearer {st.session_state.token}", "Content-Type": "application/json"},
                            json=assignment_data
                        )
                        response.raise_for_status()
                        time.sleep(0.1) # small delay for visual effect
                        progress_bar.progress((i + 1) / len(DEFAULT_ASSIGNMENTS))
                    except requests.RequestException as e:
                        st.error(f"Error creating assignment '{assignment['name']}': {str(e)}")
                        continue
                
                st.success("Default assignments created successfully!")
                st.balloons()
                
                # Clear the form and redirect to professor view
                time.sleep(2)
                st.switch_page("pages/2_Professor_View.py")
                
            except requests.RequestException as e:
                error_msg = e.response.json().get("detail", str(e)) if e.response else str(e)
                if "Class code already exists" in error_msg:
                    st.error("This class code is already in use. Please choose a different one.")
                else:
                    st.error(f"An error occurred: {error_msg}")