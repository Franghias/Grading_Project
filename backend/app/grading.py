# =========================
# Grading Logic and AI Integration
# =========================
# This file contains helper functions and logic for validating code, constructing prompts, and interacting with the AI grading API.
# It also handles response validation, error handling, and caching of grading results.

import requests
from dotenv import load_dotenv
import os
import json
import logging
import re
from typing import Optional, Dict, Any
from functools import lru_cache
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'

# Load environment variables from .env file
load_dotenv(dotenv_path=env_path)

# Set up logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for retry and cache configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.5
CACHE_SIZE = 100
MAX_CODE_LENGTH = 20000  # Maximum allowed code length
# ALLOWED_CHARS = set("#abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-=[]{}()<>.,;:!@#$%^&*|\\/\"' \n\t")

def validate_code_input(code: str) -> tuple[bool, str]:
    """
    Validate the input code for basic requirements.
    Returns (is_valid, error_message)
    - Checks for non-empty string and length constraints.
    """
    if not code or not isinstance(code, str):
        return False, "Code must be a non-empty string"
    
    if len(code) > MAX_CODE_LENGTH:
        return False, f"Code exceeds maximum length of {MAX_CODE_LENGTH} characters"
    
    return True, ""

def create_retry_session() -> requests.Session:
    """
    Create a requests session with retry logic for robust API calls.
    Retries on certain HTTP errors and supports backoff.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"]  # Explicitly allow POST method retries
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

@lru_cache(maxsize=CACHE_SIZE)
def get_cached_response(code: str) -> Optional[tuple[float, str]]:
    """
    Get cached response for previously graded code.
    Returns None if not cached. Used to avoid redundant API calls.
    """
    return None  # Cache will be populated after successful API calls

def validate_response_structure(data: dict) -> tuple[bool, str]:
    """
    Validate that the response contains all required fields with correct types.
    Returns (is_valid, error_message)
    Checks both top-level and feedback fields for type and presence.
    """
    required_fields = {
        "grade": (int, float),
        "feedback": dict
    }
    
    feedback_fields = {
        "code_quality": str,
        "bugs": list,
        "improvements": list,
        "best_practices": list
    }
    
    # Check top-level fields
    for field, expected_type in required_fields.items():
        if field not in data:
            return False, f"Missing required field: {field}"
        if not isinstance(data[field], expected_type):
            return False, f"Invalid type for {field}: expected {expected_type.__name__}"
    
    # Check feedback fields
    feedback = data["feedback"]
    for field, expected_type in feedback_fields.items():
        if field not in feedback:
            return False, f"Missing required feedback field: {field}"
        if not isinstance(feedback[field], expected_type):
            return False, f"Invalid type for feedback.{field}: expected {expected_type.__name__}"
    
    return True, ""

def extract_json_from_text(text: str) -> dict:
    """
    Try to extract JSON from text, even if it's embedded in other text or markdown code blocks.
    Uses a regex pattern to match JSON structures and validates the result.
    Returns a default error structure if parsing fails.
    """
    import json
    import re
    # Remove markdown code block wrappers
    text = text.strip()
    if text.startswith('```'):
        # Remove triple backticks and optional language
        text = re.sub(r'^```[a-zA-Z0-9]*\n?', '', text)
        text = re.sub(r'```$', '', text)
    # First try direct JSON parsing
    try:
        data = json.loads(text)
        is_valid, error_msg = validate_response_structure(data)
        if is_valid:
            return data
        logger.warning(f"Invalid response structure: {error_msg}")
    except json.JSONDecodeError:
        pass
    # Try to find the largest JSON object in the text
    json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
    matches = list(re.finditer(json_pattern, text, re.DOTALL))
    if matches:
        largest = max(matches, key=lambda m: len(m.group()))
        try:
            data = json.loads(largest.group())
            is_valid, error_msg = validate_response_structure(data)
            if is_valid:
                return data
            logger.warning(f"Invalid response structure in extracted JSON: {error_msg}")
        except json.JSONDecodeError:
            logger.warning("Failed to parse extracted JSON structure")
    fallback_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    match = re.search(fallback_pattern, text)
    if match:
        try:
            data = json.loads(match.group())
            is_valid, error_msg = validate_response_structure(data)
            if is_valid:
                return data
            logger.warning(f"Invalid response structure in fallback extracted JSON: {error_msg}")
        except json.JSONDecodeError:
            logger.warning("Failed to parse fallback extracted JSON structure")
    # If no valid JSON found, create a structured response
    logger.error("Could not extract valid JSON from response")
    return {
        "grade": 0,
        "feedback": {
            "code_quality": "Could not parse AI response. The response was missing the required 'grade' field. Please ensure your prompt instructs the AI to return a JSON object with a top-level 'grade' field (number) and a 'feedback' object as shown in the sample.",
            "bugs": ["Response parsing failed"],
            "improvements": ["Check your prompt and make sure the AI returns the required JSON structure."],
            "best_practices": ["Response format error"]
        }
    }

def safe_list(val, default=None):
    if isinstance(val, list):
        return val
    if val is None:
        return default if default is not None else []
    if isinstance(val, str):
        return [val] if val.strip() else []
    return list(val) if hasattr(val, '__iter__') else [val]

def format_feedback(feedback, error_msg=None):
    if error_msg:
        return f"""
