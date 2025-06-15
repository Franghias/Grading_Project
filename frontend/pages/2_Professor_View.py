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
    page_title="Professor View",
    page_icon="👨‍🏫",
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
st.markdown('<h1>Professor View</h1>', unsafe_allow_html=True)
st.markdown('<p>View and manage class submissions</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Check if user is logged in and is a professor
if 'user' not in st.session_state:
    st.error("Please login first")
    st.stop()

if not st.session_state.user.get('is_professor'):
    st.error("This page is for professors only")
    st.stop()

# Get professor's classes
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
    st.warning("You are not teaching any classes yet")
    
    # Add button to create new class
    if st.button("Create New Class", type="primary"):
        st.switch_page("pages/create_class.py")
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
        
        # Add option to create default assignments
        if st.button("Create Default Assignments"):
            default_assignments = [
                "Hello World",
                "Print",
                "Variable Definition and How to Use It",
                "If Else Statement",
                "For Loop"
            ]
            
            for assignment_name in default_assignments:
                try:
                    response = requests.post(
                        f"{API_URL}/classes/{selected_class['id']}/assignments/",
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                        json={"name": assignment_name, "class_id": selected_class['id']}
                    )
                    response.raise_for_status()
                except requests.RequestException as e:
                    st.error(f"Error creating assignment '{assignment_name}': {str(e)}")
                    continue
            
            st.success("Default assignments created successfully!")
            st.experimental_rerun()
    else:
        # Assignment selection
        selected_assignment = st.selectbox(
            "Select an assignment",
            options=assignments,
            format_func=lambda x: x['name']
        )

        if selected_assignment:
            # Get submissions for the selected assignment
            try:
                response = requests.get(
                    f"{API_URL}/classes/{selected_class['id']}/assignments/{selected_assignment['id']}/submissions",
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                response.raise_for_status()
                submissions = response.json()
            except requests.RequestException as e:
                st.error(f"Error fetching submissions: {str(e)}")
                st.stop()

            if not submissions:
                st.info("No submissions found for this assignment")
            else:
                # Display submissions
                st.subheader(f"Submissions for {selected_assignment['name']}")
                
                # Group submissions by user
                user_submissions = {}
                for submission in submissions:
                    user_id = submission['user_id']
                    if user_id not in user_submissions:
                        user_submissions[user_id] = []
                    user_submissions[user_id].append(submission)

                # Display submissions for each user
                for user_id, user_subs in user_submissions.items():
                    with st.expander(f"User ID: {user_id} - {len(user_subs)} submission(s)"):
                        for submission in user_subs:
                            st.markdown("---")
                            st.markdown(f"**Submission ID:** {submission['id']}")
                            st.markdown(f"**Submitted at:** {submission['created_at']}")
                            if submission['grade'] is not None:
                                st.markdown(f"**Grade:** {submission['grade']}")
                            if submission['feedback']:
                                st.markdown(f"**Feedback:** {submission['feedback']}")
                            st.markdown("**Code:**")
                            st.code(submission['code'], language="python") 