# =========================
# Prompt Management Page
# =========================
# This file implements the prompt management interface for professors.
# Professors can view, edit, and set the grading prompt used by the AI.
# Includes prompt history, sample prompt, and editing functionality.

import streamlit as st
import requests
import os
from dotenv import load_dotenv

# =========================
# Environment and API Setup
# =========================

# Load environment variables
load_dotenv()
API_URL = os.getenv('API_URL', 'http://localhost:8000')

# =========================
# Page Configuration and Sidebar
# =========================

st.set_page_config(
    page_title="Prompt Management",
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
# Sidebar Navigation
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
# Page Header and Access Control
# =========================

st.title("📝 Grading Prompt Management")

# Check if user is logged in and is a professor
if 'user' not in st.session_state:
    st.switch_page("login.py")

if not st.session_state.user.get('is_professor'):
    st.error("This page is for professors only")
    st.stop()

# =========================
# API Helper Functions
# =========================

def get_auth_header():
    """
    Return the authorization header for API requests using the current session token.
    """
    return {"Authorization": f"Bearer {st.session_state.token}"}

def fetch_current_prompt():
    """
    Fetch the current grading prompt from the backend API.
    Returns the prompt string or an empty string if not set.
    """
    try:
        response = requests.get(f"{API_URL}/grading/custom-prompt", headers=get_auth_header())
        response.raise_for_status()
        return response.json().get('prompt', '')
    except Exception as e:
        st.error(f"Error fetching current prompt: {str(e)}")
        return ''

def fetch_sample_prompt():
    """
    Fetch a sample grading prompt from the backend API.
    Returns the sample prompt string or an empty string if not available.
    """
    try:
        response = requests.get(f"{API_URL}/grading/sample-prompt", headers=get_auth_header())
        response.raise_for_status()
        return response.json().get('prompt', '')
    except Exception as e:
        st.error(f"Error fetching sample prompt: {str(e)}")
        return ''

def fetch_prompt_history():
    """
    Fetch the prompt history for the grading system.
    Currently a stub: returns a list with the sample and current prompt for demonstration.
    """
    # TODO: Replace with real API call if available
    # For now, just return a list with the current prompt and sample prompt for demo
    current = fetch_current_prompt()
    sample = fetch_sample_prompt()
    # Simulate history: [sample, current] if different
    history = []
    if sample and sample != current:
        history.append(sample)
    if current:
        history.append(current)
    return history

# =========================
# Prompt Display and Management UI
# =========================

# Show current prompt
st.subheader("Current Grading Prompt")
current_prompt = fetch_current_prompt()
st.code(current_prompt or "No prompt set.", language="text")

# Show sample prompt in an expander
with st.expander("Sample Grading Prompt", expanded=False):
    sample_prompt = fetch_sample_prompt()
    st.code(sample_prompt or "No sample prompt available.", language="text")

# Show prompt history in expandable sections with 'Use this prompt' button
st.subheader("Prompt History")
prompt_history = fetch_prompt_history()
if prompt_history:
    for i, prompt in enumerate(prompt_history[::-1], 1):
        version_label = f"Version {len(prompt_history)-i+1}"
        with st.expander(f"{version_label}", expanded=False):
            st.code(prompt, language="text")
            if st.button(f"Use this prompt", key=f"use_prompt_{i}"):
                try:
                    response = requests.post(
                        f"{API_URL}/grading/custom-prompt",
                        headers={**get_auth_header(), "Content-Type": "application/json"},
                        json={"prompt": prompt}
                    )
                    response.raise_for_status()
                    st.success(f"Prompt from {version_label} is now set as your current prompt!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error applying prompt: {str(e)}")
else:
    st.info("No prompt history available.")

# =========================
# Edit and Save New Prompt UI
# =========================

st.subheader("Edit and Save New Prompt")
new_prompt = st.text_area(
    "Enter your new grading prompt here:",
    value=current_prompt,
    height=300,
    help="You can use {code} as a placeholder for the student's code."
)
if st.button("Save New Prompt"):
    try:
        response = requests.post(
            f"{API_URL}/grading/custom-prompt",
            headers={**get_auth_header(), "Content-Type": "application/json"},
            json={"prompt": new_prompt}
        )
        response.raise_for_status()
        st.success("New grading prompt saved successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error saving new prompt: {str(e)}")

# =========================
# Navigation
# =========================

if st.button("Back to Professor View"):
    st.switch_page("pages/2_Professor_View.py") 