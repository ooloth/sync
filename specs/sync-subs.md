# Sync Subscriptions

Keeps Feedbin RSS subscriptions in sync with YouTube channel subscriptions.

## Why

YouTube's subscription feed is unreliable — it misses uploads and doesn't support filtering. Feedbin provides a better reading experience for YouTube content via RSS. This job ensures every YouTube subscription has a corresponding Feedbin RSS subscription.

## How it works

1. Fetch all YouTube subscriptions (paginated, 50 per page)
2. Fetch all Feedbin subscriptions
3. Build YouTube RSS feed URLs from channel IDs: `https://www.youtube.com/feeds/videos.xml?channel_id={id}`
4. Compute the set difference: YouTube feeds not yet in Feedbin
5. Create missing subscriptions in Feedbin (or log what would be created in dry-run mode)

## CLI interface

```
python -m youtube_sync.jobs.sync_subs [--apply] [--verbose]
```

| Flag | Default | Effect |
|------|---------|--------|
| (none) | — | Dry-run mode: logs what would be created, makes no changes |
| `--apply` | off | Actually creates subscriptions in Feedbin |
| `--verbose` / `-v` | off | Shows DEBUG-level output |

Convenience commands in `justfile`:
- `just sync-subs` — dry run
- `just sync-subs-apply` — apply changes
- `just sync-subs-verbose` — dry run with debug output

## Current behavior

- One-directional: adds missing feeds to Feedbin, never removes
- Channel name resolution: maps each feed URL back to a channel name for readable log output
- Logs summary: total YouTube feeds, total Feedbin feeds, feeds to create

## Future considerations

- **Remove stale subscriptions**: Unsubscribe from Feedbin feeds for channels no longer subscribed on YouTube
- **Pushover notifications**: Send a summary notification when sync completes (especially useful for scheduled runs)
- **Scheduled execution**: Run on a cron schedule (GitHub Actions or local cron)
- **Idempotency tracking**: Use SQLite to track sync state and avoid redundant API calls
