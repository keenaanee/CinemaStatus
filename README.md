![2](https://repository-images.githubusercontent.com/1096099312/03ae624f-f171-4de1-8abf-0758b6865b4f)

# Plex Discord Rich Presence Bot

Small Discord bot that sets its own Rich Presence based on what a Plex user is
currently watching and renames a Discord voice channel (your “cinema” channel)
based on that same Plex activity. Designed for setups where you want a Discord
account to show the movie or TV episode playing on your Plex server
(e.g. a “KeeCinema”-style cinema account).

## Pull from DockerHub

Rich Presence + cinema channel rename (CinemaStatus):

[![Docker Pulls](https://img.shields.io/docker/pulls/keenaanee/cinemastatus)](https://hub.docker.com/r/keenaanee/cinemastatus)

## What it does

### Plex → Discord Rich Presence

- Connects to your Plex server via URL and token.
- Watches active Plex sessions and optionally filters to a single Plex username.
- Updates the Discord bot’s Rich Presence with:
  - Movie title and year, or
  - TV show name, season/episode code, and episode title.
- Shows play/pause status (via the small icon and text).
- Optionally includes timestamps so Discord shows the remaining time.
- Runs as a simple, lightweight polling bot inside Docker.

### Plex → Rich Presence + cinema channel

- Renames a chosen Discord voice channel (your “cinema” channel).
- Uses the same Plex data as Rich Presence (movie or episode title).
- Applies a configurable base name (for example `🎬 Cinema`) and appends the current title.
- Uses a configurable cooldown between renames to avoid API spam.

## Requirements

- A Plex server you can reach from the container (URL + token).
- Docker (Unraid, Linux, etc.) or plain Python if you prefer running without Docker.
- A Discord bot with:
  - Permission to edit the chosen voice channel’s name in the Discord server.

## Configuration (environment variables)

All configuration is done via environment variables:

- `PLEX_URL` (required)  
  Your Plex server URL, including port.  
  Example: `http://192.168.x.x:32400`
  
- `PLEX_TOKEN` (required)  
  Your Plex API token.

- `TARGET_USER` (optional)  
  Plex username to track. If set, the bot only uses sessions from this user.  
  If left empty, it will fall back to “any active session”.

- `DISCORD_TOKEN` (required)  
  Discord bot token.

- `CINEMA_CHANNEL_ID` (required)  
  Discord voice channel ID to rename (numeric ID).

- `BASE_CHANNEL_NAME` (optional, default `🎬 Cinema`)  
  Base name of the cinema channel.  
  The bot appends the current media title to this.

- `RENAME_COOLDOWN` (optional, default `300`)  
  Seconds between channel renames.

- `POLL_INTERVAL` (optional, default `30`)  
  Seconds between Plex polls.

You can use an `.env` file or pass these directly as `-e` flags.

## Running this bot with Docker

### Build (optional, if you want your own image)

```bash
docker build -t your-docker-user/cinemastatus-plex .

### Run
```bash
docker run -d \
  --name cinemastatus-plex \
  -e DISCORD_TOKEN="your-discord-bot-token" \
  -e PLEX_URL="http://192.168.x.x:32400" \
  -e PLEX_TOKEN="your-plex-token" \
  -e TARGET_USER="YourPlexUsername" \
  -e CINEMA_CHANNEL_ID="123456789012345678" \
  -e BASE_CHANNEL_NAME="🎬 Cinema" \
  -e RENAME_COOLDOWN="300" \
  -e POLL_INTERVAL="30" \
  --restart unless-stopped \
  keenaanee/cinemastatus
```

### Logs
```bash
docker logs -f kee-cinema-bot
```

::contentReference[oaicite:0]{index=0}



