"""Render the digest as a professional HTML email and send it over SMTP."""

import html
import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr

try:
    from . import config
except ImportError:  # pragma: no cover - supports the flat-file layout used here.
    import config

log = logging.getLogger(__name__)

CATEGORY_COLORS = {
    "Model Release": "#1a4d8f",
    "Research": "#5b3a8e",
    "Tooling": "#0f6b52",
    "Industry": "#8a5a1a",
    "Policy": "#8f2d2d",
    "Funding": "#1a6b7a",
}


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def _story_block(index: int, story: dict) -> str:
    color = CATEGORY_COLORS.get(story["category"], "#41474d")
    return f"""
      <tr>
        <td style="padding:0 32px 4px 32px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                 style="border-top:1px solid #e3e6ea;">
            <tr><td style="height:24px;"></td></tr>
            <tr>
              <td>
                <span style="display:inline-block;font:600 10px/1 -apple-system,
                             'Segoe UI',Helvetica,Arial,sans-serif;letter-spacing:.09em;
                             text-transform:uppercase;color:{color};
                             border:1px solid {color};border-radius:3px;padding:5px 8px;">
                  {_esc(story['category'])}
                </span>
                <span style="font:400 12px/1 -apple-system,'Segoe UI',Helvetica,Arial,
                             sans-serif;color:#8b9299;padding-left:10px;">
                  {_esc(story['source'])}
                </span>
              </td>
            </tr>
            <tr>
              <td style="padding-top:12px;">
                <a href="{_esc(story['url'])}"
                   style="font:600 19px/1.35 Georgia,'Times New Roman',serif;
                          color:#15202b;text-decoration:none;">
                  {index}. {_esc(story['title'])}
                </a>
              </td>
            </tr>
            <tr>
              <td style="padding-top:10px;font:400 15px/1.65 -apple-system,'Segoe UI',
                         Helvetica,Arial,sans-serif;color:#3c444c;">
                {_esc(story['summary'])}
              </td>
            </tr>
            <tr>
              <td style="padding-top:12px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                  <tr>
                    <td style="border-left:3px solid #d5dae0;padding:2px 0 2px 12px;
                               font:400 14px/1.6 -apple-system,'Segoe UI',Helvetica,Arial,
                               sans-serif;color:#5a626b;">
                      <strong style="color:#3c444c;">Why it matters:</strong>
                      {_esc(story['why_it_matters'])}
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding-top:12px;padding-bottom:24px;">
                <a href="{_esc(story['url'])}"
                   style="font:600 13px/1 -apple-system,'Segoe UI',Helvetica,Arial,
                          sans-serif;color:#1a4d8f;text-decoration:none;">
                  Read the full story &rsaquo;
                </a>
              </td>
            </tr>
          </table>
        </td>
      </tr>"""


def build_html(digest: dict, now: datetime) -> str:
    date_line = now.strftime("%A, %d %B %Y")
    stories_html = "".join(
        _story_block(i, s) for i, s in enumerate(digest["stories"], start=1)
    )
    overview = _esc(digest.get("headline_summary", ""))
    overview_block = (
        f"""
      <tr>
        <td style="padding:28px 32px 4px 32px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                 style="background:#f4f6f8;border-radius:6px;">
            <tr>
              <td style="padding:20px 22px;">
                <div style="font:600 11px/1 -apple-system,'Segoe UI',Helvetica,Arial,
                            sans-serif;letter-spacing:.1em;text-transform:uppercase;
                            color:#6b737b;padding-bottom:10px;">
                  Today in brief
                </div>
                <div style="font:400 15px/1.7 -apple-system,'Segoe UI',Helvetica,Arial,
                            sans-serif;color:#2c333a;">{overview}</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>"""
        if overview
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Daily Brief</title>
</head>
<body style="margin:0;padding:0;background:#eceff2;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;">
    {len(digest['stories'])} developments in AI from the last 24 hours.
  </div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="background:#eceff2;padding:28px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="640" cellpadding="0" cellspacing="0"
               style="max-width:640px;width:100%;background:#ffffff;border-radius:8px;
                      overflow:hidden;box-shadow:0 1px 3px rgba(21,32,43,.09);">
          <tr>
            <td style="background:#15202b;padding:30px 32px;">
              <div style="font:700 23px/1.2 Georgia,'Times New Roman',serif;
                          color:#ffffff;letter-spacing:-.2px;">
                AI Daily Brief
              </div>
              <div style="font:400 13px/1.5 -apple-system,'Segoe UI',Helvetica,Arial,
                          sans-serif;color:#9aa6b2;padding-top:7px;">
                {date_line} &nbsp;&middot;&nbsp; {len(digest['stories'])} stories
              </div>
            </td>
          </tr>
          {overview_block}
          <tr><td style="height:12px;"></td></tr>
          {stories_html}
          <tr>
            <td style="background:#f4f6f8;padding:22px 32px;border-top:1px solid #e3e6ea;
                       font:400 12px/1.6 -apple-system,'Segoe UI',Helvetica,Arial,
                       sans-serif;color:#7b838b;">
              Compiled automatically from live web sources via Tavily and summarized
              with Groq. Summaries are machine-generated &mdash; verify details against
              the linked source before acting on them.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def build_plaintext(digest: dict, now: datetime) -> str:
    lines = [
        "AI DAILY BRIEF",
        now.strftime("%A, %d %B %Y"),
        "=" * 58,
        "",
    ]
    if digest.get("headline_summary"):
        lines += ["TODAY IN BRIEF", digest["headline_summary"], "", "-" * 58, ""]

    for i, s in enumerate(digest["stories"], start=1):
        lines += [
            f"{i}. [{s['category']}] {s['title']}",
            f"   Source: {s['source']}",
            "",
            f"   {s['summary']}",
            "",
            f"   Why it matters: {s['why_it_matters']}",
            f"   {s['url']}",
            "",
            "-" * 58,
            "",
        ]

    lines.append(
        "Compiled automatically via Tavily and summarized with Groq. "
        "Verify details against the linked source."
    )
    return "\n".join(lines)


def send_digest(digest: dict, now: datetime) -> None:
    subject = f"AI Daily Brief — {now.strftime('%d %b %Y')}"
    if digest["stories"]:
        subject += f" — {digest['stories'][0]['title'][:60]}"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((config.SENDER_NAME, config.SMTP_USER))
    message["To"] = ", ".join(config.RECIPIENTS)
    message.set_content(build_plaintext(digest, now))
    message.add_alternative(build_html(digest, now), subtype="html")

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.send_message(message)

    log.info("Digest emailed to %s", ", ".join(config.RECIPIENTS))
