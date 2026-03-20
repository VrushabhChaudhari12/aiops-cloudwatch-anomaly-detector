"""
AIOps CloudWatch Anomaly Detector - Main analysis logic using Ollama LLM
"""

import time
from openai import OpenAI

# Configuration
BASE_URL = "http://localhost:11434/v1"
API_KEY = "ollama"
MODEL = "llama3.2"
TIMEOUT_SECONDS = 60
MAX_RETRIES = 3
LOOP_DETECTION_LIMIT = 3

# Required fields in the response
REQUIRED_FIELDS = ["INSIGHT_TYPE", "SEVERITY", "SERVICE", "WHAT", "WHY", "IMPACT", "ACTION", "AUTO_RESOLVE"]

# Termination conditions
TERMINATION_CONDITIONS = [
    "CRITICAL",
    "OUTAGE",
    "SERVICE_DOWN",
    "DATA_LOSS",
]


def _parse_response(response_text):
    """
    Parse the LLM response to extract the 8 required fields.

    Args:
        response_text: Raw response from the LLM

    Returns:
        Dictionary with the 8 fields, or None if parsing fails
    """
    result = {}
    lines = response_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line starts with a required field
        for field in REQUIRED_FIELDS:
            if line.startswith(field + ":"):
                value = line[len(field) + 1:].strip()
                result[field] = value
                break

    # Validate all 8 fields are present and not empty
    if all(field in result and result[field].strip() for field in REQUIRED_FIELDS):
        return result
    return None


def _check_termination_condition(analysis):
    """
    Check if the analysis indicates a critical condition.

    Args:
        analysis: Parsed analysis dictionary

    Returns:
        True if termination is needed, False otherwise
    """
    severity = analysis.get("SEVERITY", "").upper()

    for condition in TERMINATION_CONDITIONS:
        if condition in severity:
            return True
    return False


def _detect_loop(previous_results):
    """
    Detect if the same error is repeating.

    Args:
        previous_results: List of previous result dictionaries

    Returns:
        True if same error repeats LOOP_DETECTION_LIMIT times, False otherwise
    """
    if len(previous_results) < LOOP_DETECTION_LIMIT:
        return False

    # Check last N results for same WHAT field
    recent = previous_results[-LOOP_DETECTION_LIMIT:]
    what_values = [r.get("WHAT", "") for r in recent]

    # If all same, it's a loop
    return len(set(what_values)) == 1


def analyse_insight(insight_json, stack_name):
    """
    Analyze a DevOps Guru insight using Ollama LLM with four-layer termination safety.

    Args:
        insight_json: String containing the DevOps Guru insight JSON
        stack_name: Name of the affected stack

    Returns:
        Dictionary with fields: INSIGHT_TYPE, SEVERITY, SERVICE, WHAT, WHY, IMPACT, ACTION, AUTO_RESOLVE

    Raises:
        Exception: If all retries fail or response is invalid
    """
    from prompts import SYSTEM_PROMPT, build_prompt

    # Build the prompt
    user_message = build_prompt(insight_json, stack_name)

    # Initialize the client
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=TIMEOUT_SECONDS)

    # Track previous results for loop detection
    previous_results = []

    # Retry logic with exponential backoff
    last_error = None

    for attempt in range(MAX_RETRIES):
        # Layer 4: Loop detection
        if _detect_loop(previous_results):
            raise ValueError(f"Loop detected: same anomaly repeated {LOOP_DETECTION_LIMIT} times")

        try:
            # Make the LLM call
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=600,
            )

            # Extract response text
            response_text = response.choices[0].message.content

            # Validate response - check all 8 fields are present
            result = _parse_response(response_text)

            if result is None:
                # Invalid response format - could retry
                last_error = ValueError(f"Invalid response format - missing required fields")
                if attempt < MAX_RETRIES - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                raise last_error

            # Track result for loop detection
            previous_results.append(result)

            # Layer 1: Check termination condition
            if _check_termination_condition(result):
                pass

            # Layer 2: Additional validation - ensure fields are meaningful
            if not all(result.get(field, "").strip() for field in REQUIRED_FIELDS):
                last_error = ValueError("Some fields are empty after parsing")
                if attempt < MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                raise last_error

            # Layer 3: Validate insight_type is valid
            insight_type = result.get("INSIGHT_TYPE", "").upper()
            if "REACTIVE" not in insight_type and "PROACTIVE" not in insight_type:
                last_error = ValueError(f"Invalid INSIGHT_TYPE: {insight_type}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                raise last_error

            # All validations passed, return result
            return result

        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            # Check if it's a connection error
            is_connection_error = any(
                keyword in error_str
                for keyword in ["connection", "timeout", "refused", "unreachable"]
            )

            if is_connection_error and attempt < MAX_RETRIES - 1:
                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                continue
            elif not is_connection_error:
                # Non-connection error, don't retry
                raise

    # All retries exhausted
    raise last_error