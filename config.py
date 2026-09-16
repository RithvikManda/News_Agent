"""Central configuration. Sensitive values can come from .env or config.json."""

import json
import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


def _load_json_config() -> dict:
    cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(cfg_path):
        return {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (TypeError, ValueError, OSError):
        return {}


def _env_example_values() -> dict[str, str]:
    values: dict[str, str] = {}
    example_path = os.path.join(os.path.dirname(__file__), ".env.example")
    if not os.path.exists(example_path):
        return values

    with open(example_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def _require(name: str) -> str:
    json_cfg = _load_json_config()
    value = ""

    if name == "GROQ_API_KEY" and json_cfg.get("GROQ_API_KEY"):
        value = str(json_cfg["GROQ_API_KEY"]).strip()
        os.environ[name] = value
    else:
        value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Copy .env.example to .env and fill it in."
        )

    example_value = _env_example_values().get(name)
    if example_value and value == example_value and name != "GROQ_API_KEY":
        raise RuntimeError(
            f"{name} still contains the sample value from .env.example. "
            f"Replace it with a real key from the provider and save .env."
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

# Each query targets a different slice of the AI world so the digest is not
# ten articles about the same launch.
SEARCH_QUERIES = [
    "latest AI model releases and launches",
    "OpenAI Anthropic Google DeepMind Meta AI announcements",
    "new AI developer tools frameworks and open source releases",
    "AI research breakthroughs and notable papers",
    "AI industry funding acquisitions and policy news",
]

# Aggregators and low-signal domains get filtered out.
BLOCKED_DOMAINS = {
    "pinterest.com",
    "quora.com",
    "facebook.com",
    "reddit.com",
}
