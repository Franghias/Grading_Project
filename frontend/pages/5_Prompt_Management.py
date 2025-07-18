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

API_URL = os.getenv('API_URL', 'http://localhost:8000').strip()

# =========================
# Page Configuration and Sidebar
# =========================

st.set_page_config(
    page_title="Prompt Management",
    page_icon="📝",
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
            /* New Earthy Palette */
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

        /* --- Expander Styling --- */
        .stExpander {
            background-color: var(--card-background-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(212, 163, 115, 0.05);
            margin-bottom: 1rem;
        }
        .stExpander header { 
            font-size: 1.1rem; 
            font-weight: 600;
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

        /* --- Input Styling --- */
        .stTextInput > div > div > input, .stTextArea > div > textarea {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            background-color: var(--card-background-color);
            color: var(--text-color);
        }
    </style>
""", unsafe_allow_html=True)


# =========================
# Sidebar Navigation (Original code)
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
# Page Header and Access Control (Original code)
# =========================
st.title("📝 Grading Prompt Management")

if 'user' not in st.session_state:
    st.switch_page("login.py")

if not st.session_state.user.get('is_professor'):
    st.error("This page is for professors only")
    st.stop()

# =========================
# API Helper Functions (Original code)
# =========================
def get_auth_header():
    return {"Authorization": f"Bearer {st.session_state.token}"}

# =========================
# Prompt Display and Management UI (Original code)
# =========================
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

st.subheader("Prompt History")
professor_prompts = []
global_prompts = []
try:
    user_id = st.session_state.user['id']
    response_prof = requests.get(f"{API_URL}/prompts/", params={"created_by": user_id, "class_id": None}, headers=get_auth_header())
    response_prof.raise_for_status()
    professor_prompts = response_prof.json()
    response_global = requests.get(f"{API_URL}/prompts/", params={"created_by": None, "class_id": None}, headers=get_auth_header())
    response_global.raise_for_status()
    global_prompts = response_global.json()
except Exception as e:
    st.error(f"Error fetching prompts: {str(e)}")

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
                            assign_response = requests.post(f"{API_URL}/classes/{selected_class_id}/prompt", params={"prompt_id": prompt['id']}, headers=get_auth_header())
                            if assign_response.status_code == 200:
                                st.success("Prompt assigned to class!")
                                st.rerun()
                            else:
                                st.error(f"Failed to assign prompt: {assign_response.text}")
                        except Exception as e:
                            st.error(f"Error assigning prompt: {str(e)}")
else:
    st.info("No unassigned professor prompts available.")

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
# Edit and Save New Prompt UI (Original code)
# =========================
st.subheader("Edit and Save New Prompt")
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

new_prompt_title = st.text_input("Prompt Title:", value=edit_prompt_title, key="edit_new_prompt_title", help="Enter a descriptive title for your grading prompt.")
new_prompt = st.text_area("Enter your grading prompt here:", value=edit_prompt_body, key="edit_new_prompt_body", height=400, help="You can use {code} as a placeholder for the student's code.")

required_phrase = '"grade":'
if st.button("Save Prompt"):
    if not new_prompt_title.strip() or not new_prompt.strip() or required_phrase not in new_prompt:
        if not new_prompt_title.strip(): st.warning("Please enter a title for your prompt.")
        if not new_prompt.strip(): st.warning("Please enter your grading prompt.")
        if required_phrase not in new_prompt: st.warning("Your prompt must instruct the AI to return a JSON object with a top-level 'grade' field.")
    else:
        try:
            if edit_prompt_id is not None:
                response = requests.put(f"{API_URL}/prompts/{edit_prompt_id}", headers={**get_auth_header(), "Content-Type": "application/json"}, json={"title": new_prompt_title, "prompt": new_prompt, "class_id": None})
                st.success("Prompt updated successfully!")
            else:
                response = requests.post(f"{API_URL}/prompts/", headers={**get_auth_header(), "Content-Type": "application/json"}, json={"prompt": new_prompt, "class_id": None, "title": new_prompt_title})
                st.success("New grading prompt saved successfully!")
            response.raise_for_status()
            st.rerun()
        except Exception as e:
            st.error(f"Error saving prompt: {str(e)}")

st.subheader("Create and Push to Global Prompt")
global_prompt_title = st.text_input("Global Prompt Title:", value="", help="Enter a descriptive title for your global grading prompt.")
global_prompt = st.text_area("Enter your global grading prompt here:", value="", height=400, help="You can use {code} as a placeholder for the student's code.")

if st.button("Push to Global Prompt"):
    if not global_prompt_title.strip() or not global_prompt.strip() or required_phrase not in global_prompt:
        if not global_prompt_title.strip(): st.warning("Please enter a title for your global prompt.")
        if not global_prompt.strip(): st.warning("Please enter your global grading prompt.")
        if required_phrase not in global_prompt: st.warning("Your prompt must instruct the AI to return a JSON object with a top-level 'grade' field.")
    else:
        try:
            response = requests.post(f"{API_URL}/prompts/", headers={**get_auth_header(), "Content-Type": "application/json"}, json={"prompt": global_prompt, "class_id": None, "title": global_prompt_title})
            response.raise_for_status()
            st.success("Global grading prompt created successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error creating global prompt: {str(e)}")

# =========================
# Navigation (Original code)
# =========================
if st.button("Back to Professor View"):
    st.switch_page("pages/2_Professor_View.py")