import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Get API URL from environment variable
API_URL = os.getenv('API_URL', 'http://localhost:8000')

# Page configuration
st.set_page_config(
    page_title="CS 1111 Grading System",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        color: #155724;
        margin: 1rem 0;
    }
    .error-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        color: #721c24;
        margin: 1rem 0;
    }
    .feedback-section {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin: 1rem 0;
    }
    .grade-display {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e9ecef;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("📚 CS 1111 Grading System")
st.markdown("""
    Welcome to the CS 1111 Grading System! Submit your Python assignments and get instant AI-powered feedback.
    Make sure your file has a `.py` extension.
""")

# Create two columns for the layout
col1, col2 = st.columns(2)

with col1:
    st.header("📤 Submit Assignment")
    
    # Student ID input
    student_id = st.text_input("Student ID", placeholder="Enter your student ID")
    
    # File upload
    uploaded_file = st.file_uploader("Upload Python file", type=["py"], help="Only .py files are accepted")
    
    # Submit button
    if st.button("Submit Assignment", type="primary"):
        if student_id and uploaded_file:
            with st.spinner("Analyzing your code with AI..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, "text/x-python")}
                    data = {"student_id": student_id}
                    
                    response = requests.post(f"{API_URL}/submissions/", files=files, data=data)
                    response.raise_for_status()
                    result = response.json()
                    
                    # Display submission success
                    st.markdown(f"""
                        <div class="success-message">
                            <h3>✅ Submission Successful!</h3>
                            <p>Submission ID: {result['id']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Display grade
                    st.markdown(f"""
                        <div class="grade-display">
                            Grade: {result['grade']}/100
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Display feedback in sections
                    st.markdown("### 📝 AI Feedback")
                    st.markdown(f"""
                        <div class="feedback-section">
                            {result['feedback'].replace(chr(10), '<br>')}
                        </div>
                    """, unsafe_allow_html=True)
                    
                except requests.RequestException as e:
                    st.markdown(f"""
                        <div class="error-message">
                            <h3>❌ Error</h3>
                            <p>{str(e)}</p>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.error("Please provide both Student ID and Python file")

with col2:
    st.header("📥 View Submission")
    
    # Submission ID input
    submission_id = st.number_input("Enter Submission ID", min_value=1, step=1)
    
    # View button
    if st.button("View Submission", type="secondary"):
        with st.spinner("Loading submission..."):
            try:
                response = requests.get(f"{API_URL}/submissions/{submission_id}")
                response.raise_for_status()
                result = response.json()
                
                st.markdown("### Submission Details")
                st.markdown(f"**Student ID:** {result['student_id']}")
                
                # Display grade
                st.markdown(f"""
                    <div class="grade-display">
                        Grade: {result['grade']}/100
                    </div>
                """, unsafe_allow_html=True)
                
                # Display feedback in sections
                st.markdown("### 📝 AI Feedback")
                st.markdown(f"""
                    <div class="feedback-section">
                        {result['feedback'].replace(chr(10), '<br>')}
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("### 💻 Submitted Code")
                st.code(result['code'], language="python")
                
            except requests.RequestException as e:
                st.markdown(f"""
                    <div class="error-message">
                        <h3>❌ Error</h3>
                        <p>{str(e)}</p>
                    </div>
                """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("Made with ❤️ for CS 1111")