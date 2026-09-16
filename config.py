"""Central configuration. Everything sensitive comes from environment variables."""

import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

# Load the project .env file even when the same variables already exist in the
# OS environment. This prevents stale shell/session values from overriding the
# repo's intended credentials.
load_dotenv(override=True)


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Copy .env.example to .env and fill it in."
        )
    return value


# --- API keys -------------------------------------------------------------
TAVILY_API_KEY = _require("TAVILY_API_KEY")
GROQ_API_KEY = _require("GROQ_API_KEY")

# --- Email ----------------------------------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = _require("SMTP_USER")          # the sending Gmail address
SMTP_PASSWORD = _require("SMTP_PASSWORD")  # Gmail App Password, NOT your login password
SENDER_NAME = os.getenv("SENDER_NAME", "AI Daily Brief")
RECIPIENTS = [
    addr.strip()
    for addr in os.getenv("RECIPIENTS", "rithvik.manda@invesco.com").split(",")
    if addr.strip()
]

# --- Model ----------------------------------------------------------------
# Groq rotates model IDs fairly often. If one 404s, the next in the list is tried.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_FALLBACK_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

# --- News search ----------------------------------------------------------
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Kolkata"))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "1"))
RESULTS_PER_QUERY = int(os.getenv("RESULTS_PER_QUERY", "6"))
MAX_STORIES_IN_EMAIL = int(os.getenv("MAX_STORIES_IN_EMAIL", "10"))

# Each query targets a different slice of the generative AI engineering stack so
# the weekly brief covers the topics a platform/AI engineer actually tracks.
SEARCH_QUERIES = [
    "new LLM model releases inference optimizations and API changes",
    "OpenAI Anthropic Google DeepMind Meta AI platform launches SDKs and developer tooling",
    "RAG embeddings vector databases agents evals prompt engineering guardrails",
    "AI infrastructure GPUs inference serving cost optimization deployment patterns",
    "AI security governance compliance model evaluation and industry standards",
]

# Aggregators and low-signal domains get filtered out.
BLOCKED_DOMAINS = {
    "pinterest.com",
    "quora.com",
    "facebook.com",
    "reddit.com",
}
