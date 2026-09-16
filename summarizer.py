"""Turn raw Tavily results into a structured, editorially useful digest via Groq."""

import json
import logging
import re

from groq import Groq

try:
    from . import config
except ImportError:  # pragma: no cover - supports the flat-file layout used here.
    import config

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the editor of a daily AI intelligence briefing read by \
technology professionals. You write with the tone of a Reuters or Bloomberg tech desk: \
precise, factual, no hype, no marketing adjectives, no exclamation marks.

You will be given raw news snippets. Return ONLY a JSON object, with no markdown fences \
and no commentary, in exactly this shape:

{
  "headline_summary": "2-3 sentence executive overview of the single most important \
theme across today's news",
  "stories": [
    {
      "title": "A clean, factual headline you rewrite yourself (max 90 characters)",
      "summary": "2-3 sentences. What happened, who did it, and why it matters. \
Concrete details only.",
      "why_it_matters": "One sentence on the practical implication for people building \
with or adopting AI.",
      "category": "One of: Model Release, Research, Tooling, Industry, Policy, Funding",
      "index": 0
    }
  ]
}

Rules:
- "index" MUST be the integer index of the source story you were given, so links can be \
reattached. Never invent an index.
- Order stories by genuine significance, most important first.
- Do not fabricate facts, numbers, dates, or quotes. If a snippet is too thin to \
summarize honestly, describe only what it actually states.
- Never copy sentences verbatim from the snippets; write in your own words.
- Skip any item that is pure advertising, a listicle, or not actually AI news.
"""


def _build_user_prompt(stories: list[dict]) -> str:
    lines = []
    for i, story in enumerate(stories):
        lines.append(
            f"[{i}] TITLE: {story['title']}\n"
            f"    SOURCE: {story['source']}\n"
            f"    DATE: {story['published'] or 'unknown'}\n"
            f"    SNIPPET: {story['content'][:900]}"
        )
    return "Today's raw AI news items:\n\n" + "\n\n".join(lines)


def _extract_json(text: str) -> dict:
    """Models occasionally wrap JSON in fences or prose. Recover it."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _call_groq(client: Groq, model: str, user_prompt: str) -> str:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )
    return completion.choices[0].message.content


def summarize(stories: list[dict]) -> dict:
    """Return {'headline_summary': str, 'stories': [...]} with source links attached."""
    if not stories:
        return {"headline_summary": "", "stories": []}

    client = Groq(api_key=config.GROQ_API_KEY)
    user_prompt = _build_user_prompt(stories)

    models_to_try = [config.GROQ_MODEL] + [
        m for m in config.GROQ_FALLBACK_MODELS if m != config.GROQ_MODEL
    ]

    last_error: Exception | None = None
    for model in models_to_try:
        try:
            log.info("Summarizing with Groq model: %s", model)
            raw = _call_groq(client, model, user_prompt)
            digest = _extract_json(raw)
            break
        except Exception as exc:
            log.warning("Model %s failed: %s", model, exc)
            last_error = exc
            if "401" in str(exc) or "invalid_api_key" in str(exc).lower():
                raise RuntimeError(
                    "Groq API key is invalid or expired. Generate a new key at console.groq.com "
                    "and update GROQ_API_KEY in config.json or .env."
                ) from exc
    else:
        raise RuntimeError(f"All Groq models failed. Last error: {last_error}")

    # Reattach real URLs and sources using the index the model returned.
    enriched = []
    for item in digest.get("stories", []):
        try:
            idx = int(item.get("index", -1))
        except (TypeError, ValueError):
            continue
        if not 0 <= idx < len(stories):
            continue
        origin = stories[idx]
        enriched.append(
            {
                "title": item.get("title") or origin["title"],
                "summary": item.get("summary", "").strip(),
                "why_it_matters": item.get("why_it_matters", "").strip(),
                "category": item.get("category", "Industry").strip(),
                "url": origin["url"],
                "source": origin["source"],
                "published": origin["published"],
            }
        )

    log.info("Digest built with %d stories", len(enriched))
    return {
        "headline_summary": digest.get("headline_summary", "").strip(),
        "stories": enriched,
    }
