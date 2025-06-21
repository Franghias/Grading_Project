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

# Load environment variables
load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")

# =========================
# Page Configuration and Sidebar
# =========================

st.set_page_config(
    page_title="Assignment Management",
    page_icon="✍️",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .assignment-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            background-color: #f9f9f9;
        }
        .assignment-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .assignment-actions {
            display: flex;
            gap: 8px;
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
    if st.button("🔄 Refresh", type="secondary", help="Refresh assignments list"):
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
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.subheader(f"📝 {assignment['name']}")
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
                            if st.button(f"🗑️ Delete", key=f"delete_{assignment['id']}", type="secondary"):
                                st.session_state.deleting_assignment = assignment
                                st.rerun()
                        
                        st.markdown("---")
                
                # Edit Assignment Modal
                if 'editing_assignment' in st.session_state:
                    assignment = st.session_state.editing_assignment
                    st.subheader(f"✏️ Edit Assignment: {assignment['name']}")
                    
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
                                            headers={"Authorization": f"Bearer {st.session_state.token}"},
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
                    st.subheader(f"🗑️ Delete Assignment: {assignment['name']}")
                    st.warning(f"Are you sure you want to delete '{assignment['name']}'? This action cannot be undone.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Yes, Delete", type="primary"):
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
        
        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button("🚀 Create Assignment", type="primary")
        
        with col2:
            if st.form_submit_button("🗑️ Clear Form"):
                st.rerun()

        if submitted:
            if not assignment_name.strip():
                st.error("❌ Assignment name is required.")
            else:
                try:
                    response = requests.post(
                        f"{API_URL}/classes/{selected_class_id}/assignments/",
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                        json={
                            "name": assignment_name.strip(), 
                            "description": assignment_description.strip(), 
                            "class_id": selected_class_id
                        }
                    )
                    response.raise_for_status()
                    st.success("✅ Assignment created successfully!")
                    st.balloons()
                    st.rerun()  # Refresh the page to show the new assignment
                except requests.RequestException as e:
                    st.error(f"❌ Error creating assignment: {e}")

# =========================
# Footer Information
# =========================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    💡 <strong>Tips:</strong> 
    • Use descriptive assignment names to help students identify tasks easily<br>
    • Provide clear descriptions with requirements and expectations<br>
    • You can edit assignments anytime, but deleting requires no existing submissions
</div>
""", unsafe_allow_html=True) 