Code Quality Assessment: Could not parse AI response\nPotential Bugs:\n\n{error_msg}\nSuggested Improvements:\n\nPlease ensure your prompt instructs the AI to return a response in the following JSON format:\n\n{{\n    \"grade\": <number>,\n    \"feedback\": {{\n        \"code_quality\": \"<assessment>\",\n        \"bugs\": [\"<bug1>\", ...],\n        \"improvements\": [\"<suggestion1>\", ...],\n        \"best_practices\": [\"<practice1>\", ...]\n    }}\n}}\n\nBest Practices:\n\nResponse format error\n"""
    return f"""
Code Quality Assessment:\n{feedback.get('code_quality', 'No assessment provided')}\n\nPotential Bugs:\n{chr(10).join(f'- {bug}' for bug in feedback['bugs'])}\n\nSuggested Improvements:\n{chr(10).join(f'- {imp}' for imp in feedback['improvements'])}\n\nBest Practices:\n{chr(10).join(f'- {practice}' for practice in feedback['best_practices'])}\n"""

def grade_code(code: str, description: str = None) -> tuple[float, str]:
    """
    Grade Python code using AI API.
    Returns a tuple of (grade, feedback).
    - Validates input code.
    - Builds a prompt including assignment description and code.
    - Calls the AI API and parses the response.
    - Handles errors and caches results.
    """
    # Input validation
    is_valid, error_msg = validate_code_input(code)
    if not is_valid:
        logger.error(f"Invalid code input: {error_msg}")
        return 0.0, f"Error: {error_msg}"

    # Check cache
    cached_result = get_cached_response(code)
    if cached_result is not None:
        logger.info("Returning cached response")
        return cached_result

    api_key = os.getenv("AI_API_KEY", "").strip()
    endpoint = os.getenv("AI_API_ENDPOINT", "").strip()
    
    if not api_key or not endpoint:
        logger.error("Missing API configuration")
        return 0.0, "Error: The AI API configuration is missing"
    
    logger.info(f"Using API endpoint: {endpoint}")
    
    # Prepare the prompt for code analysis
    prompt = f"""As a Computer Science Professor Assistant, please analyze this Python code for the following assignment:\n\nAssignment Description:\n{description or 'No description provided'}\n\nPlease provide:\n1. A grade (0-100)\n2. Detailed feedback including:\n   - Code quality assessment\n   - Potential bugs or issues\n   - Suggestions for improvement\n   - Best practices followed or missing\n\nCode to analyze:\n```python\n{code}\n```\n\nIMPORTANT: Your response MUST be in valid JSON format with this exact structure:\n{{\n    \"grade\": <number>,\n    \"feedback\": {{\n        \"code_quality\": \"<assessment>\",\n        \"bugs\": [\"<bug1>\", \"<bug2>\", ...],\n        \"improvements\": [\"<suggestion1>\", ...],\n        \"best_practices\": [\"<practice1>\", ...]\n    }}\n}}\n\nDo not include any text before or after the JSON structure."""

    try:
        logger.info("Sending request to AI API...")
        # print("AI_MODEL:", os.getenv("AI_MODEL"))
        request_payload = {
            "model": os.getenv("AI_MODEL", "").strip(),
            "messages": [
                {"role": "system", "content": "You are a Computer Science Professor Assistant grading Python code. You must respond in valid JSON format only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500,
            "stream": False,
            # "response_format": { "type": "json_object" }  # Force JSON response
        }
        # logger.info(f"Request payload: {json.dumps(request_payload, indent=2)}")
        
        # Use retry session for the request
        session = create_retry_session()
        response = session.post(
            endpoint,
            json=request_payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "HTTP-Referer": "http://localhost:8000",  # Required by OpenRouter
                "X-Title": "Code Grading System"  # Required by OpenRouter
            },
            timeout=(10, 30)  # (connect timeout, read timeout)
        )
        
        logger.info(f"Response status: {response.status_code}")
        # logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            error_msg = f"API Error Response: {response.text}"
            logger.error(error_msg)
            return 0.0, f"Error: API returned status {response.status_code}. Please check the logs for details."
            
        response.raise_for_status()
        result = response.json()
        
        # Add detailed logging
        # logger.info(f"Raw API response: {json.dumps(result, indent=2)}")
        
        # Extract the AI's response
        ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        # logger.info(f"Extracted AI response: {ai_response}")
        
        # Try to parse the response
        feedback_data = extract_json_from_text(ai_response)
        grade = float(feedback_data.get("grade", 0))
        
        # Format the feedback in a structured way
        feedback = feedback_data.get("feedback", {})
        # Robustly handle feedback fields
        feedback["bugs"] = safe_list(feedback.get("bugs"), ["No bugs identified"])
        feedback["improvements"] = safe_list(feedback.get("improvements"), ["No improvements suggested"])
        feedback["best_practices"] = safe_list(feedback.get("best_practices"), ["No best practices noted"])
        formatted_feedback = format_feedback(feedback)
        logger.info("Successfully processed AI response")
        
        # Cache the successful response
        get_cached_response.cache_clear()  # Clear old cache entries if needed
        get_cached_response(code)  # Cache the new response
        
        return grade, formatted_feedback.strip()
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return 0.0, f"Error: Could not connect to Deepseek API. Please check your internet connection and API endpoint."
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timeout: {str(e)}")
        return 0.0, "Error: Request to Deepseek API timed out. Please try again."
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return 0.0, f"Error connecting to AI API: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        formatted_feedback = format_feedback({}, error_msg="Response parsing failed")
        return 0.0, formatted_feedback.strip()

def grade_code_with_prompt(code: str, prompt: str) -> tuple[float, str]:
    """
    Grade Python code using AI API with a custom prompt
    Returns a tuple of (grade, feedback)
    """
    # Input validation
    is_valid, error_msg = validate_code_input(code)
    if not is_valid:
        logger.error(f"Invalid code input: {error_msg}")
        return 0.0, f"Error: {error_msg}"

    api_key = os.getenv("AI_API_KEY", "").strip()
    endpoint = os.getenv("AI_API_ENDPOINT", "").strip()
    if not api_key or not endpoint:
        logger.error("Missing API configuration")
        return 0.0, "Error: The AI API configuration is missing"

    logger.info(f"Using API endpoint: {endpoint}")

    try:
        logger.info("Sending request to AI API with custom prompt...")
        request_payload = {
            "model": os.getenv("AI_MODEL", "").strip(),
            "messages": [
                {"role": "system", "content": "You are a Computer Science Professor Assistant grading Python code. You must respond in valid JSON format only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500,
            "stream": False,
            # "response_format": { "type": "json_object" }
        }
        session = create_retry_session()
        response = session.post(
            endpoint,
            json=request_payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Code Grading System"
            },
            timeout=(10, 30)
        )

        logger.info(f"Response status: {response.status_code}")
        if response.status_code != 200:
            error_msg = f"API Error Response: {response.text}"
            logger.error(error_msg)
            return 0.0, f"Error: API returned status {response.status_code}. Please check the logs for details."
        
        # Try to parse the response
        response.raise_for_status()
        result = response.json()

        # Format the feedback in a structured way
        ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        feedback_data = extract_json_from_text(ai_response)
        
        grade = float(feedback_data.get("grade", 0))
        feedback = feedback_data.get("feedback", {})

        # Robustly handle feedback fields
        feedback["bugs"] = safe_list(feedback.get("bugs"), ["No bugs identified"])
        feedback["improvements"] = safe_list(feedback.get("improvements"), ["No improvements suggested"])
        feedback["best_practices"] = safe_list(feedback.get("best_practices"), ["No best practices noted"])
        formatted_feedback = format_feedback(feedback)
        
        logger.info("Successfully processed AI response")

        formatted_feedback = format_feedback(feedback)
        
        logger.info("Successfully processed AI response (custom prompt)")
        return grade, formatted_feedback.strip()
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return 0.0, f"Error: Could not connect to Deepseek API. Please check your internet connection and API endpoint."
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timeout: {str(e)}")
        return 0.0, "Error: Request to Deepseek API timed out. Please try again."
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return 0.0, f"Error connecting to AI API: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        formatted_feedback = format_feedback({}, error_msg="Response parsing failed")
        return 0.0, formatted_feedback.strip()
