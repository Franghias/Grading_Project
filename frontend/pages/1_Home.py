# =========================
# Home Page (Student/Professor Dashboard)
# =========================
# This file implements the main dashboard for both students and professors.
# It displays class information, assignments, submissions, and grades, and provides navigation to other pages.

import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time
import base64
from itertools import cycle
import json
from datetime import datetime

# =========================
# Page Configuration and Sidebar
# =========================

# Page configuration
st.set_page_config(
    page_title="Home Page",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide default sidebar and show custom sidebar for students
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

if 'user' in st.session_state and not st.session_state.user.get('is_professor'):
    with st.sidebar:
        st.title('Student Menu')
        st.page_link('pages/3_Student_View.py', label='Student View', icon='👨‍🎓')
        st.page_link('pages/1_Home.py', label='Home', icon='🏠')
        st.page_link('pages/4_Grades_View.py', label='Grades View', icon='📊')
        st.page_link('login.py', label='Logout', icon='🚪')

# =========================
# Environment and API Setup
# =========================

# Load environment variables
load_dotenv()
API_URL = os.getenv('API_URL', 'http://localhost:8000')

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
    </style>
""", unsafe_allow_html=True)

# =========================
# Authentication and Navigation
# =========================

# Check if user is logged in
if 'token' not in st.session_state:
    st.warning("Please login first")
    st.switch_page("login.py")

# Redirect based on user role and class selection
if not st.session_state.user.get('is_professor'):
    if 'selected_class' not in st.session_state:
        st.warning("Please select a class from the Student View")
        st.switch_page("pages/3_Student_View.py")
elif 'selected_class' not in st.session_state:
    st.warning("Please go to Professor View to manage your classes")
    st.switch_page("pages/2_Professor_View.py")

# =========================
# Main Dashboard Logic
# =========================

# Get the selected class from session state
selected_class = st.session_state.selected_class

# -------------------------
# Helper: Refresh class data to get latest assignments
# -------------------------
def refresh_class_data(class_id):
    """
    Fetch the latest class data including assignments from the API.
    Updates the session state with fresh data.
    """
    try:
        response = requests.get(
            f"{API_URL}/classes/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        response.raise_for_status()
        all_classes = response.json()
        
        # Find the current class in the updated data
        for class_data in all_classes:
            if class_data['id'] == class_id:
                st.session_state.selected_class = class_data
                return class_data
        
        # If class not found, return the original data
        return selected_class
    except requests.RequestException as e:
        st.error(f"Error refreshing class data: {str(e)}")
        return selected_class

# Refresh class data to get latest assignments
selected_class = refresh_class_data(selected_class['id'])

# -------------------------
# Helper: Get user submissions for a class
# -------------------------
def get_user_submissions_for_class(class_id):
    """
    Fetch all submissions for the current user for a given class.
    Returns a list of submission dicts.
    """
    try:
        response = requests.get(
            f"{API_URL}/submissions/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        response.raise_for_status()
        all_submissions = response.json()
        # Filter submissions for the current class
        class_submissions = [sub for sub in all_submissions if sub.get('class_id') == class_id]
        return class_submissions
    except requests.RequestException as e:
        st.error(f"Error fetching submissions: {str(e)}")
        return []

# Get user submissions for the current class
user_submissions = get_user_submissions_for_class(selected_class['id'])

# Create a dictionary to map assignment_id to submissions
assignment_submissions = {}
for submission in user_submissions:
    assignment_id = submission.get('assignment_id')
    if assignment_id not in assignment_submissions:
        assignment_submissions[assignment_id] = []
    assignment_submissions[assignment_id].append(submission)

# -------------------------
# Header and Class Info
# -------------------------

# Header
st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown(f'<h1>{selected_class["name"]} ({selected_class["code"]})</h1>', unsafe_allow_html=True)
st.markdown(f'<p>Welcome, {st.session_state.user["name"]}!</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Main content container
st.markdown('<div class="container mx-auto px-4 py-8">', unsafe_allow_html=True)

# Class Information Card with refresh button
st.markdown('<div class="card">', unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("### Class Information")
with col2:
    if st.button("🔄 Refresh", type="secondary", help="Refresh class data and assignments"):
        st.rerun()

st.markdown(f"**Description:** {selected_class['description'] or 'No description available'}")
st.markdown(f"**Prerequisites:** {selected_class['prerequisites'] or 'None'}")
st.markdown(f"**Learning Objectives:** {selected_class['learning_objectives'] or 'None'}")
st.markdown("**Professors:**")
for professor in selected_class['professors']:
    st.markdown(f"- {professor['name']} ({professor['email']})")
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# Assignments Section
# -------------------------

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### Assignments")
if selected_class['assignments']:
    for assignment in selected_class['assignments']:
        with st.expander(f"{assignment['name']}", expanded=False):
            st.markdown(f"**Description:** {assignment['description'] or 'No description available'}")
            # Show existing submissions and grades for this assignment
            assignment_id = assignment['id']
            if assignment_id in assignment_submissions:
                submissions = assignment_submissions[assignment_id]
                if submissions:
                    st.markdown("#### Your Submissions")
                    for i, submission in enumerate(submissions, 1):
                        st.markdown(f"**Submission {i} - {submission['created_at'][:10]}**")
                        # Display grades in two sections
                        col1, col2 = st.columns(2)
                        with col1:
                            # AI Grade Section
                            if submission['ai_grade'] is not None:
                                st.markdown("""
                                    <div style="
                                        background-color: #f0f9ff;
                                        padding: 1.5rem;
                                        border-radius: 0.5rem;
                                        text-align: center;
                                        border: 1px solid #bae6fd;
                                        margin-bottom: 1rem;
                                    ">
                                        <h3 style="margin: 0 0 1rem 0; color: #0369a1;">🤖 AI Grade</h3>
                                        <h1 style="margin: 0; color: #0369a1; font-size: 2.5rem;">{ai_grade}</h1>
                                        <p style="margin: 0; color: #0369a1; font-size: 1rem;">out of 100</p>
                                    </div>
                                """.format(ai_grade=submission['ai_grade']), unsafe_allow_html=True)
                            else:
                                st.markdown("""
                                    <div style="
                                        background-color: #fef3c7;
                                        padding: 1.5rem;
                                        border-radius: 0.5rem;
                                        text-align: center;
                                        border: 1px solid #fde68a;
                                        margin-bottom: 1rem;
                                    ">
                                        <h3 style="margin: 0 0 1rem 0; color: #92400e;">🤖 AI Grade</h3>
                                        <p style="margin: 0; color: #92400e; font-size: 1rem;">Not graded yet</p>
                                    </div>
                                """, unsafe_allow_html=True)
                        with col2:
                            # Final Grade Section
                            if submission['professor_grade'] is not None:
                                st.markdown("""
                                    <div style="
                                        background-color: #fef7ff;
                                        padding: 2rem;
                                        border-radius: 0.5rem;
                                        text-align: center;
                                        border: 2px solid #c084fc;
                                        margin-bottom: 2rem;
                                    ">
                                        <h2 style="margin: 0 0 1rem 0; color: #7c3aed;">📊 Final Grade</h2>
                                        <h1 style="margin: 0; color: #7c3aed; font-size: 3rem;">{professor_grade}</h1>
                                        <p style="margin: 0; color: #7c3aed; font-size: 1.2rem;">out of 100</p>
                                        <p style="margin: 0; color: #7c3aed; font-size: 0.9rem; margin-top: 0.5rem;">
                                            Professor's grade
                                        </p>
                                    </div>
                                """.format(
                                    professor_grade=submission['professor_grade']
                                ), unsafe_allow_html=True)
                            else:
                                st.markdown("""
                                    <div style="
                                        background-color: #fef7ff;
                                        padding: 2rem;
                                        border-radius: 0.5rem;
                                        text-align: center;
                                        border: 2px solid #c084fc;
                                        margin-bottom: 2rem;
                                    ">
                                        <h2 style="margin: 0 0 1rem 0; color: #7c3aed;">📊 Final Grade</h2>
                                        <h1 style="margin: 0; color: #7c3aed; font-size: 2rem;">Wait for Professor Feedback</h1>
                                    </div>
                                """, unsafe_allow_html=True)
                        
                        # Feedback sections
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # AI Feedback
                            st.markdown("### 🤖 AI Feedback")
                            if submission['ai_feedback']:
                                st.markdown(f"""
                                    <div style="
                                        background-color: #f8fafc;
                                        padding: 1.5rem;
                                        border-radius: 0.5rem;
                                        border: 1px solid #e2e8f0;
                                        margin-bottom: 1rem;
                                    ">
                                        {submission['ai_feedback']}
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown("""
                                    <div style="
                                        background-color: #fef3c7;
                                        padding: 1.5rem;
                                        border-radius: 0.5rem;
                                        border: 1px solid #fde68a;
                                        margin-bottom: 1rem;
                                    ">
                                        No AI feedback available
                                    </div>
                                """, unsafe_allow_html=True)
                        
                        with col2:
                            # Professor Feedback
                            st.markdown("### 👨‍🏫 Professor Feedback")
                            if submission['professor_feedback']:
                                # Convert newlines to HTML br tags to preserve formatting
                                formatted_feedback = submission['professor_feedback'].replace('\n', '<br>')
                                st.markdown(f"""
                                    <div style="
                                        background-color: #f0fdf4;
                                        padding: 1.5rem;
                                        border-radius: 0.5rem;
                                        border: 1px solid #bbf7d0;
                                        margin-bottom: 1rem;
                                    ">
                                        {formatted_feedback}
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown("""
                                    <div style="
                                        background-color: #fef3c7;
                                        padding: 1.5rem;
                                        border-radius: 0.5rem;
                                        border: 1px solid #fde68a;
                                        margin-bottom: 1rem;
                                    ">
                                        No professor feedback yet
                                    </div>
                                """, unsafe_allow_html=True)
                        
                        # Show submitted code
                        # with st.expander("Your Submitted Code", expanded=False):
                        st.code(submission['code'], language='python')
                else:
                    st.info("No submissions yet for this assignment.")
            else:
                st.info("No submissions yet for this assignment.")
            
            # Submission form for this assignment
            st.markdown("#### Submit New Code")
            submission_method = st.radio(
                "Choose how you want to submit your code:",
                ["Type Code", "Upload File"],
                horizontal=True,
                key=f"method_{assignment['id']}"
            )
            
            with st.form(f"submission_form_{assignment['id']}"):
                if submission_method == "Type Code":
                    code = st.text_area(
                        "Enter your Python code here:",
                        height=300,
                        placeholder="Write your code here...",
                        key=f"code_{assignment['id']}"
                    )
                    file = None
                else:
                    file = st.file_uploader(
                        "Choose a Python file from your computer:",
                        type=['py'],
                        key=f"file_{assignment['id']}"
                    )
                    code = None
                
                submit_button = st.form_submit_button("Submit Code")
                
                if submit_button:
                    if (submission_method == "Type Code" and code) or (submission_method == "Upload File" and file):
                        try:
                            headers = {"Authorization": f"Bearer {st.session_state.token}"}
                            files = None
                            data = None
                            if file:
                                files = {"file": file}
                            else:
                                data = {"code": code}
                            # Add class_id and assignment_id to the request
                            if data:
                                data["class_id"] = str(selected_class['id'])
                                data["assignment_id"] = str(assignment['id'])
                            else:
                                data = {
                                    "class_id": str(selected_class['id']),
                                    "assignment_id": str(assignment['id'])
                                }
                            response = requests.post(
                                f"{API_URL}/submissions/",
                                headers=headers,
                                files=files,
                                data=data
                            )
                            response.raise_for_status()
                            result = response.json()
                            st.success("Submission successful!")
                            # Only show grades and feedback if professor has graded
                            if result['professor_grade'] is None:
                                st.markdown("""
                                    <div style="
                                        background-color: #fef3c7;
                                        padding: 2rem;
                                        border-radius: 0.5rem;
                                        text-align: center;
                                        border: 2px solid #fde68a;
                                        margin-bottom: 2rem;
                                    ">
                                        <h2 style="margin: 0 0 1rem 0; color: #92400e;">Waiting for professor feedback</h2>
                                        <p style="margin: 0; color: #92400e; font-size: 1.2rem;">Your submission has been received and is pending review by your professor.</p>
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                # Show grades and feedback as before
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("""
                                        <div style="
                                            background-color: #f0f9ff;
                                            padding: 1.5rem;
                                            border-radius: 0.5rem;
                                            text-align: center;
                                            border: 1px solid #bae6fd;
                                            margin-bottom: 1rem;
                                        ">
                                            <h3 style="margin: 0 0 1rem 0; color: #0369a1;">🤖 AI Grade</h3>
                                            <h1 style="margin: 0; color: #0369a1; font-size: 2.5rem;">{ai_grade}</h1>
                                            <p style="margin: 0; color: #0369a1; font-size: 1rem;">out of 100</p>
                                        </div>
                                    """.format(ai_grade=result['ai_grade']), unsafe_allow_html=True)
                                with col2:
                                    st.markdown("""
                                        <div style="
                                            background-color: #f0fdf4;
                                            padding: 1.5rem;
                                            border-radius: 0.5rem;
                                            text-align: center;
                                            border: 1px solid #bbf7d0;
                                            margin-bottom: 1rem;
                                        ">
                                            <h3 style="margin: 0 0 1rem 0; color: #166534;">👨‍🏫 Professor Grade</h3>
                                            <h1 style="margin: 0; color: #166534; font-size: 2.5rem;">{professor_grade}</h1>
                                            <p style="margin: 0; color: #166534; font-size: 1rem;">out of 100</p>
                                        </div>
                                    """.format(professor_grade=result['professor_grade']), unsafe_allow_html=True)
                                st.markdown("""
                                    <div style="
                                        background-color: #fef7ff;
                                        padding: 2rem;
                                        border-radius: 0.5rem;
                                        text-align: center;
                                        border: 2px solid #c084fc;
                                        margin-bottom: 2rem;
                                    ">
                                        <h2 style="margin: 0 0 1rem 0; color: #7c3aed;">📊 Final Grade</h2>
                                        <h1 style="margin: 0; color: #7c3aed; font-size: 3rem;">{final_grade}</h1>
                                        <p style="margin: 0; color: #7c3aed; font-size: 1.2rem;">out of 100</p>
                                        <p style="margin: 0; color: #7c3aed; font-size: 0.9rem; margin-top: 0.5rem;">
                                            Professor's grade (overrides AI)
                                        </p>
                                    </div>
                                """.format(final_grade=result['final_grade']), unsafe_allow_html=True)
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("### 🤖 AI Feedback")
                                    st.markdown(f"""
                                        <div style="
                                            background-color: #f8fafc;
                                            padding: 1.5rem;
                                            border-radius: 0.5rem;
                                            border: 1px solid #e2e8f0;
                                            margin-bottom: 1rem;
                                        ">
                                            {result['ai_feedback']}
                                        </div>
                                    """, unsafe_allow_html=True)
                                with col2:
                                    st.markdown("### 👨‍🏫 Professor Feedback")
                                    # Convert newlines to HTML br tags to preserve formatting
                                    formatted_feedback = result['professor_feedback'].replace('\n', '<br>')
                                    st.markdown(f"""
                                        <div style="
                                            background-color: #f0fdf4;
                                            padding: 1.5rem;
                                            border-radius: 0.5rem;
                                            border: 1px solid #bbf7d0;
                                            margin-bottom: 1rem;
                                        ">
                                            {formatted_feedback}
                                        </div>
                                    """, unsafe_allow_html=True)
                                st.code(result['code'], language='python')
                        except requests.RequestException as e:
                            st.error(f"Submission failed: {str(e)}")
                    else:
                        if submission_method == "Type Code":
                            st.error("Please enter your code in the text area")
                        else:
                            st.error("Please select a Python file to upload")
else:
    st.info("No assignments available for this class yet.")
st.markdown('</div>', unsafe_allow_html=True)

# Navigation buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Back to Student View"):
        st.switch_page("pages/3_Student_View.py")
with col2:
    if st.button("View All Grades"):
        st.switch_page("pages/4_Grades_View.py")
with col3:
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("login.py")

# Image Carousel setup (moved to end)
image_paths = [
    "image1.jpg",
    "image2.jpg",
    "image3.jpg",
    "image4.jpg",
    "image5.jpg",
]

# Add CSS for smooth image transitions
st.markdown("""
    <style>
        .image-container {
            width: 100%;
            height: 400px;
            position: relative;
            margin: 20px 0;
        }
        .stImage {
            transition: opacity 1s ease-in-out;
        }
        .fade-out {
            opacity: 0;
        }
    </style>
""", unsafe_allow_html=True)

# Create a placeholder for the image
image_placeholder = st.empty()

# Initialize image index in session state if not present
if 'image_index' not in st.session_state:
    st.session_state.image_index = 0

# Display the current image
current_image = image_paths[st.session_state.image_index]
with image_placeholder:
    st.image(current_image, use_container_width=True)

# Add JavaScript for fade effect
st.markdown("""
    <script>
        function fadeOut() {
            const images = document.querySelectorAll('.stImage img');
            images.forEach(img => img.classList.add('fade-out'));
        }
        
        // Start fade out after 4 seconds
        setTimeout(fadeOut, 4000);
    </script>
""", unsafe_allow_html=True)

# Update image index for the next transition
st.session_state.image_index = (st.session_state.image_index + 1) % len(image_paths)

# Add a small delay and rerun
time.sleep(5)
st.rerun()

# Custom CSS based on the template
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

        .header h1 {
            font-size: 2.25rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .header p {
            font-size: 1rem;
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

        /* Input and uploader styling */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stFileUploader > div {
            background-color: var(--input-bg);
            color: var(--text-color);
            border: 1px solid var(--input-border);
            border-radius: 0.375rem;
            padding: 0.5rem;
        }

        /* Code block styling */
        .code-block {
            background-color: var(--input-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            padding: 1rem;
            color: var(--text-color);
            font-family: 'Fira Code', monospace;
            font-size: 14px;
        }

        /* Sidebar styling */
        .css-1d391kg {
            background-color: var(--bg-color);
            border-right: 1px solid var(--border-color);
            padding: 1rem;
        }

        /* Success and error messages */
        .success, .error {
            padding: 1rem;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
        }

        .success { background-color: var(--success-bg); color: var(--success-text); }
        .error { background-color: var(--error-bg); color: var(--error-text); }
            
        /*where we hide the default pages */
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

def get_auth_header():
    token = st.session_state.get("token")
    if not token:
        st.error("Please log in first")
        st.stop()
    return {"Authorization": f"Bearer {token}"}

def main():
    st.title("Code Grading System")
    
    if "token" not in st.session_state:
        st.warning("Please log in to access the system")
        return
    
    # Get user info
    try:
        response = requests.get(f"{API_URL}/auth/me", headers=get_auth_header())
        user = response.json()
        
        # Show welcome message with role
        role = "Professor" if user.get("is_professor") else "Student"
        st.sidebar.write(f"Welcome, {user['name']}!")
        st.sidebar.write(f"Role: {role}")
        
        # Show different options based on user role
        if user.get("is_professor"):
            show_professor_interface()
        else:
            show_student_interface()
            
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_professor_interface():
    st.header("Professor Dashboard")
    
    # Create tabs for different professor functions
    tab1, tab2, tab3, tab4 = st.tabs(["Classes", "View Submissions", "Custom Grading Prompt", "Grade with Custom Prompt"])
    
    with tab1:
        show_class_management()
    
    with tab2:
        show_submissions()
    
    with tab3:
        show_custom_grading_prompt()
    
    with tab4:
        show_grade_with_custom_prompt()

def show_class_management():
    st.subheader("Class Management")
    
    # Create new class
    with st.expander("Create New Class", expanded=False):
        with st.form("create_class_form"):
            class_name = st.text_input("Class Name", placeholder="e.g., Introduction to Python")
            class_code = st.text_input("Class Code", placeholder="e.g., CS1111")
            class_description = st.text_area("Description", placeholder="Enter class description")
            
            if st.form_submit_button("Create Class"):
                if class_name and class_code:
                    try:
                        response = requests.post(
                            f"{API_URL}/classes/",
                            headers=get_auth_header(),
                            json={
                                "name": class_name,
                                "code": class_code,
                                "description": class_description
                            }
                        )
                        response.raise_for_status()
                        st.success("Class created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating class: {str(e)}")
                else:
                    st.warning("Please fill in all required fields")
    
    # List classes
    try:
        response = requests.get(f"{API_URL}/classes/", headers=get_auth_header())
        classes = response.json()
        
        if classes:
            st.subheader("Your Classes")
            for class_ in classes:
                with st.expander(f"{class_['name']} ({class_['code']})"):
                    st.write(f"Description: {class_['description']}")
                    
                    # Show class statistics
                    try:
                        submissions_response = requests.get(
                            f"{API_URL}/classes/{class_['id']}/submissions",
                            headers=get_auth_header()
                        )
                        submissions = submissions_response.json()
                        
                        # Calculate statistics
                        total_submissions = len(submissions)
                        avg_grade = sum(s['grade'] for s in submissions) / total_submissions if total_submissions > 0 else 0
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Submissions", total_submissions)
                        with col2:
                            st.metric("Average Grade", f"{avg_grade:.1f}")
                        
                        # Show student list
                        st.subheader("Enrolled Students")
                        user_ids = set(s['user_id'] for s in submissions)
                        for user_id in user_ids:
                            user_submissions = [s for s in submissions if s['user_id'] == user_id]
                            user_avg = sum(s['grade'] for s in user_submissions) / len(user_submissions)
                            st.write(f"User ID: {user_id} - Average Grade: {user_avg:.1f}")
                            
                            # Show student's submissions
                            with st.expander("View Submissions"):
                                for submission in user_submissions:
                                    st.write(f"Submission {submission['id']} - Grade: {submission['grade']}")
                                    st.code(submission['code'], language="python")
                                    st.write("Feedback:")
                                    st.json(submission['feedback'])
                    except Exception as e:
                        st.error(f"Error loading class statistics: {str(e)}")
        else:
            st.info("You haven't created any classes yet")
            
    except Exception as e:
        st.error(f"Error loading classes: {str(e)}")

def show_custom_grading_prompt():
    st.subheader("Custom Grading Prompt")
    # Get sample prompt
    try:
        response = requests.get(f"{API_URL}/grading/sample-prompt", headers=get_auth_header())
        sample_prompt = response.json()["prompt"]
        st.write("Sample Grading Prompt:")
        st.code(sample_prompt, language="text")
        st.write("Create Your Custom Grading Prompt:")
        st.markdown("""
        <div style='background-color:#fff3cd; color:#856404; border:1px solid #ffeeba; border-radius:0.375rem; padding:1rem; margin-bottom:1rem;'>
        <strong>Important:</strong> Your prompt <b>must</b> instruct the AI to return a JSON object with a top-level <code>grade</code> field (number) and a <code>feedback</code> object as shown below:
        </div>
        """, unsafe_allow_html=True)
        st.code('''{
  "grade": 95,
  "feedback": {
    "code_quality": "Good use of functions and clear variable names.",
    "bugs": [],
    "improvements": ["Add more comments for clarity."],
    "best_practices": ["Used list comprehensions."]
  }
}''', language="json")
        custom_prompt_title = st.text_input(
            "Prompt Title:",
            value="",
            help="Enter a descriptive title for your grading prompt."
        )
        custom_prompt = st.text_area(
            "Enter your grading prompt here",
            height=400,
            help="You can use {code} as a placeholder for the student's code."
        )
        if st.button("Save Custom Prompt"):
            if not custom_prompt_title.strip():
                st.warning("Please enter a title for your prompt.")
            elif not custom_prompt.strip():
                st.warning("Please enter your custom grading prompt")
            else:
                try:
                    response = requests.post(
                        f"{API_URL}/prompts/",
                        headers=get_auth_header(),
                        json={"prompt": custom_prompt, "class_id": None, "title": custom_prompt_title}
                    )
                    st.success("Custom grading prompt saved successfully!")
                except Exception as e:
                    st.error(f"Error saving custom prompt: {str(e)}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_grade_with_custom_prompt():
    st.subheader("Grade with Custom Prompt")
    # Get all submissions
    try:
        response = requests.get(f"{API_URL}/submissions/", headers=get_auth_header())
        submissions = response.json()
        if submissions:
            submission_id = st.selectbox(
                "Select a submission to grade",
                options=[s["id"] for s in submissions],
                format_func=lambda x: f"Submission {x}"
            )
            if st.button("Grade with Custom Prompt"):
                try:
                    response = requests.post(
                        f"{API_URL}/submissions/grade-with-custom-prompt",
                        headers=get_auth_header(),
                        json={"submission_id": submission_id}
                    )
                    result = response.json()
                    st.success("Grading completed!")
                    st.write(f"Grade: {result['grade']}")
                    st.write("Feedback:")
                    st.json(result['feedback'])
                except Exception as e:
                    st.error(f"Error grading submission: {str(e)}")
        else:
            st.info("No submissions available to grade")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_student_interface():
    st.header("Student Dashboard")
    
    # Create tabs for different student functions
    tab1, tab2, tab3 = st.tabs(["Classes", "Submit Code", "View Submissions"])
    
    with tab1:
        show_student_classes()
    
    with tab2:
        show_submit_code()
    
    with tab3:
        show_submissions()

def show_student_classes():
    st.subheader("Your Classes")
    
    try:
        # Get enrolled classes
        response = requests.get(f"{API_URL}/classes/", headers=get_auth_header())
        enrolled_classes = response.json()
        
        if enrolled_classes:
            st.write("Enrolled Classes:")
            for class_ in enrolled_classes:
                with st.expander(f"{class_['name']} ({class_['code']})"):
                    st.write(f"Description: {class_['description']}")
                    
                    # Show class statistics
                    try:
                        submissions_response = requests.get(
                            f"{API_URL}/classes/{class_['id']}/submissions",
                            headers=get_auth_header()
                        )
                        submissions = submissions_response.json()
                        
                        if submissions:
                            # Calculate statistics
                            total_submissions = len(submissions)
                            avg_grade = sum(s['grade'] for s in submissions) / total_submissions
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Your Submissions", total_submissions)
                            with col2:
                                st.metric("Your Average Grade", f"{avg_grade:.1f}")
                            
                            # Show submissions
                            st.subheader("Your Submissions")
                            for submission in submissions:
                                with st.expander(f"Submission {submission['id']} - Grade: {submission['grade']}"):
                                    st.write("Code:")
                                    st.code(submission['code'], language="python")
                                    st.write("Feedback:")
                                    st.json(submission['feedback'])
                        else:
                            st.info("No submissions yet")
                    except Exception as e:
                        st.error(f"Error loading class statistics: {str(e)}")
        else:
            st.info("You are not enrolled in any classes")
        
        # Show available classes to enroll
        st.subheader("Available Classes")
        try:
            # Get all classes
            all_classes_response = requests.get(f"{API_URL}/classes/", headers=get_auth_header())
            all_classes = all_classes_response.json()
            
            # Filter out enrolled classes
            available_classes = [c for c in all_classes if c not in enrolled_classes]
            
            if available_classes:
                for class_ in available_classes:
                    with st.expander(f"{class_['name']} ({class_['code']})"):
                        st.write(f"Description: {class_['description']}")
                        if st.button("Enroll", key=f"enroll_{class_['id']}"):
                            try:
                                response = requests.post(
                                    f"{API_URL}/classes/{class_['id']}/enroll",
                                    headers=get_auth_header()
                                )
                                response.raise_for_status()
                                st.success("Successfully enrolled in class!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error enrolling in class: {str(e)}")
            else:
                st.info("No available classes to enroll")
                
        except Exception as e:
            st.error(f"Error loading available classes: {str(e)}")
            
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_submit_code():
    st.subheader("Submit Code")
    
    try:
        # Get enrolled classes
        response = requests.get(f"{API_URL}/classes/", headers=get_auth_header())
        classes = response.json()
        
        if not classes:
            st.warning("You need to enroll in a class first")
            return
        
        # Let student select a class
        selected_class = st.selectbox(
            "Select a class",
            options=classes,
            format_func=lambda x: f"{x['name']} ({x['code']})"
        )
        
        if selected_class:
            # Add radio buttons for submission method
            submission_method = st.radio(
                "Choose how you want to submit your code:",
                ["Type Code", "Upload File"],
                horizontal=True,
                help="Select 'Type Code' to write your code directly, or 'Upload File' to submit a Python file from your computer"
            )
            
            # Create the form
            with st.form("submission_form"):
                if submission_method == "Type Code":
                    st.markdown("### Type Your Code")
                    code = st.text_area(
                        "Enter your Python code here:",
                        height=300,
                        placeholder="Write your code here...",
                        help="Type or paste your Python code in this box"
                    )
                    file = None
                else:
                    st.markdown("### Upload Your File")
                    file = st.file_uploader(
                        "Choose a Python file from your computer:",
                        type=['py'],
                        help="Select a .py file from your computer"
                    )
                    code = None
                
                # Add some spacing
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Submit button
                submit_button = st.form_submit_button(
                    "Submit Code",
                    help="Click to submit your code for grading"
                )
                
                if submit_button:
                    if (submission_method == "Type Code" and code) or (submission_method == "Upload File" and file):
                        try:
                            # Prepare the request
                            headers = get_auth_header()
                            files = None
                            data = None
                            
                            if file:
                                files = {"file": file}
                                data = {"class_id": str(selected_class["id"])}  # Convert to string for form data
                            else:
                                data = {
                                    "code": code,
                                    "class_id": str(selected_class["id"])  # Convert to string for form data
                                }
                            
                            # Make the request
                            response = requests.post(
                                f"{API_URL}/submissions/",
                                headers=headers,
                                files=files,
                                data=data
                            )
                            response.raise_for_status()
                            result = response.json()
                            
                            # Display results
                            st.success("Submission successful!")
                            
                            # Display grades in two sections
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # AI Grade Section
                                st.markdown("""
                                    <div style="
                                        background-color: #f0f9ff;
                                        padding: 1.5rem;
                                        border-radius: 0.5rem;
                                        text-align: center;
                                        border: 1px solid #bae6fd;
                                        margin-bottom: 1rem;
                                    ">
                                        <h3 style="margin: 0 0 1rem 0; color: #0369a1;">🤖 AI Grade</h3>
                                        <h1 style="margin: 0; color: #0369a1; font-size: 2.5rem;">{ai_grade}</h1>
                                        <p style="margin: 0; color: #0369a1; font-size: 1rem;">out of 100</p>
                                    </div>
                                """.format(ai_grade=result['ai_grade']), unsafe_allow_html=True)
                            
                            with col2:
                                # Final Grade Section
                                if result['professor_grade'] is not None:
                                    st.markdown("""
                                        <div style="
                                            background-color: #fef7ff;
                                            padding: 2rem;
                                            border-radius: 0.5rem;
                                            text-align: center;
                                            border: 2px solid #c084fc;
                                            margin-bottom: 2rem;
                                        ">
                                            <h2 style="margin: 0 0 1rem 0; color: #7c3aed;">📊 Final Grade</h2>
                                            <h1 style="margin: 0; color: #7c3aed; font-size: 3rem;">{professor_grade}</h1>
                                            <p style="margin: 0; color: #7c3aed; font-size: 1.2rem;">out of 100</p>
                                            <p style="margin: 0; color: #7c3aed; font-size: 0.9rem; margin-top: 0.5rem;">
                                                Professor's grade (overrides AI)
                                            </p>
                                        </div>
                                    """.format(
                                        professor_grade=result['professor_grade']
                                    ), unsafe_allow_html=True)
                                else:
                                    st.markdown("""
                                        <div style="
                                            background-color: #fef7ff;
                                            padding: 2rem;
                                            border-radius: 0.5rem;
                                            text-align: center;
                                            border: 2px solid #c084fc;
                                            margin-bottom: 2rem;
                                        ">
                                            <h2 style="margin: 0 0 1rem 0; color: #7c3aed;">📊 Final Grade</h2>
                                            <h1 style="margin: 0; color: #7c3aed; font-size: 2rem;">Wait for Professor Feedback</h1>
                                        </div>
                                    """, unsafe_allow_html=True)
                            
                            # Feedback sections
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # AI Feedback
                                st.markdown("### 🤖 AI Feedback")
                                st.markdown(f"""
                                    <div style="
                                        background-color: #f8fafc;
                                        padding: 1.5rem;
                                        border-radius: 0.5rem;
                                        border: 1px solid #e2e8f0;
                                        margin-bottom: 1rem;
                                    ">
                                        {result['ai_feedback']}
                                    </div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                # Professor Feedback
                                if result['professor_feedback']:
                                    st.markdown("### 👨‍🏫 Professor Feedback")
                                    # Convert newlines to HTML br tags to preserve formatting
                                    formatted_feedback = result['professor_feedback'].replace('\n', '<br>')
                                    st.markdown(f"""
                                        <div style="
                                            background-color: #f0fdf4;
                                            padding: 1.5rem;
                                            border-radius: 0.5rem;
                                            border: 1px solid #bbf7d0;
                                            margin-bottom: 1rem;
                                        ">
                                            {formatted_feedback}
                                        </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown("### 👨‍🏫 Professor Feedback")
                                    st.markdown("""
                                        <div style="
                                            background-color: #fef3c7;
                                            padding: 1.5rem;
                                            border-radius: 0.5rem;
                                            border: 1px solid #fde68a;
                                            margin-bottom: 1rem;
                                        ">
                                            No professor feedback yet
                                        </div>
                                    """, unsafe_allow_html=True)
                            
                            # Show submitted code
                            # with st.expander("Your Submitted Code", expanded=False):
                            st.code(result['code'], language='python')
                            
                        except requests.RequestException as e:
                            st.error(f"Submission failed: {str(e)}")
                    else:
                        if submission_method == "Type Code":
                            st.error("Please enter your code in the text area")
                        else:
                            st.error("Please select a Python file to upload")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_submissions():
    st.subheader("View Submissions")
    
    try:
        # Get enrolled classes
        response = requests.get(f"{API_URL}/classes/", headers=get_auth_header())
        classes = response.json()
        
        if not classes:
            st.warning("You need to enroll in a class first")
            return
        
        # Let student select a class
        selected_class = st.selectbox(
            "Select a class",
            options=classes,
            format_func=lambda x: f"{x['name']} ({x['code']})"
        )
        
        if selected_class:
            # Get submissions for selected class
            submissions_response = requests.get(
                f"{API_URL}/classes/{selected_class['id']}/submissions",
                headers=get_auth_header()
            )
            submissions = submissions_response.json()
            
            if submissions:
                # Calculate statistics
                total_submissions = len(submissions)
                avg_grade = sum(s['grade'] for s in submissions) / total_submissions
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Submissions", total_submissions)
                with col2:
                    st.metric("Average Grade", f"{avg_grade:.1f}")
                
                # Show submissions
                for submission in submissions:
                    with st.expander(f"Submission {submission['id']} - Grade: {submission['grade']}"):
                        st.write("Code:")
                        st.code(submission['code'], language="python")
                        st.write("Feedback:")
                        st.json(submission['feedback'])
            else:
                st.info("No submissions found for this class")
    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()

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