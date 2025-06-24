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

API_URL = os.getenv('API_URL', 'http://localhost:8000')

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
    page_icon="📚",
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
# Sidebar Navigation
# =========================

if 'user' in st.session_state:
    if st.session_state.user.get('is_professor'):
        with st.sidebar:
            st.title('Professor Menu')
            st.page_link('pages/2_Professor_View.py', label='Professor View', icon='👨‍🏫')
            st.page_link('pages/5_Prompt_Management.py', label='Prompt Management', icon='📝')
            st.page_link('pages/7_Class_Statistics.py', label='Class Statistics', icon='📈')
            st.page_link('pages/6_Assignment_Management.py', label='Assignment Management', icon='🗂️')
            st.page_link('pages/create_class.py', label='Create Class', icon='➕')
            st.page_link('login.py', label='Logout', icon='🚪') 
    else:
        with st.sidebar:
            st.title('Student Menu')
            st.page_link('pages/3_Student_View.py', label='Student View', icon='👨‍🎓')
            st.page_link('pages/1_Home.py', label='Home', icon='🏠')
            st.page_link('pages/4_Grades_View.py', label='Grades View', icon='📊')
            st.page_link('login.py', label='Logout', icon='🚪') 

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
        }

        /* Apply theme */
        html, body, .stApp {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Header styling */
        .header {
            background-color: #4a9a9b;
            padding: 2rem;
            text-align: center;
            color: #ffffff;
            margin-bottom: 2rem;
        }

        /* Card styling */
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        /* Button styling */
        .stButton > button {
            background-color: var(--primary-bg);
            color: white;
            border-radius: 0.375rem;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }

        .stButton > button:hover {
            background-color: var(--primary-hover);
        }

        /* Form styling */
        .stTextInput > div > div > input {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            padding: 0.5rem;
        }

        .stTextArea > div > div > textarea {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            padding: 0.5rem;
        }

        /* Progress bar styling */
        .stProgress > div > div > div {
            background-color: var(--primary-bg);
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# Header and Access Control
# =========================

# Header
st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown('<h1>Create Class</h1>', unsafe_allow_html=True)
st.markdown('<p>Create a new class for the system</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Check if user is logged in and is a professor
if 'user' not in st.session_state:
    st.switch_page("login.py")

if not st.session_state.user.get('is_professor'):
    st.error("This page is for professors only")
    st.stop()

# =========================
# Create Class Form
# =========================

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### Create New Class")

with st.form("create_class_form"):
    # Class name
    class_name = st.text_input(
        "Class Name",
        placeholder="e.g., Introduction to Python",
        help="Enter the full name of your class"
    )
    
    # Class code
    class_code = st.text_input(
        "Class Code",
        placeholder="e.g., CS1111",
        help="Enter a unique code for your class (e.g., CS1111)"
    )
    
    # Class description
    class_description = st.text_area(
        "Class Description",
        placeholder="Enter a detailed description of your class...",
        help="Describe the class content, objectives, and any other relevant information",
        height=150
    )
    
    # Additional information
    st.markdown("### Additional Information (Optional)")
    
    # Prerequisites
    prerequisites = st.text_area(
        "Prerequisites",
        placeholder="List any prerequisites for the class...",
        help="Enter any prerequisites or recommended background knowledge",
        height=100
    )
    
    # Learning objectives
    learning_objectives = st.text_area(
        "Learning Objectives",
        placeholder="List the main learning objectives...",
        help="Enter what students will learn in this class",
        height=100
    )
    
    # Submit button
    submit_button = st.form_submit_button("Create Class")

    if submit_button:
        if not class_name or not class_code:
            st.error("Please fill in the required fields (Class Name and Class Code)")
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
                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                    json=class_data
                )
                response.raise_for_status()
                
                st.success("Class created successfully!")
                
                # Add the current user as a professor of the class
                class_data = response.json()
                professor_id = str(st.session_state.user['user_id'])
                
                response = requests.post(
                    f"{API_URL}/classes/{class_data['id']}/add-professor/{professor_id}",
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                response.raise_for_status()
                
                st.success("You have been added as a professor of this class!")

                # Create default assignments
                st.info("Creating default assignments...")
                progress_bar = st.progress(0)
                
                for i, assignment in enumerate(DEFAULT_ASSIGNMENTS):
                    try:
                        response = requests.post(
                            f"{API_URL}/classes/{class_data['id']}/assignments/",
                            headers={"Authorization": f"Bearer {st.session_state.token}"},
                            json={
                                "name": assignment["name"],
                                "description": assignment["description"],
                                "class_id": class_data['id']
                            }
                        )
                        response.raise_for_status()
                        progress_bar.progress((i + 1) / len(DEFAULT_ASSIGNMENTS))
                    except requests.RequestException as e:
                        st.error(f"Error creating assignment '{assignment['name']}': {str(e)}")
                        continue
                
                st.success("Default assignments created successfully!")
                
                # Clear the form and redirect to professor view
                time.sleep(2)
                st.switch_page("pages/2_Professor_View.py")
                
            except requests.RequestException as e:
                error_msg = str(e)
                if "Class code already exists" in error_msg:
                    st.error("This class code is already in use. Please choose a different code.")
                else:
                    st.error(f"Error creating class: {error_msg}")

st.markdown('</div>', unsafe_allow_html=True)
