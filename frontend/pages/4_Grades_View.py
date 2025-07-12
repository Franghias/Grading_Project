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
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from pathlib import Path

# =========================
# Environment and API Setup
# =========================
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
API_URL = os.getenv('API_URL', 'http://localhost:8000').strip()

# =========================
# Page Configuration
# =========================
st.set_page_config(
    page_title="Grades View",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Custom CSS Styling
# =========================
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* --- HIDE DEFAULT STREAMLIT SIDEBAR --- */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
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
        }
        .main .block-container {
            padding: 2rem;
            animation: fadeIn 0.5s ease-in-out forwards;
        }
        .page-header h1 {
            font-size: 2.5rem; font-weight: 700; color: var(--primary-color); text-align: center;
        }
        .page-header p {
            font-size: 1.1rem; color: var(--subtle-text-color); text-align: center;
        }
        .stButton > button {
            border-radius: 8px; padding: 0.6rem 1.2rem; font-weight: 600;
            transition: all 0.2s ease-in-out;
            background-color: var(--primary-color); color: white; border: none;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            background-color: var(--primary-hover-color);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)


# =========================
# Data Fetching Functions
# =========================
from utils.async_helpers import make_authenticated_request, refresh_token_if_needed

@st.cache_data(ttl=30)
def get_submissions(user_id=None, class_id=None):
    try:
        # Use the new authenticated request function with automatic token refresh
        if class_id:
            endpoint = f"classes/{class_id}/submissions"
        else:
            endpoint = "submissions/"

        submissions = make_authenticated_request('GET', endpoint)
        if submissions is None:
            return []

        # Filter by user_id if provided
        if user_id:
            return [s for s in submissions if s.get('user_id') == user_id]
        return submissions
    except Exception:
        return []

@st.cache_data(ttl=60)
def get_all_classes():
    try:
        classes = make_authenticated_request('GET', 'classes/')
        return classes if classes is not None else []
    except Exception:
        return []

# =========================
# Access Control
# =========================
if 'user' not in st.session_state:
    st.switch_page("login.py")

# =========================
# Main Logic
# =========================
all_classes = get_all_classes()

