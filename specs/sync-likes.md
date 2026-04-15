# Sync Likes

Saves YouTube liked videos to a Notion database for later reference.

**Status**: Not yet implemented (stub exists at `jobs/sync_likes.py`).

## Why

YouTube's "Liked videos" playlist is a flat, unsearchable list. Syncing liked videos to Notion enables tagging, filtering, searching, and organizing saved content alongside other notes and references.

## Desired behavior

1. Fetch liked videos from YouTube API (using the authenticated user's liked videos playlist)
2. Check which videos already exist in the Notion database (by video URL or YouTube video ID)
3. Add new liked videos to Notion with metadata

### Data to capture per video

| Field      | Source      | Notes                              |
| ---------- | ----------- | ---------------------------------- |
| Title      | YouTube API | Video title                        |
| Channel    | YouTube API | Channel name                       |
| URL        | Constructed | `https://youtube.com/watch?v={id}` |
| Date liked | YouTube API | When the user liked the video      |
| Thumbnail  | YouTube API | Medium-resolution thumbnail URL    |

## CLI interface

```
python -m sync.jobs.sync_likes [--apply] [--verbose]
```

Should follow the same dry-run/apply pattern as sync-subs.

## Open questions

- **Notion database schema**: What properties/columns should the database have? How should they map to Notion property types (title, URL, date, etc.)?
- **Unliked videos**: Should videos that are unliked on YouTube be removed from Notion, or kept?
- **Pagination**: YouTube's liked videos list can be large. What's the right batch size and how should we handle rate limits?
- **Sync frequency**: How often should this run? Is there a way to detect only new likes since last sync?
- **Duplicate detection**: Match on video URL, YouTube video ID, or both?
- **OAuth scope**: The current YouTube scope is `youtube.readonly`, which should cover liked videos — confirm this.

## Implementation notes

- Will need a new `io/notion/` adapter following the standard pattern (auth, client, models, tests)
- Notion API uses bearer token authentication
- May benefit from SQLite for tracking sync state (last sync timestamp, processed video IDs)
