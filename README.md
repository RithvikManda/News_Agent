# AI Daily Brief

A scheduled job that pulls the last 24 hours of AI news from Tavily, has Groq
write an editorial summary of each story, and emails a formatted digest at
09:00 IST every day.

```
Tavily (5 themed searches)  ->  dedupe + rank  ->  Groq (structured JSON)
                                                      |
                                       HTML + plaintext email  ->  SMTP
```

## Files

| Path | Purpose |
|---|---|
| `main.py` | Entrypoint: once, dry-run, or long-running scheduler |
| `src/config.py` | All settings and env-var loading |
| `src/fetcher.py` | Tavily search, dedup, domain filtering |
| `src/summarizer.py` | Groq call, JSON parsing, link reattachment |
| `src/emailer.py` | HTML + plaintext rendering, SMTP send |
| `.github/workflows/daily-digest.yml` | Free daily scheduling on GitHub Actions |

## Setup

**1. Install**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Get the two API keys (both free)**

- Tavily: sign up at `tavily.com`, copy the `tvly-...` key. Free tier is 1,000
  credits/month; this job uses about 5 per day.
- Groq: sign up at `console.groq.com`, create a key (`gsk_...`). Free tier is
  rate-limited per minute and per day, well above what one daily run needs.

**3. Set up the sending mailbox**

Use a personal Gmail as the sender — do not try to send *from* the Invesco
address, since corporate SMTP is usually locked down.

1. Turn on 2-Step Verification on the Google account.
2. Go to Google Account → Security → App passwords.
3. Generate one, copy the 16-character string.
4. That string is `SMTP_PASSWORD`. Your Gmail address is `SMTP_USER`.

**4. Configure**

```bash
cp .env.example .env
```

Fill in `.env`. It is gitignored — never commit it.

**5. Test before scheduling anything**

```bash
python main.py --dry-run     # builds preview.html, sends nothing
python main.py               # real run, sends the email
```

Open `preview.html` in a browser to check the layout.

## Scheduling

### Option A — GitHub Actions (recommended, free, no machine left on)

1. Push this folder to a **private** GitHub repo.
2. Repo → Settings → Secrets and variables → Actions → New repository secret.
   Add one for each: `TAVILY_API_KEY`, `GROQ_API_KEY`, `SMTP_HOST`,
   `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `RECIPIENTS`.
3. Done. The workflow fires at 03:30 UTC = 09:00 IST.
4. Actions tab → "AI Daily Brief" → *Run workflow* to test immediately.

Two caveats worth knowing: GitHub's scheduler can lag 5–20 minutes under load,
and it disables cron on repos with no commits for 60 days.

### Option B — your own machine

```bash
python main.py --schedule    # blocks; fires at 09:00 daily
```

The process must stay alive. For a laptop that sleeps, a real cron entry is
better:

```cron
0 9 * * * cd /path/to/ai-news-digest && .venv/bin/python main.py >> run.log 2>&1
```

Windows: Task Scheduler → Create Task → Daily at 9:00 AM → Action: start
`.venv\Scripts\python.exe` with argument `main.py`, "Start in" set to the
project folder.

## Tuning

Everything below is in `.env` or `src/config.py`:

- `SEARCH_QUERIES` — the five themed searches. Add or swap them to change
  coverage (e.g. drop the policy query, add one for a specific domain).
- `LOOKBACK_DAYS` — set to `2` if a daily window feels too thin on weekends.
- `MAX_STORIES_IN_EMAIL` — 10 by default; 5–6 makes for a faster read.
- `RECIPIENTS` — comma-separated for multiple addresses.
- `GROQ_MODEL` — if a model ID gets deprecated the code automatically falls
  back through the list in `config.py`, so a 404 is not fatal.
- `SYSTEM_PROMPT` in `summarizer.py` — the editorial voice. This is the single
  highest-leverage thing to edit if the tone isn't right.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `SMTPAuthenticationError` | Using the account password instead of an App Password, or 2FA is off |
| Email lands in spam | Normal for a new sender. Mark "not spam" once, or add the sender to contacts |
| "No stories returned" | Tavily credits exhausted, or `LOOKBACK_DAYS=1` on a quiet day — raise it |
| `All Groq models failed` | Key invalid, or daily rate limit hit. Check `console.groq.com` |
| Actions run never fires | Repo inactive 60+ days, or cron disabled in Settings → Actions |

Summaries are machine-generated. The prompt forbids fabrication and every story
links back to its source, but treat the digest as a pointer to read further,
not as verified reporting.
