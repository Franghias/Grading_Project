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
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'

# Load environment variables from .env file
load_dotenv(dotenv_path=env_path)

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
            st.page_link('pages/7_Class_Statistics.py', label='Class Statistics', icon='📈')
            st.page_link('pages/6_Assignment_Management.py', label='Assignment Management', icon='🗂️')
            st.page_link('pages/create_class.py', label='Create Class', icon='➕')
            st.page_link('login.py', label='Logout', icon='🚪') 
            st.markdown("---")
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

def fetch_current_prompt(class_id=None):
    """
    Fetch the current grading prompt from the backend API for a specific class.
    Returns the prompt string or an empty string if not set.
    """
    try:
        if class_id is not None:
            response = requests.get(f"{API_URL}/grading/custom-prompt?class_id={class_id}", headers=get_auth_header())
        else:
            # fallback to sample prompt if no class_id
            return fetch_sample_prompt()
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

# Add a class selection dropdown at the top
classes = []
try:
    response = requests.get(f"{API_URL}/classes/", headers=get_auth_header())
    response.raise_for_status()
    classes = response.json()
except Exception as e:
    st.error(f"Error fetching classes: {str(e)}")

selected_class_id = None
if classes:
    selected_class = st.selectbox("Select a class to manage prompts for:", options=classes, format_func=lambda c: f"{c['name']} ({c['code']})")
    selected_class_id = selected_class['id']

# Restore the section to show the current prompt assigned to the selected class
if selected_class_id:
    st.subheader("Current Grading Prompt")
    try:
        response = requests.get(f"{API_URL}/classes/{selected_class_id}/prompt", headers=get_auth_header())
        if response.status_code == 200:
            class_prompt = response.json()
            st.write(f"**Title:** {class_prompt.get('title', 'Untitled Prompt')}")
            st.code(class_prompt.get('prompt', ''), language="text")
        else:
            st.info("No prompt assigned to this class yet. Please assign one below.")
    except Exception as e:
        st.error(f"Error fetching current class prompt: {str(e)}")

# Show prompt history in expandable sections with 'Use this prompt' button
st.subheader("Prompt History")

# Fetch all prompts from backend
professor_prompts = []
global_prompts = []
try:
    # Fetch professor's own unassigned prompts
    user_id = st.session_state.user['id']
    response_prof = requests.get(f"{API_URL}/prompts/", params={"created_by": user_id, "class_id": None}, headers=get_auth_header())
    response_prof.raise_for_status()
    professor_prompts = response_prof.json()
    # Fetch global prompts (created_by=None, class_id=None)
    response_global = requests.get(f"{API_URL}/prompts/", params={"created_by": None, "class_id": None}, headers=get_auth_header())
    response_global.raise_for_status()
    global_prompts = response_global.json()
except Exception as e:
    st.error(f"Error fetching prompts: {str(e)}")

# Professor Prompts Section (history: only prompts with class_id=None)
st.markdown("### 👨‍🏫 Professor Prompt History (Unassigned)")
if professor_prompts:
    for prompt in professor_prompts:
        if prompt['class_id'] is None:
            with st.expander(f"{prompt['title'] or 'Untitled Prompt'} (Unassigned)", expanded=False):
                st.code(prompt['prompt'], language="text")
                if st.button(f"Assign to this class", key=f"assign_prof_prompt_{prompt['id']}"):
                    if not selected_class_id:
                        st.warning("Please select a class to assign this prompt.")
                    else:
                        try:
                            assign_response = requests.post(
                                f"{API_URL}/classes/{selected_class_id}/prompt",
                                params={"prompt_id": prompt['id']},
                                headers=get_auth_header()
                            )
                            if assign_response.status_code == 200:
                                st.success("Prompt assigned to class!")
                                st.rerun()
                            else:
                                st.error(f"Failed to assign prompt: {assign_response.text}")
                        except Exception as e:
                            st.error(f"Error assigning prompt: {str(e)}")
else:
    st.info("No unassigned professor prompts available.")

