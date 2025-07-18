# =========================
# Class Statistics & Analytics Dashboard
# =========================
# This file implements a comprehensive analytics dashboard for professors
# to view detailed statistics about their classes, student performance, and trends.

import streamlit as st
import requests
import os
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter
import seaborn as sns
from datetime import datetime, timedelta

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
    page_title="Class Analytics Dashboard",
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
        :root {
            --primary-color: #d4a373;         /* Tan (for headings and primary actions) */
            --primary-hover-color: #faedcd;    /* Sandy Beige (for button hover) */
            --background-color: #e9edc9;      /* Pale Green/Yellow (main background) */
            --card-background-color: #fefae0; /* Creamy Yellow (card background) */
            --text-color: #5d4037;            /* Dark Brown for main text */
            --subtle-text-color: #8a817c;      /* Muted gray-brown for paragraphs */
            --border-color: #ccd5ae;          /* Muted Earthy Green (borders) */
            --secondary-color: #ccd5ae;       /* Muted Earthy Green for secondary elements */
        }
        
        [data-testid="stSidebarNav"] {display: none;}
        
        html, body, .stApp {
            background-color: var(--background-color);
            color: var(--text-color);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .header {
            background-color: var(--card-background-color);
            padding: 2rem;
            text-align: center;
            color: var(--text-color);
            margin-bottom: 2rem;
            border-radius: 15px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px -1px rgba(212, 163, 115, 0.1);
        }
        .header h1, .header p {
             color: var(--text-color);
        }

        .card, .chart-container {
            background-color: var(--card-background-color);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px 0 rgba(212, 163, 115, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# Access Control and Header
# =========================

if 'user' not in st.session_state:
    st.switch_page("login.py")

if not st.session_state.user.get('is_professor'):
    st.error("This page is for professors only")
    st.stop()

st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown('<h1>📊 Class Analytics Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p>Comprehensive insights into student performance and class trends</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Sidebar navigation for professors
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

# =========================
# Helper Functions
# =========================

def fetch_classes():
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

def fetch_class_submissions(class_id):
    try:
        response = requests.get(
            f"{API_URL}/classes/{class_id}/submissions",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching submissions: {str(e)}")
        return []

def fetch_class_assignments(class_id):
    try:
        response = requests.get(
            f"{API_URL}/classes/{class_id}/assignments/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching assignments: {str(e)}")
        return []

def get_grade_letter(grade):
    if grade >= 90: return 'A'
    elif grade >= 80: return 'B'
    elif grade >= 70: return 'C'
    elif grade >= 60: return 'D'
    else: return 'F'

# =========================
# Fetch Data
# =========================

classes = fetch_classes()
if not classes:
    st.warning("You are not teaching any classes yet.")
    st.stop()

# Class selection with refresh button
col1, col2 = st.columns([3, 1])
with col1:
    selected_class = st.selectbox(
        "Select a class",
        options=classes,
        format_func=lambda x: f"{x['name']} ({x['code']})"
    )
with col2:
    if st.button("🔄 Refresh", help="Refresh class statistics"):
        st.rerun()

if selected_class:
    submissions = fetch_class_submissions(selected_class['id'])
    assignments = fetch_class_assignments(selected_class['id'])
    
    if not submissions:
        st.info("No submissions found for this class yet.")
        st.stop()

    # =========================
    # Data Processing
    # =========================
    
    # Create comprehensive dataframe
    data = []
    for sub in submissions:
        final_grade = sub.get('final_grade')
        professor_grade = sub.get('professor_grade')
        
        # Determine which grade to use (prioritize final_grade, then professor_grade)
        grade = final_grade if final_grade is not None else professor_grade
            
        if grade is not None:
            data.append({
                'user_id': sub['user_id'],
                'assignment_id': sub['assignment_id'],
                'grade': grade,
                'ai_grade': sub.get('ai_grade'),
                'professor_grade': professor_grade, # Keep professor_grade for comparison
                'created_at': sub['created_at'],
                'assignment_name': next((a['name'] for a in assignments if a['id'] == sub['assignment_id']), 'Unknown')
            })
    
    if not data:
        st.info("No graded submissions found for this class yet.")
        st.stop()
    
    df = pd.DataFrame(data)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['grade_letter'] = df['grade'].apply(get_grade_letter)

    # --- Data for Student Performance ---
    student_stats = df.groupby('user_id').agg({
        'grade': ['mean', 'count', 'std'],
        'assignment_id': 'nunique'
    }).round(2)
    student_stats.columns = ['Average Grade', 'Total Submissions', 'Grade Std Dev', 'Assignments Attempted']
    student_stats = student_stats.reset_index()

    # =========================
    # Overview Metrics
    # =========================
    
    st.markdown("## 📈 Overview Metrics")
    
    # Calculate passing rate
    passing_rate = (student_stats['Average Grade'] >= 60).mean() * 100
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Average Grade", f"{df['grade'].mean():.1f}%")
    with col2:
        st.metric("Total Submissions", f"{len(df)}")
    with col3:
        st.metric("Active Students", f"{df['user_id'].nunique()}")
    with col4:
        st.metric("Assignments", f"{df['assignment_id'].nunique()}")
    with col5:
        st.metric("Passing Rate", f"{passing_rate:.1f}%")

    # =========================
    # Detailed Analytics Tabs
    # =========================
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Grade Distribution", "📈 Assignment Analysis", "👥 Student Performance", "🤖 AI Grade Analysis", "⏰ Time Trends"])
    
    with tab1:
        st.markdown("## 📊 Grade Distribution Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Grade distribution histogram
            fig_hist = px.histogram(
                df, x='grade', nbins=20,
                title="Overall Grade Distribution",
                labels={'grade': 'Grade (%)', 'count': 'Number of Submissions'},
                color_discrete_sequence=['#d4a373']
            )
            fig_hist.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#5d4037')
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Grade letter distribution
            grade_counts = df['grade_letter'].value_counts()
            fig_pie = px.pie(
                values=grade_counts.values, names=grade_counts.index,
                title="Grade Letter Distribution",
                color_discrete_sequence=px.colors.qualitative.Antique
            )
            fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#5d4037')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # CONSOLIDATED Grade statistics table
        st.markdown("### 📋 Grade Statistics Summary")
        grade_summary = df['grade'].describe().to_frame().T
        st.dataframe(grade_summary, use_container_width=True)
    
    with tab2:
        st.markdown("## 📈 Assignment Performance Analysis")
        
        assignment_stats = df.groupby('assignment_name').agg(
            {'grade': ['mean', 'std', 'count'], 'user_id': 'nunique'}
        ).round(2)
        assignment_stats.columns = ['Average Grade', 'Std Dev', 'Submissions', 'Students']
        assignment_stats = assignment_stats.reset_index()
        
        fig_assignment = px.bar(
            assignment_stats, x='assignment_name', y='Average Grade',
            title="Average Grade by Assignment",
            labels={'assignment_name': 'Assignment', 'Average Grade': 'Average Grade (%)'},
            color='Average Grade', color_continuous_scale='YlOrBr'
        )
        fig_assignment.update_layout(xaxis_tickangle=-45, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#5d4037')
        st.plotly_chart(fig_assignment, use_container_width=True)
        
        st.markdown("### 📋 Assignment Statistics")
        st.dataframe(assignment_stats, use_container_width=True)
    
    with tab3:
        st.markdown("## 👥 Student Performance Analysis")
        
        # REPLACED Top Performers chart with a distribution of student averages
        st.markdown("### Class Performance Distribution")
        fig_student_dist = px.histogram(
            student_stats, x='Average Grade', nbins=15,
            title="Distribution of Student Average Grades",
            labels={'Average Grade': 'Average Grade Bins', 'count': 'Number of Students'},
            color_discrete_sequence=['#d4a373']
        )
        fig_student_dist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#5d4037')
        st.plotly_chart(fig_student_dist, use_container_width=True)
        
        st.markdown("### 📋 Detailed Student Statistics")
        st.dataframe(student_stats, use_container_width=True)
        
    with tab4: # NEW TAB for AI Grade Analysis
        st.markdown("## 🤖 AI vs. Professor Grade Analysis")
        
        df_both_grades = df.dropna(subset=['professor_grade', 'ai_grade']).copy()

        if df_both_grades.empty:
            st.info("No submissions with both AI and Professor grades are available to compare.")
        else:
            mean_abs_diff = (df_both_grades['ai_grade'] - df_both_grades['professor_grade']).abs().mean()
            st.metric("Mean Absolute Difference", f"{mean_abs_diff:.2f} points")

            col1, col2 = st.columns(2)
            with col1:
                fig_scatter = px.scatter(
                    df_both_grades, x='ai_grade', y='professor_grade',
                    title='AI vs. Professor Grade Correlation',
                    trendline="ols", trendline_color_override="#d4a373",
                    labels={'ai_grade': 'AI Grade', 'professor_grade': 'Professor Final Grade'}
                )
                fig_scatter.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#5d4037')
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            with col2:
                fig_hist_comp = go.Figure()
                fig_hist_comp.add_trace(go.Histogram(x=df_both_grades['ai_grade'], name='AI Grades', marker_color='#d4a373', opacity=0.7))
                fig_hist_comp.add_trace(go.Histogram(x=df_both_grades['professor_grade'], name='Professor Grades', marker_color='#ccd5ae', opacity=0.7))
                fig_hist_comp.update_layout(
                    barmode='overlay', title_text='AI vs. Professor Grade Distribution',
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#5d4037'
                )
                fig_hist_comp.update_traces(opacity=0.75)
                st.plotly_chart(fig_hist_comp, use_container_width=True)

    with tab5:
        st.markdown("## ⏰ Time-Based Trends")
        
        # This line creates columns named 'created_at' and 'Submissions'
        daily_submissions = df.groupby(df['created_at'].dt.date).size().reset_index(name='Submissions')
        
        # Use the correct column name 'created_at' for the x-axis
        fig_trend = px.line(
            daily_submissions, x='created_at', y='Submissions',
            title="Daily Submission Trends", markers=True,
            labels={'created_at': 'Date'} # Add a label to display 'Date' on the chart
        )
        fig_trend.update_traces(line_color='#d4a373')
        fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#5d4037')
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # The rest of the tab's code remains the same
        df['date'] = df['created_at'].dt.date
        grade_trends = df.groupby('date')['grade'].mean().reset_index()
        
        fig_grade_trend = px.line(
            grade_trends, x='date', y='grade',
            title="Average Grade Trends Over Time", markers=True,
            labels={'date': 'Date', 'grade': 'Average Grade'}
        )
        fig_grade_trend.update_traces(line_color='#ccd5ae')
        fig_grade_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#5d4037')
        st.plotly_chart(fig_grade_trend, use_container_width=True)
    
    # =========================
    # Export Options
    # =========================
    
    st.markdown("---")
    st.markdown("## 📤 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # The button is just for display; the download_button below handles the action.
        st.button("📊 Export Grade Report", use_container_width=True)
        csv_grades = df.to_csv(index=False)
        st.download_button(
            label="Download Grades as CSV",
            data=csv_grades,
            file_name=f"{selected_class['name']}_grade_report.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # The button is just for display; the download_button below handles the action.
        st.button("📈 Export Statistics Summary", use_container_width=True)
        csv_stats = student_stats.to_csv(index=False)
        st.download_button(
            label="Download Student Stats as CSV",
            data=csv_stats,
            file_name=f"{selected_class['name']}_student_statistics.csv",
            mime="text/csv",
            use_container_width=True
        )