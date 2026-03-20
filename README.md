# AIOps CloudWatch Anomaly Detector

AI-powered anomaly detection for AWS CloudWatch powered by DevOps Guru insights and LLM analysis.

## Overview

Correlates metric anomalies from AWS DevOps Guru and generates plain-English incident summaries with actionable steps.
Automatically classifies insights as REACTIVE (happening now) or PROACTIVE (predicted).

## Features

- **Anomaly Detection**: Identifies unusual patterns in Lambda, RDS, EC2, API Gateway metrics
- **Insight Classification**: REACTIVE vs PROACTIVE categorization
- **Plain-English Summaries**: Converts complex metrics into actionable incident reports

## Stack

- Python
- Ollama (localhost:11434)
- llama3.2 model

## Setup

1. Ensure Ollama is running with llama3.2 model:
   ```bash
   ollama run llama3.2
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Run

```bash
py main.py
```

This will analyze four sample DevOps Guru insight scenarios:
- lambda_duration_spike
- rds_connection_anomaly
- ec2_cpu_proactive
- api_gateway_5xx