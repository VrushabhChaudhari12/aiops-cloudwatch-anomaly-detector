"""
AIOps CloudWatch Anomaly Detector - Main analysis logic using Ollama LLM
Refactored to use centralized config, structured logging, and confidence scoring.
"""
import time
import logging
import json
from openai import OpenAI
import config

logger = logging.getLogger(__name__)

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
    Attempts JSON parsing first, then falls back to line-by-line parsing.

    Returns:
        dict with the 8 fields, or None if parsing fails
    """
    # Attempt 1: Try JSON parsing
    try:
        data = json.loads(response_text.strip())
        if isinstance(data, dict) and all(f in data for f in REQUIRED_FIELDS):
            logger.debug("Response parsed as JSON successfully")
            return {f: str(data[f]).strip() for f in REQUIRED_FIELDS}
    except (json.JSONDecodeError, ValueError):
        pass

    # Attempt 2: Line-by-line KEY: value parsing
    result = {}
    lines = response_text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        for field in REQUIRED_FIELDS:
            if line.startswith(field + ":"):
                value = line[len(field) + 1:].strip()
                result[field] = value
                break

    if all(field in result and result[field].strip() for field in REQUIRED_FIELDS):
        return result

    logger.warning("Failed to parse response - missing fields: %s",
                   [f for f in REQUIRED_FIELDS if f not in result])
    return None


def _score_confidence(result):
    """
    Score the confidence of an analysis result (0.0 - 1.0).
    Based on field completeness, specificity, and INSIGHT_TYPE validity.
    """
    score = 0.0
    max_score = 4.0

    # All required fields present and non-empty
    filled = sum(1 for f in REQUIRED_FIELDS if result.get(f, "").strip())
    score += (filled / len(REQUIRED_FIELDS)) * 2.0

    # INSIGHT_TYPE is valid
    insight_type = result.get("INSIGHT_TYPE", "").upper()
    if "REACTIVE" in insight_type or "PROACTIVE" in insight_type:
        score += 1.0

    # ACTION field has meaningful content (>10 chars)
    if len(result.get("ACTION", "")) > 10:
        score += 1.0

    return round(score / max_score, 2)


def _check_termination_condition(analysis):
    """Return True if the analysis indicates a critical/termination condition."""
    severity = analysis.get("SEVERITY", "").upper()
    for condition in TERMINATION_CONDITIONS:
        if condition in severity:
            return True
    return False


def _detect_loop(previous_results):
    """Return True if the same WHAT error repeats LOOP_DETECTION_THRESHOLD times."""
    limit = config.LOOP_DETECTION_THRESHOLD
    if len(previous_results) < limit:
        return False
    recent = previous_results[-limit:]
    what_values = [r.get("WHAT", "") for r in recent]
    return len(set(what_values)) == 1


def analyse_insight(insight_json, stack_name):
    """
    Analyze a DevOps Guru insight using the configured LLM with four-layer termination safety.

    Args:
        insight_json: String containing the DevOps Guru insight JSON
        stack_name: Name of the affected stack

    Returns:
        dict with fields: INSIGHT_TYPE, SEVERITY, SERVICE, WHAT, WHY, IMPACT, ACTION,
                          AUTO_RESOLVE, and _confidence (float 0.0-1.0)

    Raises:
        Exception: If all retries fail or response is invalid
    """
    from prompts import SYSTEM_PROMPT, build_prompt

    logger.info("Analysing insight for stack: %s", stack_name)
    user_message = build_prompt(insight_json, stack_name)

    client = OpenAI(
        base_url=config.BASE_URL,
        api_key=config.API_KEY,
        timeout=config.TIMEOUT_SECONDS,
    )

    previous_results = []
    last_error = None

    for attempt in range(config.MAX_RETRIES):
        # Layer 4: Loop detection
        if _detect_loop(previous_results):
            raise ValueError(
                f"Loop detected: same anomaly repeated {config.LOOP_DETECTION_THRESHOLD} times"
            )

        try:
            logger.debug("LLM call attempt %d/%d", attempt + 1, config.MAX_RETRIES)
            response = client.chat.completions.create(
                model=config.MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
            )

            response_text = response.choices[0].message.content
            result = _parse_response(response_text)

            if result is None:
                last_error = ValueError("Invalid response format - missing required fields")
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise last_error

            # Layer 2: Ensure fields are meaningful
            if not all(result.get(field, "").strip() for field in REQUIRED_FIELDS):
                last_error = ValueError("Some fields are empty after parsing")
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise last_error

            # Layer 3: Validate INSIGHT_TYPE
            insight_type = result.get("INSIGHT_TYPE", "").upper()
            if "REACTIVE" not in insight_type and "PROACTIVE" not in insight_type:
                last_error = ValueError(f"Invalid INSIGHT_TYPE: {insight_type}")
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise last_error

            # Attach confidence score
            result["_confidence"] = _score_confidence(result)
            previous_results.append(result)

            # Layer 1: Log if critical termination condition met
            if _check_termination_condition(result):
                logger.warning("Critical termination condition detected: %s",
                               result.get("SEVERITY"))

            logger.info(
                "Analysis complete for %s | severity=%s | confidence=%.2f",
                stack_name,
                result.get("SEVERITY"),
                result["_confidence"],
            )
            return result

        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            is_connection_error = any(
                kw in error_str for kw in ["connection", "timeout", "refused", "unreachable"]
            )
            if is_connection_error and attempt < config.MAX_RETRIES - 1:
                wait_time = 2 ** attempt
                logger.warning("Connection error on attempt %d, retrying in %ds: %s",
                               attempt + 1, wait_time, e)
                time.sleep(wait_time)
                continue
            elif not is_connection_error:
                logger.error("Non-retryable error during analysis: %s", e)
                raise

    logger.error("All %d retries exhausted for stack: %s", config.MAX_RETRIES, stack_name)
    raise last_error
