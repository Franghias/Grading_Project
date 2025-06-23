# =========================
# Grades View Page
# =========================
# This file implements the grades viewing page for students and professors.
# Students can view their submissions and grades for each class and assignment.
# Professors can view and grade student submissions, and provide feedback.

import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =========================
# Environment and API Setup
# =========================

# Load environment variables
load_dotenv()
API_URL = os.getenv('API_URL', 'http://localhost:8000')

# =========================
# Page Configuration and Sidebar
# =========================

# Page configuration
st.set_page_config(
    page_title="Grades View",
    page_icon="📊",
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

        /* Grade card styling */
        .grade-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .grade-card h3 {
            margin: 0 0 0.5rem 0;
            font-size: 1.25rem;
            font-weight: 600;
        }

        .grade-card .grade {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }

        .grade-card .date {
            font-size: 0.9rem;
            opacity: 0.9;
        }

        .grade-card .class-name {
            font-size: 1rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# Access Control and Header
# =========================

# Check if user is logged in
if 'user' not in st.session_state:
    st.switch_page("login.py")

# Check if user is a student (main view is for students)
if st.session_state.user.get('is_professor'):
    st.error("This page is for students only")
    st.stop()

# Header
st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown('<h1>📊 My Grades</h1>', unsafe_allow_html=True)
st.markdown(f'<p>Welcome, {st.session_state.user["name"]}!</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.info('Note: The AI grades your code using the assignment description as context for more accurate feedback.')

# =========================
# Data Fetching Functions
# =========================

def get_user_submissions():
    """
    Fetch all submissions for the current user from the backend API.
    Returns a list of submission dictionaries.
    """
    try:
        response = requests.get(
            f"{API_URL}/submissions/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching submissions: {str(e)}")
        return []

def get_all_classes():
    """
    Fetch all classes from the backend API.
    Returns a list of class dictionaries.
    """
    try:
        response = requests.get(
            f"{API_URL}/classes/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching classes: {str(e)}")
        return []

# =========================
# Data Preparation
# =========================

# Get all submissions and classes for the current user
submissions = get_user_submissions()
all_classes = get_all_classes()

# Filter to only classes the student is enrolled in
student_classes = [c for c in all_classes if any(s['user_id'] == st.session_state.user['user_id'] for s in c.get('students', []))]

if not student_classes:
    st.info("You are not enrolled in any classes.")
    st.stop()

# =========================
# Add a toggle at the top to switch between Grades and My Statistics
# =========================
view_option = st.radio(
    "Select View",
    ("Assignments and Submissions", "My Statistics"),
    horizontal=True,
    index=0
)

if view_option == "Assignments and Submissions":
    # =========================
    # Student View: Class and Submission Display
    # =========================
    selected_class = st.selectbox(
        "Select a class to view your submissions:",
        options=student_classes,
        format_func=lambda c: f"{c['name']} ({c['code']})"
    )
    def show_submissions_for_class(selected_class, submissions):
        assignments = selected_class.get('assignments', [])
        assignment_id_to_info = {a['id']: a for a in assignments}
        class_submissions = [s for s in submissions if s['assignment_id'] in assignment_id_to_info]
        if not class_submissions:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### No submissions for this class yet.")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        for assignment in assignments:
            st.markdown(f"#### {assignment['name']}")
            assignment_subs = [s for s in class_submissions if s['assignment_id'] == assignment['id']]
            if not assignment_subs:
                st.info("No submissions for this assignment yet.")
                continue
            assignment_subs_sorted = sorted(assignment_subs, key=lambda x: x['created_at'])
            for i, sub in enumerate(assignment_subs_sorted, 1):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Submission {i}**")
                    prof_grade = sub.get('professor_grade')
                    if prof_grade is not None:
                        st.markdown(f"**Final Grade:** {prof_grade}")
                    else:
                        st.markdown("**Final Grade:** wait for professor feedback")
                    submitted_at = sub.get('created_at', '')
                    st.markdown(f"**Submitted at:** {submitted_at[:19].replace('T', ' ')}")
                with col2:
                    st.markdown(f"**Professor Feedback:** {sub.get('professor_feedback', 'N/A')}")
                st.markdown("**Submitted Code:**")
                st.code(sub.get('code', ''), language="python")
                st.markdown("---")
    default_view = show_submissions_for_class(selected_class, submissions)
else:
    # =========================
    # Student Statistics Section (moved from Student View)
    # =========================
    if not submissions:
        st.info("No submissions found yet.")
    else:
        data = []
        for sub in submissions:
            # Only use final_grade or professor_grade for statistics
            grade = sub.get('final_grade') or sub.get('professor_grade')
            if grade is not None:
                data.append({
                    'assignment_id': sub['assignment_id'],
                    'class_id': sub['class_id'],
                    'grade': grade,
                    'professor_grade': sub.get('professor_grade'),
                    'final_grade': sub.get('final_grade'),
                    'created_at': sub['created_at'],
                    'assignment_name': sub['assignment']['name'] if sub.get('assignment') else 'Unknown'
                })
        if not data:
            st.info("No graded submissions found yet.")
        else:
            df = pd.DataFrame(data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            def get_grade_letter(grade):
                if grade >= 90: return 'A'
                elif grade >= 80: return 'B'
                elif grade >= 70: return 'C'
                elif grade >= 60: return 'D'
                else: return 'F'
            df['grade_letter'] = df['grade'].apply(get_grade_letter)
            st.markdown("## 📊 My Statistics Overview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Grade", f"{df['grade'].mean():.1f}%")
            with col2:
                st.metric("Total Submissions", f"{len(df)}")
            with col3:
                st.metric("Assignments Attempted", f"{df['assignment_id'].nunique()}")
            tab1, tab2, tab3 = st.tabs(["📊 Grade Distribution", "📈 Assignment Analysis", "⏰ Time Trends"])
            with tab1:
                st.markdown("### 📊 Grade Distribution")
                col1, col2 = st.columns(2)
                with col1:
                    fig_hist = px.histogram(
                        df, x='grade', nbins=20,
                        title="Grade Distribution",
                        labels={'grade': 'Grade (%)', 'count': 'Number of Submissions'},
                        color_discrete_sequence=['#4a9a9b']
                    )
                    fig_hist.update_layout(
                        showlegend=False,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                with col2:
                    grade_counts = df['grade_letter'].value_counts()
                    fig_pie = px.pie(
                        values=grade_counts.values,
                        names=grade_counts.index,
                        title="Grade Letter Distribution",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_pie.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            with tab2:
                st.markdown("### 📈 Assignment Performance")
                assignment_stats = df.groupby('assignment_name').agg({
                    'grade': ['mean', 'std', 'count']
                }).round(2)
                assignment_stats.columns = ['Average Grade', 'Std Dev', 'Submissions']
                assignment_stats = assignment_stats.reset_index()
                fig_assignment = px.bar(
                    assignment_stats,
                    x='assignment_name',
                    y='Average Grade',
                    title="Average Grade by Assignment",
                    labels={'assignment_name': 'Assignment', 'Average Grade': 'Average Grade (%)'},
                    color='Average Grade',
                    color_continuous_scale='RdYlGn'
                )
                fig_assignment.update_layout(
                    xaxis_tickangle=-45,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_assignment, use_container_width=True)
                st.markdown("### 📋 Assignment Statistics")
                st.dataframe(assignment_stats, use_container_width=True)
            with tab3:
                st.markdown("### ⏰ Time-Based Trends")
                df['date'] = df['created_at'].dt.date
                daily_submissions = df.groupby('date').size().reset_index()
                daily_submissions.columns = ['Date', 'Submissions']
                fig_trend = px.line(
                    daily_submissions,
                    x='Date',
                    y='Submissions',
                    title="Daily Submission Trends",
                    markers=True
                )
                fig_trend.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_trend, use_container_width=True)
                grade_trends = df.groupby('date')['grade'].mean().reset_index()
                fig_grade_trend = px.line(
                    grade_trends,
                    x='date',
                    y='grade',
                    title="Average Grade Trends Over Time",
                    markers=True
                )
                fig_grade_trend.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_grade_trend, use_container_width=True)

# =========================
# Professor Grading Section (if professor)
# =========================

if st.session_state.user.get('is_professor'):
    # Re-create class_submissions for professor grading section
    class_submissions = defaultdict(list)
    for sub in submissions:
        class_submissions[sub['class_id']].append(sub)
    st.markdown('---')
    st.header('👨‍🏫 Professor Grading Section')
    # Select class and assignment
    all_classes = get_all_classes()
    class_options = [c for c in all_classes if c['id'] in class_submissions]
    selected_class = st.selectbox('Select Class', class_options, format_func=lambda c: f"{c['name']} ({c['code']})")
    assignment_options = selected_class['assignments']
    selected_assignment = st.selectbox('Select Assignment', assignment_options, format_func=lambda a: a['name'])
    # Fetch all submissions for this assignment
    try:
        response = requests.get(
            f"{API_URL}/classes/{selected_class['id']}/assignments/{selected_assignment['id']}/submissions",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        response.raise_for_status()
        grouped_submissions = response.json()
    except Exception as e:
        st.error(f"Error fetching submissions: {e}")
        grouped_submissions = []
    for user_data in grouped_submissions:
        with st.expander(f"{user_data['username']} ({user_data['user_id']})", expanded=False):
            user_subs = sorted(user_data['submissions'], key=lambda x: x['created_at'], reverse=True)
            for i, submission in enumerate(user_subs, 1):
                st.markdown(f"**Submission {i} - {submission['created_at'][:10]}**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if submission['professor_grade'] is not None:
                        prof_grade_color = "green" if submission['professor_grade'] >= 70 else "orange" if submission['professor_grade'] >= 50 else "red"
                        st.markdown(f"""
                            <div style="background-color: #f0f9ff; padding: 1rem; border-radius: 0.5rem; text-align: center; border: 1px solid #bae6fd;">
                                <h4 style="margin: 0 0 0.5rem 0; color: #0369a1;">👨‍🏫 Professor Grade</h4>
                                <h2 style="margin: 0; color: {prof_grade_color}; font-size: 1.5rem;">{submission['professor_grade']}</h2>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("**👨‍🏫 Professor Grade:** Not graded")
                with col2:
                    if submission['final_grade'] is not None:
                        final_grade_color = "green" if submission['final_grade'] >= 70 else "orange" if submission['final_grade'] >= 50 else "red"
                        st.markdown(f"""
                            <div style="background-color: #fef7ff; padding: 1rem; border-radius: 0.5rem; text-align: center; border: 2px solid #c084fc;">
                                <h4 style="margin: 0 0 0.5rem 0; color: #7c3aed;">📊 Final Grade</h4>
                                <h2 style="margin: 0; color: {final_grade_color}; font-size: 1.5rem;">{submission['final_grade']}</h2>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("**📊 Final Grade:** Not available")
                # Professor Grading Interface
                st.markdown("### 👨‍🏫 Set Professor Grade")
                with st.form(f"grade_form_{submission['id']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        professor_grade = st.number_input(
                            "Grade (0-100)",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(submission['professor_grade']) if submission['professor_grade'] is not None else 0.0,
                            step=0.1,
                            key=f"grade_{submission['id']}"
                        )
                    with col2:
                        professor_feedback = st.text_area(
                            "Feedback (optional)",
                            value=submission['professor_feedback'] if submission['professor_feedback'] else "",
                            height=150,
                            key=f"feedback_{submission['id']}"
                        )
                        submit_grade = st.form_submit_button("Set Grade")
                        if submit_grade:
                            try:
                                response = requests.post(
                                    f"{API_URL}/submissions/{submission['id']}/professor-grade",
                                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                                    json={
                                        "grade": professor_grade,
                                        "feedback": professor_feedback if professor_feedback.strip() else None
                                    }
                                )
                                response.raise_for_status()
                                st.success("Grade set successfully!")
                                st.rerun()
                            except requests.RequestException as e:
                                st.error(f"Error setting grade: {str(e)}")
                # Feedback sections
                col1, col2 = st.columns(2)
                with col1:
                    if submission['professor_feedback']:
                        st.markdown("### 👨‍🏫 Professor Feedback")
                        # Convert newlines to HTML br tags to preserve formatting
                        formatted_feedback = submission['professor_feedback'].replace('\n', '<br>')
                        st.markdown(f"<div style='background-color: #f0fdf4; padding: 1rem; border-radius: 0.5rem; border: 1px solid #bbf7d0;'>{formatted_feedback}</div>", unsafe_allow_html=True)
                st.markdown("### Submitted Code")
                st.code(submission['code'], language="python")
                st.markdown("---")

# =========================
# Navigation Buttons
# =========================

st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Back to Home"):
        if 'selected_class' in st.session_state:
            st.switch_page("pages/1_Home.py")
        else:
            st.switch_page("pages/3_Student_View.py")

with col2:
    if st.button("Back to Student View"):
        st.switch_page("pages/3_Student_View.py")

with col3:
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("login.py")

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