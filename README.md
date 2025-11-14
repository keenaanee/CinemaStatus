# Discord Cinema Status Bot

Small Discord bot that renames a voice channel based on a user's Rich Presence
(e.g. Plex Rich Presence). Designed for "cinema" setups where one account
screen-shares Plex into a voice channel.

## Pull from DockerHub

[![Docker Pulls](https://img.shields.io/docker/pulls/keenaanee/cinema-status)](https://hub.docker.com/r/keenaanee/cinema-status)

## What it does

- Watches a single Discord user (your cinema account).
- Whenever that user has a non-streaming Rich Presence activity (e.g. Plex
  "Watching: Movie Name"), the bot renames a voice channel to:

  `BASE_CHANNEL_NAME – Movie Name`

- When the activity disappears, it resets the channel name back to
  `BASE_CHANNEL_NAME`.
- Rate-limited with a configurable cooldown so it doesn't spam the Discord API.

## Requirements

- A Discord bot with:
  - Presence Intent enabled
  - Server Members Intent enabled
  - Permission to manage channels in your server
- A user whose Rich Presence shows what they're watching (e.g. Plex Rich Presence).
- Docker (Unraid, Linux, etc.) or plain Python.

## Configuration (environment variables)

All configuration is done via environment variables:

- `DISCORD_TOKEN` (required)  
  Your bot token from the Discord Developer Portal.

- `TARGET_USER_ID` (required)  
  The Discord user ID to watch (e.g. your "KeeCinema" account).

- `CINEMA_CHANNEL_ID` (required)  
  The voice channel ID to rename.

- `BASE_CHANNEL_NAME` (optional, default: `🎬 Cinema`)  
  The base name for the channel. The bot will append `– Movie Title`.

- `RENAME_COOLDOWN` (optional, default: `300`)  
  Minimum number of seconds between renames. This helps avoid rate limits.
  Example: `300` = 5 minutes.

See `.env.example` for a sample.

## Running with Docker

### Build

```bash
docker build -t kee-cinema-bot .
```

### Run
```bash
docker run -d \
  --name kee-cinema-bot \
  -e DISCORD_TOKEN="their-token" \
  -e TARGET_USER_ID="their-user-id" \
  -e CINEMA_CHANNEL_ID="their-channel-id" \
  -e BASE_CHANNEL_NAME="🎬 Cinema" \
  -e RENAME_COOLDOWN="300" \
  --restart unless-stopped \
  kee-cinema-bot
```

### Logs
```bash
docker logs -f kee-cinema-bot


```

