# AIOps CloudWatch Anomaly Detector

> **AI-powered incident triage for AWS CloudWatch** — correlates DevOps Guru insights with an LLM to produce structured, actionable incident reports in seconds.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://python.org)
[![LLM](https://img.shields.io/badge/LLM-Ollama%20%7C%20llama3.2-orange)](https://ollama.ai)
[![AWS](https://img.shields.io/badge/AWS-DevOps%20Guru-yellow?logo=amazon-aws)](https://aws.amazon.com/devops-guru/)
[![Slack](https://img.shields.io/badge/Slack-Webhook%20Ready-4A154B?logo=slack)](https://api.slack.com/messaging/webhooks)

---

## Problem

On-call engineers waste critical minutes interpreting raw CloudWatch metrics during incidents. AWS DevOps Guru surfaces anomalies but the insights are verbose JSON — not immediately actionable.

## Solution

This system feeds DevOps Guru insight JSON into a local LLM (Ollama + llama3.2) and extracts a structured 8-field incident report: anomaly type, severity, affected service, root cause, impact, immediate actions, and auto-resolve guidance. Results are posted to Slack or printed to console with ANSI color coding.

---

## Architecture

```
AWS DevOps Guru
      │
      ▼
 mock_insights.py   ← Simulates insight JSON payloads (Lambda, RDS, EC2, API GW)
      │
      ▼
  detector.py       ← LLM analysis with 4-layer termination safety + confidence scoring
      │             ← Retries with exponential backoff, loop detection, JSON validation
      ▼
slack_notifier.py   ← Formats as Slack Block Kit payload or ANSI console output
      │
      ▼
 Slack / Console
```

---

## Key Features

| Feature | Detail |
|---|---|
| **Insight Classification** | REACTIVE (active incident) vs PROACTIVE (predicted) |
| **Structured Output** | 8 required fields: `INSIGHT_TYPE`, `SEVERITY`, `SERVICE`, `WHAT`, `WHY`, `IMPACT`, `ACTION`, `AUTO_RESOLVE` |
| **Confidence Scoring** | Each analysis scored 0.0–1.0 based on completeness, INSIGHT_TYPE validity, and ACTION specificity |
| **4-Layer Safety** | Termination detection → field validation → INSIGHT_TYPE validation → loop detection |
| **Retry Logic** | Exponential backoff (1s, 2s, 4s) on connection errors; non-retryable errors fail fast |
| **JSON + Line Parsing** | Dual-mode response parsing: tries JSON first, falls back to `KEY: value` line parsing |
| **Slack Block Kit** | Rich formatted alerts with severity emoji, confidence %, and timestamp |
| **12-Factor Config** | All settings via environment variables with typed defaults in `config.py` |
| **CLI Targeting** | `--scenario` flag to run a single scenario; `--log-level` for verbosity control |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.9+ |
| LLM Backend | Ollama (local) — llama3.2 |
| LLM Client | `openai` SDK (OpenAI-compatible) |
| Notifications | Slack Incoming Webhooks / ANSI console |
| Config | Environment variables via `os.getenv` |
| Scenarios | AWS DevOps Guru mock payloads (Lambda, RDS, EC2, API Gateway) |

---

## Quickstart

### 1. Start Ollama with llama3.2

```bash
ollama run llama3.2
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure (optional)

```bash
# All settings have safe defaults — override only what you need
export MODEL=llama3.2
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
export LOG_LEVEL=INFO
export CRITICAL_ANOMALY_SCORE=80.0
```

### 4. Run

```bash
# Run all 4 scenarios
python main.py

# Run a specific scenario
python main.py --scenario lambda_duration_spike

# Debug mode
python main.py --log-level DEBUG
```

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `BASE_URL` | `http://localhost:11434/v1` | Ollama API base URL |
| `API_KEY` | `ollama` | API key (use any string for local Ollama) |
| `MODEL` | `llama3.2` | LLM model name |
| `MAX_RETRIES` | `3` | Max LLM call attempts per scenario |
| `TIMEOUT_SECONDS` | `90` | Per-request timeout |
| `TEMPERATURE` | `0.1` | LLM sampling temperature |
| `MAX_TOKENS` | `2048` | Max tokens per response |
| `LOOP_DETECTION_THRESHOLD` | `3` | Consecutive identical results before loop abort |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `SLACK_WEBHOOK_URL` | `` | Slack incoming webhook URL |
| `CRITICAL_ANOMALY_SCORE` | `80.0` | Score threshold for CRITICAL classification |
| `HIGH_ANOMALY_SCORE` | `50.0` | Score threshold for HIGH classification |

---

## Scenarios

| Scenario Key | Stack | Insight Type |
|---|---|---|
| `lambda_duration_spike` | payment-processing-service | REACTIVE |
| `rds_connection_anomaly` | user-database-cluster | REACTIVE |
| `ec2_cpu_proactive` | analytics-processing-fleet | PROACTIVE |
| `api_gateway_5xx` | customer-api-gateway | REACTIVE |

---

## Output Example

```
2025-01-15T10:23:41 [INFO] detector: Analysing insight for stack: payment-processing-service
2025-01-15T10:23:52 [INFO] detector: Analysis complete for payment-processing-service | severity=HIGH | confidence=0.88

======================================================================
=============== REACTIVE - ANOMALY DETECTED ===============
======================================================================

*Stack:* payment-processing-service
*Severity:* HIGH
*Service:* AWS Lambda
*What:* Lambda function duration exceeding 15s SLA threshold
*Why:* Downstream RDS connection pool exhaustion causing blocking I/O
*Impact:* Payment processing latency p99 > 30s; checkout failures rising
*Action:* 1. Scale RDS read replicas. 2. Enable Lambda concurrency limits.
*Auto-resolve:* No — manual RDS scaling required

_Analysis completed at 2025-01-15 10:23:52 | Confidence: 88%_
```

---

## SRE / DevOps Context

This project demonstrates:

- **Agentic AI patterns**: multi-layer validation, loop detection, confidence scoring, structured extraction from unstructured LLM output
- **Production-grade Python**: typed configs, structured logging (`%(asctime)s [%(levelname)s]`), `argparse` CLI, exit codes
- **Incident management automation**: classifying, triaging, and routing alerts without human intervention
- **LLM reliability engineering**: dual-mode parsing (JSON + line-by-line), exponential backoff, non-retryable error fast-fail

---

## Project Structure

```
aiops-cloudwatch-anomaly-detector/
├── config.py            # Centralized config via env vars
├── detector.py          # LLM analysis engine with safety layers
├── main.py              # CLI entry point with argparse
├── mock_insights.py     # AWS DevOps Guru mock payloads
├── prompts.py           # LLM system prompt and user prompt builder
├── slack_notifier.py    # Slack Block Kit + console output
└── requirements.txt     # Python dependencies
```
