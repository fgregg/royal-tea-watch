# royal-tea-watch

Polls <https://www.theroyaleagle.net/royal-tea> every ~15 min from a GitHub
Actions cron and pushes an [ntfy.sh](https://ntfy.sh) notification when:

- a new event date appears,
- an event date disappears, or
- a date flips between **Sold Out** and **Available**.

Reservations open ~1 month in advance and sell out fast, so the goal is to
catch a new June/July date the moment it shows up.

## Subscribe on your phone

1. Install the ntfy app: <https://ntfy.sh/app> (iOS / Android).
2. Add subscription to topic: **`royal-tea-fgregg-7k2pq9`**.
3. Test from your laptop:
   ```bash
   curl -d "hello from cli" https://ntfy.sh/royal-tea-fgregg-7k2pq9
   ```

The topic is public-but-unguessable; anyone who knows the string can read or
publish to it. If you ever want a new one, change it in both
`.github/workflows/watch.yml` and your phone subscription.

## How it works

`check.py` fetches the page (plain GET; the event grid is server-rendered),
extracts each `royal-tea-time-YYYY-MM-DD-HH-MM` slug, and attributes the
adjacent "Sold Out" ribbon to its slug by matching the rendered date label
(e.g. "Tue, Jun 09") back to the slug's month/day.

State (`state.json`) is committed back to the repo each time anything changes,
so you also get a free audit trail in the git log.

## Run / disable

- Manual trigger: Actions → "watch" → "Run workflow".
- Disable: Actions → "watch" → "..." → "Disable workflow", or delete the repo.

## Why public

Public repos get unlimited GitHub Actions minutes. The state and HTML are
already public anyway.
