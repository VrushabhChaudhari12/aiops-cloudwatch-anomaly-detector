"""
Slack Notifier - Formats and sends anomaly analysis as a Slack-style message.

Supports both real Slack webhook delivery (via SLACK_WEBHOOK_URL) and
console output when no webhook is configured. Severity-aware color coding
and confidence score display included.
"""
import json
import logging
import urllib.request
from datetime import datetime

import config

logger = logging.getLogger(__name__)


def _build_payload(analysis: dict, stack_name: str) -> dict:
    """
    Build a Slack Block Kit payload from the analysis result.

    Args:
        analysis: Dict with INSIGHT_TYPE, SEVERITY, SERVICE, WHAT, WHY,
                  IMPACT, ACTION, AUTO_RESOLVE, and optional _confidence
        stack_name: Name of the affected stack

    Returns:
        Slack-compatible Block Kit payload dict
    """
    insight_type = analysis.get("INSIGHT_TYPE", "UNKNOWN").strip().upper()
    severity = analysis.get("SEVERITY", "UNKNOWN").strip().upper()
    confidence = analysis.get("_confidence", None)

    # Color emoji based on severity
    if "CRITICAL" in severity:
        color_emoji = ":red_circle:"
    elif "HIGH" in severity:
        color_emoji = ":large_orange_circle:"
    elif "MEDIUM" in severity:
        color_emoji = ":large_yellow_circle:"
    else:
        color_emoji = ":large_green_circle:"

    insight_label = (
        "*REACTIVE - ANOMALY DETECTED*" if "REACTIVE" in insight_type
        else "*PROACTIVE - ANOMALY PREDICTED*"
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    confidence_str = f" | Confidence: {confidence:.0%}" if confidence is not None else ""

    return {
        "text": f"{color_emoji} AIOps Alert: {insight_type} on {stack_name}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{color_emoji} AIOps CloudWatch Alert",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Stack:*\n{stack_name}"},
                    {"type": "mrkdwn", "text": f"*Insight Type:*\n{insight_label}"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity}"},
                    {"type": "mrkdwn", "text": f"*Service:*\n{analysis.get('SERVICE', 'N/A')}"},
                ],
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*What is happening:*\n{analysis.get('WHAT', 'N/A')}\n\n"
                        f"*Root cause:*\n{analysis.get('WHY', 'N/A')}\n\n"
                        f"*Impact:*\n{analysis.get('IMPACT', 'N/A')}\n\n"
                        f"*Immediate actions:*\n{analysis.get('ACTION', 'N/A')}\n\n"
                        f"*Auto-resolve:*\n{analysis.get('AUTO_RESOLVE', 'N/A')}"
                    ),
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Analysis completed at {timestamp}{confidence_str}_",
                    }
                ],
            },
        ],
    }


def _send_webhook(payload: dict) -> None:
    """POST payload to the configured Slack webhook URL."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        config.SLACK_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Slack webhook returned HTTP {resp.status}")
    logger.info("Slack notification sent successfully")


def _print_console(analysis: dict, stack_name: str) -> None:
    """Print a formatted console representation (fallback when no webhook configured)."""
    insight_type = analysis.get("INSIGHT_TYPE", "UNKNOWN").strip().upper()
    severity = analysis.get("SEVERITY", "UNKNOWN").strip().upper()
    confidence = analysis.get("_confidence", None)

    if "REACTIVE" in insight_type:
        header_color = "\033[91m"
        header_text = "REACTIVE - ANOMALY DETECTED"
    else:
        header_color = "\033[93m"
        header_text = "PROACTIVE - ANOMALY PREDICTED"
    reset = "\033[0m"

    sep = "=" * 70
    div = "-" * 70
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    confidence_str = f" | Confidence: {confidence:.0%}" if confidence is not None else ""

    print(f"\n{sep}")
    print(f"{header_color}{'=':*<15} {header_text} {'=':*<15}{reset}")
    print(f"{sep}")
    print(f"\n*Stack:* {stack_name}")
    print(f"*Insight Type:* {analysis.get('INSIGHT_TYPE', 'N/A')}")
    print(div)
    print(f"\n*SEVERITY:* {severity}")
    print(f"*SERVICE:* {analysis.get('SERVICE', 'N/A')}")
    print(f"*WHAT:* {analysis.get('WHAT', 'N/A')}")
    print(f"*WHY:* {analysis.get('WHY', 'N/A')}")
    print(f"*IMPACT:* {analysis.get('IMPACT', 'N/A')}")
    print(f"*ACTION:* {analysis.get('ACTION', 'N/A')}")
    print(f"*AUTO_RESOLVE:* {analysis.get('AUTO_RESOLVE', 'N/A')}")
    print(f"\n{div}")
    print(f"_Analysis completed at {timestamp}{confidence_str}_")
    print(f"{sep}\n")


def post_to_slack(analysis: dict, stack_name: str) -> None:
    """
    Send analysis to Slack or print to console if no webhook is configured.

    Args:
        analysis: Analysis result dictionary from detector.analyse_insight()
        stack_name: Name of the affected stack
    """
    if config.SLACK_WEBHOOK_URL:
        try:
            payload = _build_payload(analysis, stack_name)
            _send_webhook(payload)
            return
        except Exception as exc:
            logger.warning("Slack webhook failed, falling back to console: %s", exc)

    _print_console(analysis, stack_name)
