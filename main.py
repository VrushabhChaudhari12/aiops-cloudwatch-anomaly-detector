"""
AIOps CloudWatch Anomaly Detector - Main entry point

Runs DevOps Guru insight scenarios through LLM analysis and posts results to Slack.
Supports CLI arguments for targeted scenario execution and configurable log levels.
"""
import argparse
import logging
import sys

import config
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


def _setup_logging(level: str) -> None:
    """Configure root logger with the given level string."""
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def run_scenario(scenario_name: str, stack_name: str) -> bool:
    """
    Run a single scenario: get insight, analyze, and post to Slack.

    Args:
        scenario_name: The scenario key
        stack_name: Name of the affected stack

    Returns:
        True on success, False on failure
    """
    logger = logging.getLogger(__name__)
    logger.info("Running scenario: %s | stack: %s", scenario_name, stack_name)

    try:
        insight_json = get_insight(scenario_name)
        result = analyse_insight(insight_json, stack_name)
        post_to_slack(result, stack_name)
        logger.info(
            "Scenario complete: %s | confidence=%.2f",
            scenario_name,
            result.get("_confidence", 0.0),
        )
        return True
    except Exception as exc:
        logger.error("Scenario failed: %s - %s", scenario_name, exc)
        return False


def main() -> int:
    """Parse CLI args, configure logging, and run selected scenarios."""
    parser = argparse.ArgumentParser(
        description="AIOps CloudWatch Anomaly Detector"
    )
    parser.add_argument(
        "--scenario",
        choices=[s for s, _ in SCENARIOS],
        help="Run a specific scenario only (default: all)",
    )
    parser.add_argument(
        "--log-level",
        default=config.LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: %(default)s)",
    )
    args = parser.parse_args()

    _setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    targets = [
        (s, stk) for s, stk in SCENARIOS
        if args.scenario is None or s == args.scenario
    ]

    logger.info("Starting AIOps CloudWatch Anomaly Detector (%d scenario(s))", len(targets))
    failures = 0
    for scenario_name, stack_name in targets:
        success = run_scenario(scenario_name, stack_name)
        if not success:
            failures += 1

    if failures:
        logger.warning("%d scenario(s) failed out of %d", failures, len(targets))
    else:
        logger.info("All %d scenario(s) completed successfully", len(targets))

    return failures  # exit code: 0 = all passed


if __name__ == "__main__":
    sys.exit(main())
