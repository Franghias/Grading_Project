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

# Hide default sidebar
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            margin: 0.5rem 0;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        .chart-container {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# Custom CSS Styling
# =========================

st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-color: #f8fafc;
            --text-color: #1a202c;
            --card-bg: #ffffff;
            --primary-bg: #4a9a9b;
            --primary-hover: #3d8283;
            --border-color: #e2e8f0;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
        }
        html, body, .stApp {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .header {
            background: linear-gradient(135deg, #4a9a9b 0%, #3d8283 100%);
            padding: 2rem;
            text-align: center;
            color: #ffffff;
            margin-bottom: 2rem;
            border-radius: 0 0 20px 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
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
    if st.button("🔄 Refresh", type="secondary", help="Refresh class statistics"):
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
        grade = sub.get('final_grade') or sub.get('professor_grade') or sub.get('ai_grade')
        if grade is not None:
            data.append({
                'user_id': sub['user_id'],
                'assignment_id': sub['assignment_id'],
                'grade': grade,
                'ai_grade': sub.get('ai_grade'),
                'professor_grade': sub.get('professor_grade'),
                'final_grade': sub.get('final_grade'),
                'created_at': sub['created_at'],
                'assignment_name': next((a['name'] for a in assignments if a['id'] == sub['assignment_id']), 'Unknown')
            })
    
    if not data:
        st.info("No graded submissions found for this class yet.")
        st.stop()
    
    df = pd.DataFrame(data)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['grade_letter'] = df['grade'].apply(get_grade_letter)
    
    # =========================
    # Overview Metrics
    # =========================
    
    st.markdown("## 📈 Overview Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Average Grade</div>
            <div class="metric-value">{df['grade'].mean():.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Submissions</div>
            <div class="metric-value">{len(df)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Students</div>
            <div class="metric-value">{df['user_id'].nunique()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Assignments</div>
            <div class="metric-value">{df['assignment_id'].nunique()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # =========================
    # Detailed Analytics Tabs
    # =========================
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Grade Distribution", "📈 Assignment Analysis", "👥 Student Performance", "⏰ Time Trends"])
    
    with tab1:
        st.markdown("## 📊 Grade Distribution Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Grade distribution histogram
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
            # Grade letter distribution
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
        
        # Grade statistics table
        st.markdown("### 📋 Grade Statistics")
        stats_df = df['grade'].describe()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Mean", f"{stats_df['mean']:.2f}%")
            st.metric("Median", f"{df['grade'].median():.2f}%")
        with col2:
            st.metric("Standard Deviation", f"{stats_df['std']:.2f}%")
            st.metric("Variance", f"{stats_df['std']**2:.2f}")
        with col3:
            st.metric("Minimum", f"{stats_df['min']:.2f}%")
            st.metric("Maximum", f"{stats_df['max']:.2f}%")
        with col4:
            st.metric("25th Percentile", f"{stats_df['25%']:.2f}%")
            st.metric("75th Percentile", f"{stats_df['75%']:.2f}%")
    
    with tab2:
        st.markdown("## 📈 Assignment Performance Analysis")
        
        # Assignment performance comparison
        assignment_stats = df.groupby('assignment_name').agg({
            'grade': ['mean', 'std', 'count'],
            'user_id': 'nunique'
        }).round(2)
        assignment_stats.columns = ['Average Grade', 'Std Dev', 'Submissions', 'Students']
        assignment_stats = assignment_stats.reset_index()
        
        # Assignment performance chart
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
        
        # Assignment statistics table
        st.markdown("### 📋 Assignment Statistics")
        st.dataframe(assignment_stats, use_container_width=True)
    
    with tab3:
        st.markdown("## 👥 Student Performance Analysis")
        
        # Student performance summary
        student_stats = df.groupby('user_id').agg({
            'grade': ['mean', 'count', 'std'],
            'assignment_id': 'nunique'
        }).round(2)
        student_stats.columns = ['Average Grade', 'Total Submissions', 'Grade Std Dev', 'Assignments Attempted']
        student_stats = student_stats.reset_index()
        
        # Top performers
        st.markdown("### 🏆 Top Performers")
        top_performers = student_stats.nlargest(5, 'Average Grade')
        fig_top = px.bar(
            top_performers,
            x='user_id',
            y='Average Grade',
            title="Top 5 Students by Average Grade",
            color='Average Grade',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_top, use_container_width=True)
        
        # Student statistics table
        st.markdown("### 📋 Student Statistics")
        st.dataframe(student_stats, use_container_width=True)
    
    with tab4:
        st.markdown("## ⏰ Time-Based Trends")
        
        # Daily submission trends
        daily_submissions = df.groupby(df['created_at'].dt.date).size().reset_index()
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
        
        # Grade trends over time
        df['date'] = df['created_at'].dt.date
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
    # Export Options
    # =========================
    
    st.markdown("---")
    st.markdown("## 📤 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Grade Report", type="primary"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{selected_class['name']}_grade_report.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📈 Export Statistics Summary", type="secondary"):
            summary_data = {
                'Metric': ['Total Submissions', 'Average Grade', 'Active Students', 'Assignments'],
                'Value': [len(df), f"{df['grade'].mean():.2f}%", df['user_id'].nunique(), df['assignment_id'].nunique()]
            }
            summary_df = pd.DataFrame(summary_data)
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="Download Summary",
                data=csv,
                file_name=f"{selected_class['name']}_statistics_summary.csv",
                mime="text/csv"
            )