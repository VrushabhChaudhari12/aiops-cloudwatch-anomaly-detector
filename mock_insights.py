"""
Mock AWS DevOps Guru insight scenarios for testing anomaly detection
"""

import json
from datetime import datetime, timedelta

SCENARIOS = {
    "lambda_duration_spike": {
        "insight_id": "guru-insight-001",
        "insight_type": "REACTIVE",
        "severity": "HIGH",
        "affected_stack": "payment-processing-service",
        "affected_resources": [
            "arn:aws:lambda:us-east-1:123456789012:function:payment-handler",
            "arn:aws:lambda:us-east-1:123456789012:function:payment-validator"
        ],
        "anomalous_metrics": [
            {
                "metric_name": "Duration",
                "resource": "payment-handler",
                "current_value": 8500,
                "baseline_value": 850,
                "unit": "ms",
                "anomaly_type": "spike",
                "percentage_change": 900
            },
            {
                "metric_name": "Duration",
                "resource": "payment-validator",
                "current_value": 7200,
                "baseline_value": 720,
                "unit": "ms",
                "anomaly_type": "spike",
                "percentage_change": 900
            }
        ],
        "related_events": [
            "Cold start detected for payment-handler",
            "Increased memory pressure observed",
            "Concurrent execution reached 500"
        ],
        "start_time": "2024-03-15T14:30:00Z"
    },
    "rds_connection_anomaly": {
        "insight_id": "guru-insight-002",
        "insight_type": "REACTIVE",
        "severity": "HIGH",
        "affected_stack": "user-database-cluster",
        "affected_resources": [
            "arn:aws:rds:us-east-1:123456789012:db:user-prod-cluster",
            "arn:aws:rds:us-east-1:123456789012:cluster:user-prod-cluster"
        ],
        "anomalous_metrics": [
            {
                "metric_name": "DatabaseConnections",
                "resource": "user-prod-cluster",
                "current_value": 450,
                "baseline_value": 150,
                "unit": "Count",
                "anomaly_type": "spike",
                "percentage_change": 200
            },
            {
                "metric_name": "CPUUtilization",
                "resource": "user-prod-cluster",
                "current_value": 85,
                "baseline_value": 35,
                "unit": "Percent",
                "anomaly_type": "high",
                "percentage_change": 143
            }
        ],
        "related_events": [
            "Connection pool exhausted",
            "Wait events increasing",
            "Active transactions peaked"
        ],
        "start_time": "2024-03-15T16:45:00Z"
    },
    "ec2_cpu_proactive": {
        "insight_id": "guru-insight-003",
        "insight_type": "PROACTIVE",
        "severity": "MEDIUM",
        "affected_stack": "analytics-processing-fleet",
        "affected_resources": [
            "arn:aws:ec2:us-east-1:123456789012:instance/i-0abc123def456",
            "arn:aws:ec2:us-east-1:123456789012:instance/i-0def456abc789"
        ],
        "anomalous_metrics": [
            {
                "metric_name": "CPUUtilization",
                "resource": "analytics-worker-1",
                "current_value": 78,
                "baseline_value": 45,
                "unit": "Percent",
                "anomaly_type": "trend",
                "trend": "increasing",
                "percentage_change": 73
            },
            {
                "metric_name": "CPUUtilization",
                "resource": "analytics-worker-2",
                "current_value": 82,
                "baseline_value": 45,
                "unit": "Percent",
                "anomaly_type": "trend",
                "trend": "increasing",
                "percentage_change": 82
            }
        ],
        "related_events": [
            "CPU utilization trending upward over 4 hours",
            "Memory allocation approaching limit",
            "Auto Scaling group approaching max capacity"
        ],
        "start_time": "2024-03-15T10:00:00Z"
    },
    "api_gateway_5xx": {
        "insight_id": "guru-insight-004",
        "insight_type": "REACTIVE",
        "severity": "CRITICAL",
        "affected_stack": "customer-api-gateway",
        "affected_resources": [
            "arn:aws:apigateway:us-east-1:/apis/abc123/stages/prod",
            "arn:aws:apigateway:us-east-1:/apis/abc123/routes/POST /customers"
        ],
        "anomalous_metrics": [
            {
                "metric_name": "5XXError",
                "resource": "prod-stage",
                "current_value": 125,
                "baseline_value": 5,
                "unit": "Count",
                "anomaly_type": "spike",
                "percentage_change": 2400
            },
            {
                "metric_name": "Latency",
                "resource": "prod-stage",
                "current_value": 3500,
                "baseline_value": 250,
                "unit": "ms",
                "anomaly_type": "spike",
                "percentage_change": 1300
            }
        ],
        "related_events": [
            "HTTP 503 Service Unavailable errors detected",
            "Backend service timeout errors increasing",
            "Integration latency exceeding threshold"
        ],
        "start_time": "2024-03-15T18:15:00Z"
    }
}


def get_insight(scenario):
    """
    Get DevOps Guru insight JSON for a given scenario.

    Args:
        scenario: One of 'lambda_duration_spike', 'rds_connection_anomaly', 'ec2_cpu_proactive', 'api_gateway_5xx'

    Returns:
        Formatted JSON string of the insight
    """
    insight = SCENARIOS.get(scenario, SCENARIOS["lambda_duration_spike"])
    return json.dumps(insight, indent=2)