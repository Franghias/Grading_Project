import streamlit as st
import requests
import os
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

# =========================
# Environment and API Setup
# =========================

load_dotenv()
API_URL = os.getenv('API_URL', 'http://localhost:8000')

# =========================
# Page Configuration and Sidebar
# =========================

st.set_page_config(
    page_title="Class Statistics",
    page_icon="📈",
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
        :root {
            --bg-color: #f7f3e3;
            --text-color: #1a202c;
            --card-bg: #f7fafc;
            --primary-bg: #4a9a9b;
            --primary-hover: #3d8283;
            --border-color: #e2e8f0;
        }
        html, body, .stApp {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .header {
            background-color: #4a9a9b;
            padding: 2rem;
            text-align: center;
            color: #ffffff;
            margin-bottom: 2rem;
        }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
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
st.markdown('<h1>📈 Class Statistics</h1>', unsafe_allow_html=True)
st.markdown('<p>View overall grade statistics for your classes</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# =========================
# Fetch Professor's Classes
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

classes = fetch_classes()
if not classes:
    st.warning("You are not teaching any classes yet.")
    st.stop()

selected_class = st.selectbox(
    "Select a class",
    options=classes,
    format_func=lambda x: f"{x['name']} ({x['code']})"
)

# =========================
# Fetch Submissions for Selected Class
# =========================

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

if selected_class:
    submissions = fetch_class_submissions(selected_class['id'])
    if not submissions:
        st.info("No submissions found for this class.")
        st.stop()

    # Use final_grade if available, else professor_grade, else ai_grade
    grades = []
    for sub in submissions:
        grade = sub.get('final_grade')
        if grade is None:
            grade = sub.get('professor_grade')
        if grade is None:
            grade = sub.get('ai_grade')
        if grade is not None:
            grades.append(grade)

    if not grades:
        st.info("No grades available for this class yet.")
        st.stop()

    grades_np = np.array(grades)
    mean = np.mean(grades_np)
    median = np.median(grades_np)
    mode = float(pd.Series(grades_np).mode().iloc[0]) if len(grades_np) > 0 else None
    min_grade = np.min(grades_np)
    max_grade = np.max(grades_np)
    count = len(grades_np)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Grade Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Mean", f"{mean:.2f}")
        st.metric("Median", f"{median:.2f}")
    with col2:
        st.metric("Mode", f"{mode:.2f}")
        st.metric("Min", f"{min_grade:.2f}")
    with col3:
        st.metric("Max", f"{max_grade:.2f}")
        st.metric("# of Grades", count)
    st.markdown("</div>", unsafe_allow_html=True)

    # Grade Distribution Histogram
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Grade Distribution")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(grades_np, bins=10, color="#4a9a9b", edgecolor="black", alpha=0.7)
    ax.set_xlabel("Grade")
    ax.set_ylabel("Number of Students")
    ax.set_title("Grade Distribution Histogram")
    st.pyplot(fig)
    st.markdown("</div>", unsafe_allow_html=True)

    # Pie chart of grade ranges
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Grade Ranges Pie Chart")
    bins = [0, 60, 70, 80, 90, 100]
    labels = ['F (<60)', 'D (60-69)', 'C (70-79)', 'B (80-89)', 'A (90-100)']
    grade_ranges = pd.cut(grades_np, bins=bins, labels=labels, include_lowest=True, right=True)
    range_counts = grade_ranges.value_counts().sort_index()
    fig2, ax2 = plt.subplots()
    ax2.pie(range_counts, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.PuBuGn(np.linspace(0.3, 0.9, len(labels))))
    ax2.axis('equal')
    st.pyplot(fig2)
    st.markdown("</div>", unsafe_allow_html=True)

    # Show raw data option
    with st.expander("Show Raw Grades Data"):
        st.write(pd.DataFrame({'Grade': grades_np}))

# Sidebar navigation for professors
if st.session_state.user.get('is_professor'):
    with st.sidebar:
        st.title('Professor Menu')
        st.page_link('pages/2_Professor_View.py', label='Professor View', icon='👨‍🏫')
        st.page_link('pages/5_Prompt_Management.py', label='Prompt Management', icon='📝')
        st.page_link('pages/create_class.py', label='Create Class', icon='➕')
        st.page_link('pages/4_Grades_View.py', label='Grades View', icon='📊')
        st.page_link('pages/7_Class_Statistics.py', label='Class Statistics', icon='📈')
        st.page_link('login.py', label='Logout', icon='🚪') 