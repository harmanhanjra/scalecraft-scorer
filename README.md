# scalecraft-scorer

Score small-business leads 0-100 on how likely they need a website or
automation work, from a plain CSV. Part of the ScaleCraft lead pipeline:
**hunter** (clean raw lists) → **scorer** (rank them) → **outreach** (draft emails).

Offline, stdlib-only, single file.

## Signals

- No website listed → +25 (prime client)
- Social page instead of a real site → +15
- Dated TLD (.info/.biz/.net) → +10
- Free email provider (gmail etc.) → -8
- Already pays for custom-domain email → -10
- Pain keywords in notes ("outdated", "manual", "paper", ...) → +15

Baseline 50, clamped to 0-100, output sorted best-first with reasons per lead.

## Usage

```
python scalecraft-scorer.py --in leads.csv
python scalecraft-scorer.py --in leads.csv --min-score 60 --out hot.json
```

Input: CSV or JSON with columns `name, city, website, phone, email, notes`.

## Tests

```
python -m unittest test_scorer
```

MIT
