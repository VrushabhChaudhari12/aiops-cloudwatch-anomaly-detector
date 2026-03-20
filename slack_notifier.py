"""
Slack Notifier - Formats and prints anomaly analysis in Slack-style output
"""

from datetime import datetime


def post_to_slack(analysis, stack_name):
    """
    Print a formatted Slack-style message to console.

    Args:
        analysis: Dictionary with fields: INSIGHT_TYPE, SEVERITY, SERVICE, WHAT, WHY, IMPACT, ACTION, AUTO_RESOLVE
        stack_name: Name of the affected stack
    """
    insight_type = analysis.get("INSIGHT_TYPE", "UNKNOWN").strip().upper()
    severity = analysis.get("SEVERITY", "UNKNOWN").strip().upper()

    # Determine header based on insight type
    if "REACTIVE" in insight_type:
        header_color = "\033[91m"  # Red for urgent
        if severity == "CRITICAL":
            header_text = "REACTIVE - CRITICAL ANOMALY DETECTED"
        elif severity == "HIGH":
            header_text = "REACTIVE - HIGH SEVERITY ANOMALY"
        else:
            header_text = "REACTIVE - ANOMALY DETECTED"
    else:
        header_color = "\033[93m"  # Amber/warning for proactive
        header_text = "PROACTIVE - ANOMALY PREDICTED"

    reset_ansi = "\033[0m"

    # Header
    header = "=" * 70
    print(header)
    print(f"{header_color}{'='*15} {header_text} {'='*15}{reset_ansi}")
    print(header)

    # Stack info
    print(f"\n*Stack:* {stack_name}")
    print(f"*Insight Type:* {analysis.get('INSIGHT_TYPE', 'N/A')}")

    # Divider
    divider = "-" * 70

    # Analysis fields
    print(divider)
    print(f"\n*SEVERITY:* {severity}")
    print(f"\n*SERVICE:* {analysis.get('SERVICE', 'N/A')}")
    print(f"\n*WHAT:* {analysis.get('WHAT', 'N/A')}")
    print(f"\n*WHY:* {analysis.get('WHY', 'N/A')}")
    print(f"\n*IMPACT:* {analysis.get('IMPACT', 'N/A')}")
    print(f"\n*ACTION:* {analysis.get('ACTION', 'N/A')}")
    print(f"\n*AUTO_RESOLVE:* {analysis.get('AUTO_RESOLVE', 'N/A')}")

    # Footer with timestamp
    print("\n" + divider)
    footer = "=" * 70
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f" _Analysis completed at {timestamp}_ ")
    print(footer)
    print()