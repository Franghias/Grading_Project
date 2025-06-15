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
    page_title="Student View",
    page_icon="👨‍🎓",
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
st.markdown('<h1>Student View</h1>', unsafe_allow_html=True)
st.markdown('<p>View and enroll in available classes</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Check if user is logged in and is a student
if 'user' not in st.session_state:
    st.error("Please login first")
    st.stop()

if st.session_state.user.get('is_professor'):
    st.error("This page is for students only")
    st.stop()

# Get student's classes (both enrolled and available)
try:
    response = requests.get(
        f"{API_URL}/classes/",
        headers={"Authorization": f"Bearer {st.session_state.token}"}
    )
    response.raise_for_status()
    all_classes = response.json()
except requests.RequestException as e:
    st.error(f"Error fetching classes: {str(e)}")
    st.stop()

# Separate enrolled and available classes
enrolled_classes = [c for c in all_classes if c.get('is_enrolled')]
available_classes = [c for c in all_classes if not c.get('is_enrolled')]

# Display enrolled classes if any
if enrolled_classes:
    st.markdown("### Your Enrolled Classes")
    for class_data in enrolled_classes:
        with st.expander(f"{class_data['name']} ({class_data['code']})"):
            st.markdown(f"**Description:** {class_data['description'] or 'No description available'}")
            st.markdown(f"**Prerequisites:** {class_data['prerequisites'] or 'None'}")
            st.markdown(f"**Learning Objectives:** {class_data['learning_objectives'] or 'None'}")
            st.markdown("**Professors:**")
            for professor in class_data['professors']:
                st.markdown(f"- {professor['name']} ({professor['email']})")
            
            # Button to view class details
            if st.button(f"View {class_data['name']} Details", key=f"view_{class_data['id']}"):
                # Store the complete class data in session state
                st.session_state.selected_class = {
                    "id": class_data['id'],
                    "name": class_data['name'],
                    "code": class_data['code'],
                    "description": class_data['description'],
                    "prerequisites": class_data['prerequisites'],
                    "learning_objectives": class_data['learning_objectives'],
                    "professors": class_data['professors'],
                    "students": class_data['students'],
                    "assignments": class_data['assignments']
                }
                st.switch_page("pages/1_Home.py")

# Display available classes
if available_classes:
    st.markdown("### Available Classes")
    for class_data in available_classes:
        with st.expander(f"{class_data['name']} ({class_data['code']})"):
            st.markdown(f"**Description:** {class_data['description'] or 'No description available'}")
            st.markdown(f"**Prerequisites:** {class_data['prerequisites'] or 'None'}")
            st.markdown(f"**Learning Objectives:** {class_data['learning_objectives'] or 'None'}")
            st.markdown("**Professors:**")
            for professor in class_data['professors']:
                st.markdown(f"- {professor['name']} ({professor['email']})")
            
            # Enroll button
            if st.button(f"Enroll in {class_data['name']}", key=f"enroll_{class_data['id']}"):
                try:
                    response = requests.post(
                        f"{API_URL}/classes/{class_data['id']}/enroll",
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    response.raise_for_status()
                    st.success(f"Successfully enrolled in {class_data['name']}!")
                    
                    # After successful enrollment, store the class data and redirect to Home
                    st.session_state.selected_class = {
                        "id": class_data['id'],
                        "name": class_data['name'],
                        "code": class_data['code'],
                        "description": class_data['description'],
                        "prerequisites": class_data['prerequisites'],
                        "learning_objectives": class_data['learning_objectives'],
                        "professors": class_data['professors'],
                        "students": class_data['students'],
                        "assignments": class_data['assignments']
                    }
                    time.sleep(2)
                    st.switch_page("pages/1_Home.py")
                except requests.RequestException as e:
                    st.error(f"Error enrolling in class: {str(e)}")
else:
    st.info("No available classes to enroll in at the moment.")

# Logout button
if st.button("Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("login.py") 