# --- PROFESSOR VIEW ---
if st.session_state.user.get('is_professor'):
    st.markdown('<div class="page-header"><h1>Professor Analytics</h1></div>', unsafe_allow_html=True)
    professor_classes = [c for c in all_classes if st.session_state.user['user_id'] in [p['user_id'] for p in c.get('professors', [])]]

    if not professor_classes:
        st.info("You are not assigned to any classes.")
        st.stop()

    selected_class = st.selectbox("Select a class to view analytics:", options=professor_classes, format_func=lambda c: f"{c['name']} ({c['code']})")

    if selected_class:
        submissions = get_submissions(class_id=selected_class['id'])
        if not submissions:
            st.info("No submissions found for this class yet.")
        else:
            processed_data = [{'user_name': s.get('user', {}).get('name', 'Unknown'),'professor_grade': s.get('professor_grade'),'ai_grade': s.get('ai_grade')} for s in submissions]
            df = pd.DataFrame(processed_data)
            df_graded = df.dropna(subset=['professor_grade']).copy()

            tab1, tab2, tab3 = st.tabs(["📊 Student Performance", "🤖 AI Grade Analysis", "📈 Class Statistics"])

            with tab1:
                student_perf = df_graded.groupby('user_name')['professor_grade'].mean().reset_index()
                if student_perf.empty:
                    st.info("No graded submissions to show student performance.")
                else:
                    fig = px.bar(student_perf, x='user_name', y='professor_grade', title='Average Grade per Student', color='professor_grade', color_continuous_scale='Teal')
                    fig.update_layout(xaxis_title="Student", yaxis_title="Average Grade", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)

            with tab2:
                df_both_grades = df.dropna(subset=['professor_grade', 'ai_grade']).copy()
                if df_both_grades.empty:
                    st.info("No submissions with both AI and Professor grades to compare.")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        fig_scatter = px.scatter(df_both_grades, x='ai_grade', y='professor_grade', title='AI vs. Professor Grade Correlation', trendline="ols", trendline_color_override="#d6336c")
                        fig_scatter.update_layout(xaxis_title="AI Grade", yaxis_title="Professor Final Grade", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_scatter, use_container_width=True)
                    with col2:
                        fig_hist = go.Figure()
                        fig_hist.add_trace(go.Histogram(x=df_both_grades['ai_grade'], name='AI Grades', marker_color='#4a9a9b', opacity=0.75))
                        fig_hist.add_trace(go.Histogram(x=df_both_grades['professor_grade'], name='Professor Grades', marker_color='#3d8283', opacity=0.75))
                        fig_hist.update_layout(barmode='overlay', title_text='AI vs. Professor Grade Distribution', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        fig_hist.update_traces(opacity=0.7)
                        st.plotly_chart(fig_hist, use_container_width=True)

            with tab3:
                 if df_graded.empty:
                    st.info("No graded submissions for statistical analysis.")
                 else:
                    st.markdown("#### Class-Wide Grade Statistics")
                    mean_grade = df_graded['professor_grade'].mean()
                    median_grade = df_graded['professor_grade'].median()
                    mode_grade = df_graded['professor_grade'].mode()
                    std_dev = df_graded['professor_grade'].std()

                    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
                    s_col1.metric("Mean Grade", f"{mean_grade:.2f}")
                    s_col2.metric("Median Grade", f"{median_grade:.2f}")
                    s_col3.metric("Mode Grade", f"{mode_grade[0] if not mode_grade.empty else 'N/A'}")
                    s_col4.metric("Std. Deviation", f"{std_dev:.2f}")

# --- STUDENT VIEW ---
else:
    st.markdown(f'<div class="page-header"><h1>My Grades</h1><p>Welcome, {st.session_state.user["name"]}!</p></div>', unsafe_allow_html=True)
    student_classes = [c for c in all_classes if any(s.get('user_id') == st.session_state.user['user_id'] for s in c.get('students', []))]
    if not student_classes:
        st.info("You are not enrolled in any classes yet.")
        st.stop()

    view_option = st.radio("Select View:", ("Assignments and Submissions", "My Statistics"), horizontal=True, index=0)

    if view_option == "Assignments and Submissions":
        selected_class = st.selectbox("Select a class:", options=student_classes, format_func=lambda c: f"{c['name']} ({c['code']})")
        if selected_class:
            submissions = get_submissions(user_id=st.session_state.user['user_id'], class_id=selected_class['id'])
            if not submissions:
                st.info("No submissions found for this class.")
            else:
                for assignment in selected_class.get('assignments', []):
                    assignment_subs = [s for s in submissions if s.get('assignment_id') == assignment.get('id')]
                    if assignment_subs:
                        with st.expander(f"Submissions for: {assignment['name']}", expanded=True):
                            for sub in assignment_subs:
                                # Use the same grade selection logic for consistency
                                final_grade = sub.get('final_grade')
                                professor_grade = sub.get('professor_grade')
                                
                                if final_grade is not None:
                                    grade = final_grade
                                elif professor_grade is not None:
                                    grade = professor_grade
                                else:
                                    grade = 'Pending'
                                
                                st.markdown(f"**Final Grade:** {grade}")
                                st.markdown(f"**Feedback:** *{sub.get('professor_feedback', 'N/A')}*")
                                st.code(sub.get('code', ''), language="python")
                                st.markdown("---")
                    else:
                        st.info(f"No submissions found for assignment: {assignment['name']}")
    else: # My Statistics View
        st.markdown("### My Statistics Overview")
        
        # Add class selection for statistics
        selected_class_stats = st.selectbox(
            "Select a class for detailed statistics:", 
            options=[None] + student_classes, 
            format_func=lambda c: "All Classes (Overall)" if c is None else f"{c['name']} ({c['code']})",
            index=0
        )
        
        if selected_class_stats is None:
            # Overall statistics across all classes
            all_my_submissions = get_submissions(user_id=st.session_state.user['user_id'])
        else:
            # Statistics for specific class
            all_my_submissions = get_submissions(user_id=st.session_state.user['user_id'], class_id=selected_class_stats['id'])
        
        # Fix: Use final_grade or professor_grade, but handle 0 correctly
        graded_subs = []
        for s in all_my_submissions:
            final_grade = s.get('final_grade')
            professor_grade = s.get('professor_grade')
            
            # Determine which grade to use (prioritize final_grade, then professor_grade)
            if final_grade is not None:
                grade = final_grade
            elif professor_grade is not None:
                grade = professor_grade
            else:
                grade = None
                
            if grade is not None:  # This correctly checks for None, allowing 0 grades
                graded_subs.append(s)

        if not graded_subs:
            if selected_class_stats is None:
                st.info("No graded submissions available to generate statistics.")
            else:
                st.info(f"No graded submissions available for {selected_class_stats['name']}.")
        else:
            student_data = []
            for s in graded_subs:
                # Use the same grade selection logic for consistency
                final_grade = s.get('final_grade')
                professor_grade = s.get('professor_grade')
                
                if final_grade is not None:
                    grade = final_grade
                elif professor_grade is not None:
                    grade = professor_grade
                else:
                    grade = None
                    
                student_data.append({
                    'assignment_name': s.get('assignment', {}).get('name', 'Unknown'), 
                    'grade': grade,
                    'class_name': next((c['name'] for c in student_classes if c['id'] == s.get('class_id')), 'Unknown')
                })
            df_student = pd.DataFrame(student_data)

            # --- Student Statistical Summary ---
            if selected_class_stats is None:
                st.markdown("#### Your Overall Performance (All Classes)")
            else:
                st.markdown(f"#### Your Performance in {selected_class_stats['name']}")
            
            mean_grade = df_student['grade'].mean()
            median_grade = df_student['grade'].median()
            mode_grade = df_student['grade'].mode()

            stat_col1, stat_col2, stat_col3 = st.columns(3)
            stat_col1.metric("Your Mean Grade", f"{mean_grade:.2f}")
            stat_col2.metric("Your Median Grade", f"{median_grade:.2f}")
            stat_col3.metric("Your Mode Grade", f"{mode_grade[0] if not mode_grade.empty else 'N/A'}")

            # --- Student Charts ---
            if selected_class_stats is None:
                tab1, tab2, tab3 = st.tabs(["📊 Grade Comparison", "📈 Grade Spread", "🎓 Performance by Class"])
            else:
                tab1, tab2 = st.tabs(["📊 Grade Comparison", "📈 Grade Spread"])
            
            with tab1:
                if selected_class_stats is None:
                    # Overall comparison across all classes
                    student_avg = df_student.groupby('assignment_name')['grade'].mean().reset_index()
                    student_avg['Type'] = 'Your Average'
                    class_avg_data = []
                    for s_class in student_classes:
                        class_submissions = get_submissions(class_id=s_class['id'])
                        # Use the same grade selection logic for class data
                        class_graded_data = []
                        for s in class_submissions:
                            final_grade = s.get('final_grade')
                            professor_grade = s.get('professor_grade')
                            
                            if final_grade is not None:
                                grade = final_grade
                            elif professor_grade is not None:
                                grade = professor_grade
                            else:
                                grade = None
                                
                            if grade is not None:
                                class_graded_data.append({
                                    'assignment_name': s.get('assignment', {}).get('name', 'Unknown'), 
                                    'grade': grade
                                })
                        
                        if class_graded_data:
                            class_avg_data.extend(class_graded_data)
                    
                    if class_avg_data:
                        df_class_all = pd.DataFrame(class_avg_data).groupby('assignment_name')['grade'].mean().reset_index()
                        df_class_all['Type'] = 'Class Average'
                        df_combined = pd.concat([student_avg, df_class_all])
                        df_combined.rename(columns={'grade': 'Grade'}, inplace=True)
                        fig = px.bar(
                            df_combined, x='assignment_name', y='Grade', color='Type', barmode='group',
                            title='Your Average Grade vs. Class Average (All Classes)',
                            color_discrete_map={'Your Average': '#4a9a9b', 'Class Average': '#aecdc2'}
                        )
                        fig.update_layout(xaxis_title="Assignment", yaxis_title="Average Grade", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    # Single class comparison
                    student_avg = df_student.groupby('assignment_name')['grade'].mean().reset_index()
                    student_avg['Type'] = 'Your Average'
                    class_submissions = get_submissions(class_id=selected_class_stats['id'])
                    class_graded_data = []
                    for s in class_submissions:
                        final_grade = s.get('final_grade')
                        professor_grade = s.get('professor_grade')
                        
                        if final_grade is not None:
                            grade = final_grade
                        elif professor_grade is not None:
                            grade = professor_grade
                        else:
                            grade = None
                            
                        if grade is not None:
                            class_graded_data.append({
                                'assignment_name': s.get('assignment', {}).get('name', 'Unknown'), 
                                'grade': grade
                            })
                    
                    if class_graded_data:
                        df_class_all = pd.DataFrame(class_graded_data).groupby('assignment_name')['grade'].mean().reset_index()
                        df_class_all['Type'] = 'Class Average'
                        df_combined = pd.concat([student_avg, df_class_all])
                        df_combined.rename(columns={'grade': 'Grade'}, inplace=True)
                        fig = px.bar(
                            df_combined, x='assignment_name', y='Grade', color='Type', barmode='group',
                            title=f'Your Average Grade vs. Class Average - {selected_class_stats["name"]}',
                            color_discrete_map={'Your Average': '#4a9a9b', 'Class Average': '#aecdc2'}
                        )
                        fig.update_layout(xaxis_title="Assignment", yaxis_title="Average Grade", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No class average data available for comparison.")
            
            with tab2:
                if selected_class_stats is None:
                    fig_box = px.box(df_student, x='assignment_name', y='grade', title="Your Grade Distribution by Assignment (All Classes)", points="all")
                else:
                    fig_box = px.box(df_student, x='assignment_name', y='grade', title=f"Your Grade Distribution by Assignment - {selected_class_stats['name']}", points="all")
                fig_box.update_layout(xaxis_title="Assignment", yaxis_title="Grade", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_box, use_container_width=True)
            
            # Add performance by class tab for overall view
            if selected_class_stats is None:
                with tab3:
                    # Performance by class
                    class_performance = df_student.groupby('class_name')['grade'].agg(['mean', 'count']).reset_index()
                    class_performance.columns = ['Class', 'Average Grade', 'Number of Assignments']
                    
                    fig_class = px.bar(
                        class_performance, 
                        x='Class', 
                        y='Average Grade',
                        title='Your Average Grade by Class',
                        color='Average Grade',
                        color_continuous_scale='RdYlGn'
                    )
                    fig_class.update_layout(xaxis_title="Class", yaxis_title="Average Grade", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_class, use_container_width=True)
                    
                    # Show detailed class performance table
                    st.markdown("#### Detailed Class Performance")
                    st.dataframe(class_performance, use_container_width=True)

# =========================
# Sidebar Navigation
# =========================
with st.sidebar:
    if st.session_state.user.get('is_professor'):
        st.page_link('pages/2_Professor_View.py', label='Professor View', icon='👨‍🏫')
        st.page_link('pages/4_Grades_View.py', label='Grade Analytics', icon='📊')
    else:
        st.title("🎓 Student Menu")
        st.page_link('pages/3_Student_View.py', label='Student View', icon='👨‍🎓')
        st.page_link('pages/1_Home.py', label='Home', icon='🏠')
        st.page_link('pages/4_Grades_View.py', label='Grades View', icon='📊')
    
    st.markdown("---")
    
    # Session management
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Session", use_container_width=True, help="Refresh your session token"):
            if refresh_token_if_needed():
                st.success("Session refreshed!")
            else:
                st.info("Session is still valid")
    
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("login.py")