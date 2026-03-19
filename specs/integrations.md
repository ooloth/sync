# Integrations

External services and their authentication patterns. All secrets are stored in 1Password (vault: "Scripts") and retrieved via `io/op/secrets.py`.

## YouTube Data API v3

- **Docs**: https://developers.google.com/youtube/v3/docs
- **Scope**: `youtube.readonly`
- **Auth**: OAuth 2.0 with a hybrid token strategy
  - **Fast path**: Cached access token on disk (`.secrets/oauth_access_token.json`, ~1 hour validity)
  - **Refresh path**: Refresh token stored in 1Password → exchanges for new access token
  - **Full OAuth**: Browser flow when refresh token is invalid; user manually updates 1Password afterward
- **1Password items**: `YouTube API` → fields: `oauth_client_secrets.json`, `oauth_refresh_token`
- **Client library**: `google-api-python-client` with `google-auth-oauthlib`
- **Used by**: sync-subs (list subscriptions), sync-likes (list liked videos)

### API operations

| Operation | Method | Pagination |
|-----------|--------|------------|
| List subscriptions | `subscriptions.list(mine=True)` | Yes, 50/page via `list_next()` |
| List liked videos | Not yet implemented | — |

## Feedbin API

- **Docs**: https://github.com/feedbin/feedbin-api
- **Base URL**: `https://api.feedbin.com/v2`
- **Auth**: HTTP Basic (username + password)
- **1Password items**: `Feedbin API` → fields: `username`, `password`
- **Client library**: httpx
- **Used by**: sync-subs

### API operations

| Operation | Endpoint | Notes |
|-----------|----------|-------|
| List subscriptions | `GET /subscriptions.json` | Returns all subscriptions |
| Create subscription | `POST /subscriptions.json` | Body: `{"feed_url": "..."}` |

## Pushover

- **Docs**: https://pushover.net/api
- **Base URL**: `https://api.pushover.net/1`
- **Auth**: App token + user key (sent in request body)
- **1Password items**: `Pushover` → fields: `app_token`, `user_key`
- **Client library**: httpx
- **Used by**: Not yet integrated into jobs (available for notifications)

### API operations

| Operation | Endpoint | Notes |
|-----------|----------|-------|
| Send message | `POST /messages.json` | Supports title, HTML formatting |

## 1Password

- **Docs**: https://developer.1password.com/docs/cli/secret-reference-syntax/
- **Vault**: `Scripts`
- **Auth**: CLI biometric (local) or `OP_SERVICE_ACCOUNT_TOKEN` (CI)
- **Access pattern**: `op read op://Scripts/{item}/{field}`
- **Caching**: `@lru_cache` on `get_secret()` — each (item, field) pair fetched once per run

## Notion (planned)

- **Docs**: https://developers.notion.com/
- **Auth**: Bearer token (integration token)
- **Intended use**: Store liked YouTube videos in a Notion database
- **Will need**: `io/notion/` adapter (auth, client, models, tests)
- **1Password item**: TBD

## SQLite (planned)

- **Intended use**: Local state tracking (e.g., last sync timestamp, processed video IDs) to avoid redundant API calls
- **Will need**: `io/sqlite/` adapter
- **Storage location**: Likely `.data/` directory (gitignored)
