"""
AIOps CloudWatch Anomaly Detector - Main entry point

Runs all four DevOps Guru insight scenarios and prints formatted analysis.
"""

from mock_insights import get_insight
from detector import analyse_insight
from slack_notifier import post_to_slack


# Define the scenarios to run
SCENARIOS = [
    ("lambda_duration_spike", "payment-processing-service"),
    ("rds_connection_anomaly", "user-database-cluster"),
    ("ec2_cpu_proactive", "analytics-processing-fleet"),
    ("api_gateway_5xx", "customer-api-gateway"),
]


def run_scenario(scenario_name, stack_name):
    """
    Run a single scenario: get insight, analyze, and post to Slack.

    Args:
        scenario_name: The scenario key
        stack_name: Name of the affected stack
    """
    # Print scenario name
    print(f"\n{'='*70}")
    print(f"  SCENARIO: {scenario_name.upper()}")
    print(f"  STACK: {stack_name}")
    print(f"{'='*70}\n")

    # Get insight JSON
    insight_json = get_insight(scenario_name)

    # Analyze the insight
    result = analyse_insight(insight_json, stack_name)

    # Post to Slack
    post_to_slack(result, stack_name)

    # Add separator between scenarios
    print("\n" + "=" * 70 + "\n")


def main():
    """Run all scenarios sequentially."""
    print("\n" + "=" * 70)
    print("  AIOPS CLOUDWATCH ANOMALY DETECTOR")
    print("=" * 70 + "\n")

    for scenario_name, stack_name in SCENARIOS:
        run_scenario(scenario_name, stack_name)

    print("\nAll scenarios completed.")


if __name__ == "__main__":
    main()