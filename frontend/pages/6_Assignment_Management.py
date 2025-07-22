# =========================
# Assignment Management Page
# =========================
# This file implements the assignment management interface for professors.
# Professors can create, view, edit, and delete assignments for their classes.
# Includes forms for creating and editing assignments, and API calls for data management.

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

API_URL = os.getenv("API_URL", "http://localhost:8000").strip()

# =========================
# Page Configuration and Sidebar
# =========================

st.set_page_config(
    page_title="Assignment Management",
    page_icon="✍️",
    layout="wide"
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
        h2, h3 { /* This targets st.subheader and st.header */
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 0.5rem;
            color: var(--text-color);
        }

        /* --- Custom Card Styling for Assignments --- */
        .st-emotion-cache-16txtl3 { /* This targets st.container */
            background-color: var(--card-background-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(212, 163, 115, 0.05);
            padding: 1rem 1.5rem;
            margin-bottom: 1rem;
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
# Sidebar Navigation
# =========================

if 'user' not in st.session_state:
    st.switch_page("login.py")

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

# Header
st.title("📚 Assignment Management")
st.write("Create, view, edit, and delete assignments for your classes.")

# Check if user is logged in and is a professor
if 'user' not in st.session_state or not st.session_state.user.get('is_professor'):
    st.error("You must be logged in as a professor to access this page.")
    st.stop()

# =========================
# Fetch Professor's Classes
# =========================

try:
    response = requests.get(
        f"{API_URL}/classes/",
        headers={"Authorization": f"Bearer {st.session_state.token}"}
    )
    response.raise_for_status()
    classes = response.json()
    if not classes:
        st.warning("You are not teaching any classes. Please create a class first.")
        st.stop()
except requests.RequestException as e:
    st.error(f"Error fetching classes: {e}")
    st.stop()

# =========================
# Class Selection Dropdown
# =========================

col1, col2 = st.columns([3, 1])
with col1:
    class_options = {c['id']: f"{c['name']} ({c['code']})" for c in classes}
    selected_class_id = st.selectbox("Select a Class", options=list(class_options.keys()), format_func=lambda x: class_options[x])
with col2:
    if st.button("🔄 Refresh", help="Refresh assignments list"):
        st.rerun()

st.markdown("---")

# =========================
# Main Content Tabs
# =========================

tab1, tab2 = st.tabs(["📋 View Assignments", "➕ Create New Assignment"])

with tab1:
    # =========================
    # View and Manage Existing Assignments
    # =========================
    
    st.header("📋 Current Assignments")
    
    # Fetch assignments for the selected class
    if selected_class_id:
        try:
            response = requests.get(
                f"{API_URL}/classes/{selected_class_id}/assignments/",
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            response.raise_for_status()
            assignments = response.json()

            if not assignments:
                st.info("No assignments found for this class. Create your first assignment in the 'Create New Assignment' tab.")
            else:
                st.write(f"Found {len(assignments)} assignment(s) for this class:")
                
                for assignment in assignments:
                    with st.container():
                        col1, col2, col3 = st.columns([4, 1, 1])
                        
                        with col1:
                            st.subheader(f"{assignment['name']}")
                            if assignment.get('description'):
                                st.write(assignment['description'])
                            else:
                                st.write("*No description provided*")
                            st.caption(f"Created: {assignment['created_at'][:10]}")
                        
                        with col2:
                            if st.button(f"✏️ Edit", key=f"edit_{assignment['id']}"):
                                st.session_state.editing_assignment = assignment
                                st.rerun()
                        
                        with col3:
                            if st.button(f"🗑️ Delete", key=f"delete_{assignment['id']}"):
                                st.session_state.deleting_assignment = assignment
                                st.rerun()
                
                # Edit Assignment Modal
                if 'editing_assignment' in st.session_state:
                    assignment = st.session_state.editing_assignment
                    st.header(f"✏️ Edit Assignment: {assignment['name']}")
                    
                    with st.form(f"edit_form_{assignment['id']}"):
                        edit_name = st.text_input("Assignment Name", value=assignment['name'], key=f"edit_name_{assignment['id']}")
                        edit_description = st.text_area("Assignment Description", value=assignment.get('description', ''), key=f"edit_desc_{assignment['id']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Save Changes"):
                                if not edit_name.strip():
                                    st.error("Assignment name is required.")
                                else:
                                    try:
                                        response = requests.put(
                                            f"{API_URL}/assignments/{assignment['id']}",
                                            headers={"Authorization": f"Bearer {st.session_state.token}", "Content-Type": "application/json"},
                                            json={"name": edit_name.strip(), "description": edit_description.strip()}
                                        )
                                        response.raise_for_status()
                                        st.success("✅ Assignment updated successfully!")
                                        del st.session_state.editing_assignment
                                        st.rerun()
                                    except requests.RequestException as e:
                                        st.error(f"❌ Error updating assignment: {e}")
                        
                        with col2:
                            if st.form_submit_button("❌ Cancel"):
                                del st.session_state.editing_assignment
                                st.rerun()
                
                # Delete Assignment Confirmation
                if 'deleting_assignment' in st.session_state:
                    assignment = st.session_state.deleting_assignment
                    st.header(f"🗑️ Delete Assignment: {assignment['name']}")
                    st.warning(f"Are you sure you want to delete '{assignment['name']}'? This action cannot be undone.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Yes, Delete"):
                            try:
                                response = requests.delete(
                                    f"{API_URL}/assignments/{assignment['id']}",
                                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                                )
                                response.raise_for_status()
                                st.success("✅ Assignment deleted successfully!")
                                del st.session_state.deleting_assignment
                                st.rerun()
                            except requests.RequestException as e:
                                if response.status_code == 400:
                                    st.error(f"❌ Cannot delete assignment: {response.json().get('detail', 'Unknown error')}")
                                else:
                                    st.error(f"❌ Error deleting assignment: {e}")
                    
                    with col2:
                        if st.button("❌ Cancel"):
                            del st.session_state.deleting_assignment
                            st.rerun()

        except requests.RequestException as e:
            st.error(f"Error fetching assignments: {e}")

with tab2:
    # =========================
    # Create New Assignment Form
    # =========================
    
    st.header("➕ Create New Assignment")
    
    with st.form("new_assignment_form", clear_on_submit=True):
        assignment_name = st.text_input("Assignment Name", placeholder="e.g., Assignment 1: Introduction to Python")
        assignment_description = st.text_area(
            "Assignment Description", 
            placeholder="Describe what students need to do for this assignment...",
            height=150
        )
        
        submitted = st.form_submit_button("🚀 Create Assignment")
        
        if submitted:
            if not assignment_name.strip():
                st.error("❌ Assignment name is required.")
            else:
                try:
                    response = requests.post(
                        f"{API_URL}/classes/{selected_class_id}/assignments/",
                        headers={"Authorization": f"Bearer {st.session_state.token}", "Content-Type": "application/json"},
                        json={
                            "name": assignment_name.strip(), 
                            "description": assignment_description.strip(), 
                            "class_id": selected_class_id
                        }
                    )
                    response.raise_for_status()
                    st.success("✅ Assignment created successfully!")
                    st.balloons()
                except requests.RequestException as e:
                    st.error(f"❌ Error creating assignment: {e}")

# =========================
# Footer Information
# =========================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: var(--subtle-text-color); font-size: 0.8em;'>
    💡 <strong>Tips:</strong> 
    • Use descriptive assignment names to help students identify tasks easily<br>
    • Provide clear descriptions with requirements and expectations<br>
    • You can edit assignments anytime, but deleting requires no existing submissions
</div>
""", unsafe_allow_html=True)