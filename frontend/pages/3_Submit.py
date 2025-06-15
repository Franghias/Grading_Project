import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
API_URL = os.getenv('API_URL', 'http://localhost:8000')

# Page configuration
st.set_page_config(
    page_title="Submit Assignment",
    page_icon="📝",
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
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown('<h1>Submit Assignment</h1>', unsafe_allow_html=True)
st.markdown('<p>Submit your code for grading</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Check if user is logged in
if 'user' not in st.session_state:
    st.error("Please login first")
    st.stop()

# Get user's enrolled classes
try:
    response = requests.get(
        f"{API_URL}/classes/",
        headers={"Authorization": f"Bearer {st.session_state.token}"}
    )
    response.raise_for_status()
    classes = response.json()
except requests.RequestException as e:
    st.error(f"Error fetching classes: {str(e)}")
    st.stop()

if not classes:
    st.warning("You are not enrolled in any classes")
    st.stop()

# Class selection
selected_class = st.selectbox(
    "Select a class",
    options=classes,
    format_func=lambda x: f"{x['name']} ({x['code']})"
)

if selected_class:
    # Get assignments for the selected class
    try:
        response = requests.get(
            f"{API_URL}/classes/{selected_class['id']}/assignments/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        response.raise_for_status()
        assignments = response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching assignments: {str(e)}")
        st.stop()

    if not assignments:
        st.warning("No assignments found for this class")
    else:
        # Assignment selection
        selected_assignment = st.selectbox(
            "Select an assignment",
            options=assignments,
            format_func=lambda x: x['name']
        )

        if selected_assignment:
            # Submission form
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"### {selected_assignment['name']}")
            if selected_assignment.get('description'):
                st.markdown(selected_assignment['description'])
            
            # Code input
            code = st.text_area(
                "Enter your code",
                height=300,
                help="Write your Python code here"
            )
            
            # File upload
            uploaded_file = st.file_uploader(
                "Or upload a Python file",
                type=['py'],
                help="Upload a .py file instead of writing code directly"
            )
            
            # Submit button
            if st.button("Submit"):
                if not code and not uploaded_file:
                    st.error("Please either enter code or upload a file")
                else:
                    try:
                        # Prepare form data
                        files = {}
                        data = {
                            "class_id": str(selected_class['id']),
                            "assignment_id": str(selected_assignment['id'])
                        }
                        
                        if uploaded_file:
                            files['file'] = uploaded_file
                        else:
                            data['code'] = code
                        
                        # Submit code
                        response = requests.post(
                            f"{API_URL}/submissions/",
                            headers={"Authorization": f"Bearer {st.session_state.token}"},
                            data=data,
                            files=files
                        )
                        response.raise_for_status()
                        
                        st.success("Submission successful!")
                        time.sleep(2)
                        st.experimental_rerun()
                    except requests.RequestException as e:
                        st.error(f"Error submitting code: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True) 