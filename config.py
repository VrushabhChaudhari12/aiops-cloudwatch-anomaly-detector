"""
Centralized configuration for AIOps CloudWatch Anomaly Detector.
All settings controlled via environment variables with typed defaults.
"""
import os

# LLM Backend
BASE_URL: str = os.getenv("BASE_URL", "http://localhost:11434/v1")
API_KEY: str = os.getenv("API_KEY", "ollama")
MODEL: str = os.getenv("MODEL", "llama3.2")

# Generation settings
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
TIMEOUT_SECONDS: int = int(os.getenv("TIMEOUT_SECONDS", "90"))
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))
LOOP_DETECTION_THRESHOLD: int = int(os.getenv("LOOP_DETECTION_THRESHOLD", "3"))

# Output
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Notifications
SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")

# Anomaly detection thresholds
CRITICAL_ANOMALY_SCORE: float = float(os.getenv("CRITICAL_ANOMALY_SCORE", "80.0"))
HIGH_ANOMALY_SCORE: float = float(os.getenv("HIGH_ANOMALY_SCORE", "50.0"))

# Required sections in anomaly analysis
REQUIRED_SECTIONS: list[str] = [
    "ANOMALY TYPE", "AFFECTED SERVICE", "WHAT IS HAPPENING",
    "ROOT CAUSE", "IMMEDIATE ACTIONS", "ESCALATION"
]