# Global Prompts Section
st.markdown("### 🌐 Global Prompts (Available to All Classes)")
if global_prompts:
    for prompt in global_prompts:
        if prompt.get('created_by') is None:
            with st.expander(f"{prompt['title'] or 'Untitled Prompt'} (Global)", expanded=False):
                st.code(prompt['prompt'], language="text")
                copy_title = st.text_input(f"Title for your copy of this global prompt", value=prompt['title'] or '', key=f"copy_global_title_{prompt['id']}")
                if st.button(f"Copy to My Prompts", key=f"copy_global_prompt_{prompt['id']}"):
                    if not copy_title.strip():
                        st.warning("Please enter a title for your copy.")
                    else:
                        try:
                            response = requests.post(
                                f"{API_URL}/prompts/",
                                headers={**get_auth_header(), "Content-Type": "application/json"},
                                json={"prompt": prompt['prompt'], "class_id": None, "title": copy_title}
                            )
                            response.raise_for_status()
                            st.success("Copied to your prompt history! You can now assign it to a class from your history below.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error copying global prompt: {str(e)}")
else:
    st.info("No global prompts available.")

# =========================
# Edit and Save New Prompt UI (with edit existing option)
# =========================
st.subheader("Edit and Save New Prompt")

# Dropdown to select a prompt to edit, or create new
prompt_options = ["Create New Prompt"] + [p['title'] or f"Untitled Prompt {p['id']}" for p in professor_prompts]
selected_option = st.selectbox("Select a prompt to edit or create a new one:", options=prompt_options)

if selected_option == "Create New Prompt":
    edit_prompt_id = None
    edit_prompt_title = ""
    edit_prompt_body = ""
else:
    idx = prompt_options.index(selected_option) - 1
    edit_prompt_id = professor_prompts[idx]['id']
    edit_prompt_title = professor_prompts[idx]['title'] or ""
    edit_prompt_body = professor_prompts[idx]['prompt'] or ""

new_prompt_title = st.text_input(
    "Prompt Title:",
    value=edit_prompt_title,
    key="edit_new_prompt_title",
    help="Enter a descriptive title for your grading prompt."
)
new_prompt = st.text_area(
    "Enter your grading prompt here:",
    value=edit_prompt_body,
    key="edit_new_prompt_body",
    height=400,
    help="You can use {code} as a placeholder for the student's code."
)

required_phrase = '"grade":'
if st.button("Save Prompt"):
    if not new_prompt_title.strip():
        st.warning("Please enter a title for your prompt.")
    elif not new_prompt.strip():
        st.warning("Please enter your grading prompt.")
    elif required_phrase not in new_prompt:
        st.warning("Your prompt must instruct the AI to return a JSON object with a top-level 'grade' field. Please see the sample above.")
    else:
        try:
            if edit_prompt_id is not None:
                # Update existing prompt
                response = requests.put(
                    f"{API_URL}/prompts/{edit_prompt_id}",
                    headers={**get_auth_header(), "Content-Type": "application/json"},
                    json={"title": new_prompt_title, "prompt": new_prompt, "class_id": None}
                )
                response.raise_for_status()
                st.success("Prompt updated successfully!")
            else:
                # Create new prompt
                response = requests.post(
                    f"{API_URL}/prompts/",
                    headers={**get_auth_header(), "Content-Type": "application/json"},
                    json={"prompt": new_prompt, "class_id": None, "title": new_prompt_title}
                )
                response.raise_for_status()
                st.success("New grading prompt saved successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error saving prompt: {str(e)}")

# Add a button to push a new prompt to global prompt (class_id=None)
st.subheader("Create and Push to Global Prompt")
global_prompt_title = st.text_input(
    "Global Prompt Title:",
    value="",
    help="Enter a descriptive title for your global grading prompt."
)
global_prompt = st.text_area(
    "Enter your global grading prompt here:",
    value="",
    height=400,
    help="You can use {code} as a placeholder for the student's code."
)
if st.button("Push to Global Prompt"):
    required_phrase = '"grade":'
    if not global_prompt_title.strip():
        st.warning("Please enter a title for your global prompt.")
    elif not global_prompt.strip():
        st.warning("Please enter your global grading prompt.")
    elif required_phrase not in global_prompt:
        st.warning("Your prompt must instruct the AI to return a JSON object with a top-level 'grade' field. Please see the sample above.")
    else:
        try:
            response = requests.post(
                f"{API_URL}/prompts/",
                headers={**get_auth_header(), "Content-Type": "application/json"},
                json={"prompt": global_prompt, "class_id": None, "title": global_prompt_title}
            )
            response.raise_for_status()
            st.success("Global grading prompt created successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error creating global prompt: {str(e)}")

# =========================
# Navigation
# =========================

if st.button("Back to Professor View"):
    st.switch_page("pages/2_Professor_View.py") 