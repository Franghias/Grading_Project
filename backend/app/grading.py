import requests
from dotenv import load_dotenv
import os
import json
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def extract_json_from_text(text: str) -> dict:
    """
    Try to extract JSON from text, even if it's embedded in other text.
    """
    # First try direct JSON parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON-like structure in the text
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    
    # If no JSON found, create a structured response
    return {
        "grade": 0,
        "feedback": {
            "code_quality": "Could not parse AI response",
            "bugs": ["Response parsing failed"],
            "improvements": ["Please try again"],
            "best_practices": ["Response format error"]
        }
    }

def grade_code(code: str) -> tuple[float, str]:
    """
    Grade Python code using Deepseek AI API
    Returns a tuple of (grade, feedback)
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    endpoint = os.getenv("DEEPSEEK_API_ENDPOINT")
    
    if not api_key or not endpoint:
        logger.error("Missing API configuration")
        return 0.0, "Error: Deepseek API configuration missing"
    
    logger.info(f"Using API endpoint: {endpoint}")
    
    # Prepare the prompt for code analysis
    prompt = f"""As a CS professor, please analyze this Python code and provide:
1. A grade (0-100)
2. Detailed feedback including:
   - Code quality assessment
   - Potential bugs or issues
   - Suggestions for improvement
   - Best practices followed or missing

Code to analyze:
```python
{code}
```

IMPORTANT: Your response MUST be in valid JSON format with this exact structure:
{{
    "grade": <number>,
    "feedback": {{
        "code_quality": "<assessment>",
        "bugs": ["<bug1>", "<bug2>", ...],
        "improvements": ["<suggestion1>", "<suggestion2>", ...],
        "best_practices": ["<practice1>", "<practice2>", ...]
    }}
}}

Do not include any text before or after the JSON structure."""

    try:
        logger.info("Sending request to Deepseek API...")
        request_payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a CS professor grading Python code. You must respond in valid JSON format only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500, #Adjust this to increase or decrease the amount of tokens used for better performance over price
            "stream": False
        }
        logger.info(f"Request payload: {json.dumps(request_payload, indent=2)}")
        
        response = requests.post(
            endpoint,
            json=request_payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=30
        )
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            logger.error(f"API Error Response: {response.text}")
            return 0.0, f"Error: API returned status {response.status_code}. Please check the logs for details."
            
        response.raise_for_status()
        result = response.json()
        
        # Extract the AI's response
        ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        logger.info(f"Raw AI response: {ai_response}")
        
        # Try to parse the response
        feedback_data = extract_json_from_text(ai_response)
        grade = float(feedback_data.get("grade", 0))
        
        # Format the feedback in a structured way
        feedback = feedback_data.get("feedback", {})
        formatted_feedback = f"""
Code Quality Assessment:
{feedback.get('code_quality', 'No assessment provided')}

Potential Bugs:
{chr(10).join(f'- {bug}' for bug in feedback.get('bugs', ['No bugs identified']))}

Suggested Improvements:
{chr(10).join(f'- {imp}' for imp in feedback.get('improvements', ['No improvements suggested']))}

Best Practices:
{chr(10).join(f'- {practice}' for practice in feedback.get('best_practices', ['No best practices noted']))}
"""
        logger.info("Successfully processed AI response")
        return grade, formatted_feedback.strip()
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return 0.0, f"Error: Could not connect to Deepseek API. Please check your internet connection and API endpoint."
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timeout: {str(e)}")
        return 0.0, "Error: Request to Deepseek API timed out. Please try again."
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return 0.0, f"Error connecting to Deepseek API: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 0.0, f"An unexpected error occurred: {str(e)}"

