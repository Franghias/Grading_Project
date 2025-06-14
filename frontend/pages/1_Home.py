import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time
import base64

# Load environment variables
load_dotenv()
API_URL = os.getenv('API_URL', 'http://localhost:8000')

# Initialize session state for token if not exists
if 'token' not in st.session_state:
    st.session_state.token = None
    st.session_state.user = None

# Check authentication
if not st.session_state.token:
    st.switch_page("login.py")

# Page configuration
st.set_page_config(
    page_title="CS 1111 Grading System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS based on the template
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
            --input-bg: #ffffff;
            --input-border: #cbd5e0;
            --success-bg: #e6fffa;
            --success-text: #2d3748;
            --error-bg: #fee2e2;
            --error-text: #702020;
        }

        /* Apply theme */
        html, body, .stApp {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 16px;
            line-height: 1.5;
        }

        /* Header styling */
        .header {
            background-color: #4a9a9b;
            padding: 2rem;
            text-align: center;
            position: relative;
            overflow: hidden;
            min-height: 200px;
            color: #ffffff;
        }

        .header h1 {
            font-size: 2.25rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .header p {
            font-size: 1rem;
        }

        /* Card styling */
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            padding: 1.5rem;
            text-align: center;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        /* Button styling */
        .stButton > button {
            background-color: var(--primary-bg);
            color: white;
            border-radius: 0.375rem;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: background-color 0.2s ease;
        }

        .stButton > button:hover {
            background-color: var(--primary-hover);
        }

        /* Input and uploader styling */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stFileUploader > div {
            background-color: var(--input-bg);
            color: var(--text-color);
            border: 1px solid var(--input-border);
            border-radius: 0.375rem;
            padding: 0.5rem;
        }

        /* Code block styling */
        .code-block {
            background-color: var(--input-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            padding: 1rem;
            color: var(--text-color);
            font-family: 'Fira Code', monospace;
            font-size: 14px;
        }

        /* Sidebar styling */
        .css-1d391kg {
            background-color: var(--bg-color);
            border-right: 1px solid var(--border-color);
            padding: 1rem;
        }

        /* Success and error messages */
        .success, .error {
            padding: 1rem;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
        }

        .success { background-color: var(--success-bg); color: var(--success-text); }
        .error { background-color: var(--error-bg); color: var(--error-text); }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown('<h1>CS 1111 Grading System</h1>', unsafe_allow_html=True)
st.markdown(f'<p>Welcome, {st.session_state.user["name"]}!</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Create two columns for the main content
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="text-lg font-medium mb-2">Submit Assignment</h3>', unsafe_allow_html=True)
    student_id = st.text_input("Student ID", placeholder="Enter 8-digit student ID", key="submit_student_id")
    uploaded_file = st.file_uploader("Upload Python File", type=["py"], help="Upload a .py file")
    if st.button("Submit Assignment", key="submit_assignment"):
        if student_id and uploaded_file:
            with st.spinner("Analyzing code..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, "text/x-python")}
                    data = {"student_id": student_id}
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    response = requests.post(f"{API_URL}/submissions/", files=files, data=data, headers=headers)
                    response.raise_for_status()
                    result = response.json()
                    st.markdown(f'<div class="success"><h4 class="font-medium">Success!</h4><p>Submission ID: {result["id"]}</p></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="card p-3 mb-3"><p class="text-lg font-medium">Grade: {result["grade"]}/100</p></div>', unsafe_allow_html=True)
                    st.markdown('<h4 class="text-base font-medium mb-1">AI Feedback</h4>', unsafe_allow_html=True)
                    st.markdown(f'<div class="card p-3"><p>{result["feedback"].replace(chr(10), "<br>")}</p></div>', unsafe_allow_html=True)
                except requests.RequestException as e:
                    st.markdown(f'<div class="error"><h4 class="font-medium">Error</h4><p>{str(e)}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error"><p>Please provide both Student ID and Python file</p></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="text-lg font-medium mb-2">View Submission</h3>', unsafe_allow_html=True)
    submission_id = st.number_input("Submission ID", min_value=1, step=1, key="view_submission_id")
    if st.button("View Submission", key="view_submission"):
        with st.spinner("Loading submission..."):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{API_URL}/submissions/{submission_id}", headers=headers)
                response.raise_for_status()
                result = response.json()
                st.markdown('<h4 class="text-base font-medium mb-1">Submission Details</h4>', unsafe_allow_html=True)
                st.markdown(f'<p class="text-sm text-gray-500 mb-2"><strong>Student ID:</strong> {result["student_id"]}</p>', unsafe_allow_html=True)
                st.markdown(f'<div class="card p-3 mb-3"><p class="text-lg font-medium">Grade: {result["grade"]}/100</p></div>', unsafe_allow_html=True)
                st.markdown('<h4 class="text-base font-medium mb-1">AI Feedback</h4>', unsafe_allow_html=True)
                st.markdown(f'<div class="card p-3 mb-2"><p>{result["feedback"].replace(chr(10), "<br>")}</p></div>', unsafe_allow_html=True)
                st.markdown('<h4 class="text-base font-medium mb-1">Submitted Code</h4>', unsafe_allow_html=True)
                st.markdown(f'<div class="code-block"><pre><code class="language-python">{result["code"]}</code></pre></div>', unsafe_allow_html=True)
            except requests.RequestException as e:
                st.markdown(f'<div class="error"><h4 class="font-medium">Error</h4><p>{str(e)}</p></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Add logout button in the sidebar
with st.sidebar:
    if st.button("Logout"):
        st.session_state.token = None
        st.session_state.user = None
        st.switch_page("login.py") 