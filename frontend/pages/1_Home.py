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
from pathlib import Path

# =========================
# Page Configuration and Sidebar
# =========================

st.set_page_config(
    page_title="Home Page",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide default sidebar and show custom sidebar for students if applicable
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

if 'user' in st.session_state and not st.session_state.user.get('is_professor'):
    with st.sidebar:
        st.title("🎓 Student Menu")
        st.page_link('pages/3_Student_View.py', label='Student View', icon='👨‍🎓')
        st.page_link('pages/1_Home.py', label='Home', icon='🏠')
        st.page_link('pages/4_Grades_View.py', label='Grades View', icon='📊')
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("login.py")

# =========================
# Environment and API Setup
# =========================
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
API_URL = os.getenv('API_URL', 'http://localhost:8000').strip()

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

        /* --- Theme & Base Styles --- */
        :root {
            --primary-color: #4a9a9b;
            --primary-hover-color: #3d8283;
            --background-color: #f0f2f6;
            --card-background-color: #ffffff;
            --text-color: #262730;
            --subtle-text-color: #5E5E5E;
            --border-color: #e0e0e0;
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
        .page-header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            text-align: center;
        }
        .page-header p {
            font-size: 1.1rem;
            color: var(--subtle-text-color);
            text-align: center;
        }

        /* --- Card & Expander Styling --- */
        .stExpander, .styled-card {
            background-color: var(--card-background-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.5rem;
            transition: all 0.3s ease-in-out;
        }
        .stExpander:hover, .styled-card:hover {
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
            transform: translateY(-3px);
        }
        .stExpander header { font-size: 1.25rem; font-weight: 600; }
        .styled-card { padding: 1.5rem; }

        /* --- Button Styling --- */
        .stButton > button {
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
            background-color: var(--primary-color);
            color: white;
            border: none;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            background-color: var(--primary-hover-color);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        /* --- Grade & Feedback Boxes --- */
        .grade-box {
            padding: 1.5rem; border-radius: 10px; text-align: center;
            margin-bottom: 1rem; border: 1px solid transparent;
        }
        .grade-box h3 { margin: 0 0 0.5rem 0; font-size: 1.1rem; }
        .grade-box .grade-value { margin: 0; font-size: 2.5rem; font-weight: 700; }
        .ai-grade-box { background-color: #eef7f7; color: #3d8283; border-color: #a7d0d1; }
        .final-grade-box { background-color: #f3eef7; color: #6a4a9b; border-color: #c4a7d1; }
        .pending-box { background-color: #f7f3e3; color: #926f0e; border-color: #e3d2a7; }
        .feedback-box {
             background-color: #f8fafc; padding: 1.2rem;
             border-radius: 8px; border: 1px solid var(--border-color);
        }
    </style>
""", unsafe_allow_html=True)


# =========================
# Authentication and Navigation
# =========================
if 'token' not in st.session_state:
    st.warning("Please login first.")
    st.switch_page("login.py")
    st.stop()

# =========================
# Data Fetching and Caching
# =========================
@st.cache_data(ttl=60)
def get_all_classes(token):
    try:
        response = requests.get(f"{API_URL}/classes/", headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []

@st.cache_data(ttl=30)
def get_user_submissions_for_class_cached(class_id, token):
    try:
        response = requests.get(f"{API_URL}/submissions/", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        response.raise_for_status()
        return [s for s in response.json() if s['class_id'] == class_id]
    except requests.RequestException:
        return []

# Fetch all classes to find enrolled ones for the new dropdown
all_classes = get_all_classes(st.session_state.token)
is_prof = st.session_state.user.get('is_professor', False)
user_id = st.session_state.user.get('id') # Corrected to 'id' to match user object

if is_prof:
    enrolled_classes = [c for c in all_classes if user_id in [p.get('id') for p in c.get('professors', [])]]
else:
    enrolled_classes = [c for c in all_classes if any(s.get('id') == user_id for s in c.get('students', []))]


# =========================
# Page Header & Class Selection
# =========================
st.markdown(f"""
<div class="page-header">
    <h1>Home Dashboard</h1>
    <p>Welcome, {st.session_state.user["name"]}!</p>
</div>
""", unsafe_allow_html=True)

if not enrolled_classes:
    st.warning("You are not enrolled in or teaching any classes yet.")
    st.stop()

# Create a mapping for the selectbox for better readability
class_dict = {c['id']: c for c in enrolled_classes}
class_options = {c['id']: f"{c['name']} ({c['code']})" for c in enrolled_classes}
options_with_placeholder = {None: "--- Please select a class to view details ---", **class_options}

# Get the currently selected ID from session state, if it exists
selected_id = st.session_state.get('selected_class_id')

# Display the selectbox. Its state is inherently managed by Streamlit across reruns.
chosen_id = st.selectbox(
    "**Your Classes**",
    options=list(options_with_placeholder.keys()),
    format_func=lambda id: options_with_placeholder[id],
    index=list(options_with_placeholder.keys()).index(selected_id) if selected_id in options_with_placeholder else 0
)

# Update session state if the selection has changed
if chosen_id != selected_id:
    st.session_state.selected_class_id = chosen_id
    if chosen_id:
        st.session_state.selected_class = class_dict[chosen_id]
        get_user_submissions_for_class_cached.clear()
    else:
        # User selected the placeholder, so clear the selected class
        if 'selected_class' in st.session_state:
            del st.session_state['selected_class']
    st.rerun()

# =========================
# Main Dashboard UI (Conditional)
# =========================
if 'selected_class' in st.session_state and st.session_state.selected_class:
    selected_class = st.session_state.selected_class

    st.markdown("---")

    # --- Class Information Card ---
    st.markdown('<div class="styled-card">', unsafe_allow_html=True)
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"### 📚 Class Information: {selected_class['name']}")
    with col2:
        if st.button("🔄 Refresh Data", help="Refresh all class data and submissions"):
            get_user_submissions_for_class_cached.clear()
            st.rerun()

    st.markdown(f"**Description:** {selected_class.get('description', 'N/A')}")
    st.markdown(f"**Prerequisites:** {selected_class.get('prerequisites', 'None')}")
    st.markdown(f"**Learning Objective:** {selected_class.get('learning_objectives', 'None')}")
    for professor in selected_class.get('professors', []):
        st.markdown(f"- **Professor:** {professor['name']} ({professor['email']})")
    st.markdown('</div>', unsafe_allow_html=True)


    # --- Data Fetching for Selected Class ---
    submissions = get_user_submissions_for_class_cached(selected_class['id'], st.session_state.token)
    assignment_submissions = {}
    for sub in submissions:
        assignment_id = sub.get('assignment_id')
        if assignment_id not in assignment_submissions:
            assignment_submissions[assignment_id] = []
        assignment_submissions[assignment_id].append(sub)

    # --- Assignments Section ---
    st.markdown("### Assignments")
    if selected_class.get('assignments'):
        for assignment in selected_class['assignments']:
            with st.expander(f"📝 {assignment['name']}", expanded=False):
                st.markdown(f"**Description:** {assignment.get('description', 'No description available')}")
                st.markdown("---")
                
                # --- Student Submission View ---
                if not is_prof:
                    st.markdown("#### Your Submissions")
                    assignment_id = assignment['id']
                    if assignment_id in assignment_submissions:
                        for i, submission in enumerate(assignment_submissions[assignment_id], 1):
                            st.markdown(f"**Submission {i} (Submitted: {submission['created_at'][:10]})**")
                            g_col1, g_col2 = st.columns(2)
                            with g_col1:
                                st.markdown(f'<div class="grade-box ai-grade-box"><h3>🤖 AI Grade</h3><p class="grade-value">{submission.get("ai_grade", "...")}</p></div>', unsafe_allow_html=True)
                            with g_col2:
                                st.markdown(f'<div class="grade-box final-grade-box"><h3>📊 Final Grade</h3><p class="grade-value">{submission.get("professor_grade", "...")}</p></div>', unsafe_allow_html=True)

                            f_col1, f_col2 = st.columns(2)
                            with f_col1:
                                st.markdown("##### AI Feedback")
                                st.markdown(f'<div class="feedback-box">{submission.get("ai_feedback", "N/A")}</div>', unsafe_allow_html=True)
                            with f_col2:
                                st.markdown("##### Professor Feedback")
                                st.markdown(f'<div class="feedback-box">{submission.get("professor_feedback", "N/A")}</div>', unsafe_allow_html=True)
                            
                            st.code(submission['code'], language='python')
                            st.markdown("---")
                    else:
                        st.info("No submissions yet for this assignment.")

                    # --- Submission Form ---
                    st.markdown("#### Submit New Code")
                    submission_method = st.radio("Submission method:", ["Type Code", "Upload File"], horizontal=True, key=f"method_{assignment['id']}")
                    with st.form(f"submission_form_{assignment['id']}"):
                        code_input = st.text_area("Enter code:", height=250, key=f"code_{assignment['id']}") if submission_method == "Type Code" else None
                        file_input = st.file_uploader("Upload a .py file:", type=['py'], key=f"file_{assignment['id']}") if submission_method == "Upload File" else None
                        if st.form_submit_button("Submit Code"):
                            if (code_input and code_input.strip()) or file_input:
                                try:
                                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                                    data = {"class_id": str(selected_class['id']), "assignment_id": str(assignment['id'])}
                                    files = {"file": file_input.getvalue()} if file_input else None
                                    if not files: data["code"] = code_input
                                    
                                    response = requests.post(f"{API_URL}/submissions/", headers=headers, data=data, files=files)
                                    response.raise_for_status()
                                    st.success("Submission successful!")
                                    get_user_submissions_for_class_cached.clear()
                                    st.rerun()
                                except requests.RequestException as e:
                                    st.error(f"Submission failed: {e.response.text if e.response else e}")
                            else:
                                st.error("Please provide code or upload a file.")
                else: # --- Professor View ---
                    st.info("To manage submissions for this assignment, please go to the Professor View.")

    else:
        st.info("No assignments available for this class yet.")

    # --- Navigation buttons ---
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Back to All Classes"):
            # Clear selection and go back to the main view
            if 'selected_class' in st.session_state: del st.session_state['selected_class']
            if 'selected_class_id' in st.session_state: del st.session_state['selected_class_id']
            if is_prof:
                st.switch_page("pages/2_Professor_View.py")
            else:
                st.switch_page("pages/3_Student_View.py")
    with col2:
        if st.button("View My Grades"):
            st.switch_page("pages/4_Grades_View.py")
    with col3:
        if st.button("Logout"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.switch_page("login.py")
else:
    st.info("Please select a class from the dropdown menu above to begin.")