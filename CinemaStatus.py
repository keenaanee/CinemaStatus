import os
import sys
import time

import discord
from discord import Activity, ActivityType
from discord.ext import tasks
from plexapi.server import PlexServer


def get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"ERROR: Required environment variable '{name}' is not set.")
        sys.exit(1)
    return value


# ====== CONFIG FROM ENVIRONMENT ======

DISCORD_TOKEN = get_required_env("DISCORD_TOKEN")

PLEX_URL = get_required_env("PLEX_URL")
PLEX_TOKEN = get_required_env("PLEX_TOKEN")
TARGET_USER = os.environ.get("TARGET_USER")  # Plex username (optional)

CINEMA_CHANNEL_ID = int(get_required_env("CINEMA_CHANNEL_ID"))
BASE_CHANNEL_NAME = os.environ.get("BASE_CHANNEL_NAME", " Cinema")
RENAME_COOLDOWN = int(os.environ.get("RENAME_COOLDOWN", "300"))  # seconds

POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "30"))  # seconds

# =====================================

intents = discord.Intents.none()  # we only change our own presence and channels
intents.guilds = True  # needed to fetch/edit the voice channel


def build_activity_from_session(session):
    """
    Build a Discord Activity from a Plex session, mirroring Discord-Plex-DRPP logic.
    Returns (activity, channel_title, paused).
    channel_title is what we'll feed into the cinema channel name.
    """
    player_state = (
        getattr(session.player, "state", "playing")
        if hasattr(session, "player")
        else "playing"
    )
    paused = player_state != "playing"

    # Movie
    if session.type == "movie":
        year = f" ({session.year})" if getattr(session, "year", None) else ""
        details = f"{session.title}{year}"
        main_line = details
        state_text = details
        large = "movie"

    # TV episode
    elif session.type == "episode":
        show = getattr(session, "grandparentTitle", "Unknown Show")
        season = (
            f"S{session.parentIndex:02d}"
            if getattr(session, "parentIndex", None)
            else ""
        )
        ep = (
            f"E{session.index:02d}"
            if getattr(session, "index", None)
            else ""
        )
        details = f"{show} - {season}{ep}: {session.title}".lstrip(" -")
        main_line = show
        state_text = f"{season}{ep}: {session.title}".lstrip(": ")
        large = "tv"

    # Fallback for other media types
    else:
        details = getattr(session, "title", "Media")
        main_line = details
        state_text = session.type.capitalize()
        large = "plex"

    # Timestamps for elapsed/remaining
    timestamps = None
    if (
        not paused
        and getattr(session, "viewOffset", None) is not None
        and getattr(session, "duration", None) is not None
    ):
        elapsed = session.viewOffset / 1000
        duration = session.duration / 1000
        start = int(time.time() - elapsed)
        end = int(start + duration)
        timestamps = {"start": start, "end": end}

    activity = Activity(
        type=ActivityType.watching,
        name=main_line,  # main visible line (movie/show title or show name)
        details=details,
        state=state_text,
        large_image=large,
        large_text="Watching on Plex",
        small_image="paused" if paused else "playing",
        small_text=player_state.capitalize(),
        timestamps=timestamps,
    )

    # For the channel name, using "details" gives a nice human-readable title
    channel_title = details

    return activity, channel_title, paused


class CinemaBot(discord.Client):
    def __init__(self, plex: PlexServer, **kwargs):
        super().__init__(**kwargs)
        self.plex = plex
        self.plex_target_user = TARGET_USER

        self.last_channel_name = None
        self.last_rename_ts = 0
        self.rename_cooldown = RENAME_COOLDOWN

        self.cinema_channel = None

    async def setup_hook(self):
        # Start the Plex poll loop when the bot is ready
        self.poll_plex.start()

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"Plex URL: {PLEX_URL}")
        print(f"Plex target user: {self.plex_target_user or '(any)'}")
        print(f"Cinema channel ID: {CINEMA_CHANNEL_ID}")
        print(f"Base channel name: {BASE_CHANNEL_NAME}")
        print(f"Rename cooldown: {self.rename_cooldown} seconds")
        print(f"Poll interval: {POLL_INTERVAL} seconds")

        # Resolve the cinema channel once
        self.cinema_channel = None
        for guild in self.guilds:
            channel = guild.get_channel(CINEMA_CHANNEL_ID)
            if channel is not None:
                self.cinema_channel = channel
                break

        if self.cinema_channel is None:
            print("ERROR: Cinema channel not found in any guild.")

    @tasks.loop(seconds=POLL_INTERVAL)
    async def poll_plex(self):
        if self.cinema_channel is None:
            # Try to resolve the channel again if guilds changed
            for guild in self.guilds:
                channel = guild.get_channel(CINEMA_CHANNEL_ID)
                if channel is not None:
                    self.cinema_channel = channel
                    break
            if self.cinema_channel is None:
                print("Cinema channel still not found; skipping this poll.")
                return

        # Get sessions from Plex
        try:
            sessions = self.plex.sessions()
        except Exception as e:
            print(f"Error getting sessions from Plex: {e}")
            await self.change_presence(activity=None)
            await self._maybe_rename_channel(BASE_CHANNEL_NAME)
            return

        chosen_session = None
        for session in sessions:
            user = None

            # Try to get the username from different possible locations
            if hasattr(session, "user") and session.user and hasattr(session.user, "title"):
                user = session.user.title
            elif hasattr(session, "usernames") and session.usernames:
                user = session.usernames[0]

            if self.plex_target_user:
                if user == self.plex_target_user:
                    chosen_session = session
                    break
            else:
                # No explicit target; just take the first session
                chosen_session = session
                break

        if not chosen_session:
            # No matching/active sessions
            await self.change_presence(activity=None)
            await self._maybe_rename_channel(BASE_CHANNEL_NAME)
            print("No active Plex sessions; cleared presence and reset channel name.")
            return

        # Build Discord activity + channel title from the chosen Plex session
        activity, channel_title, paused = build_activity_from_session(chosen_session)

        # Update bot presence
        try:
            await self.change_presence(activity=activity)
        except Exception as e:
            print(f"Failed to update presence: {e}")

        # Update cinema channel name
        title_for_channel = channel_title or "Watching"
        new_name = f"{BASE_CHANNEL_NAME} – {title_for_channel[:50]}"
        await self._maybe_rename_channel(new_name)

        print(
            f"Updated presence and channel from Plex session "
            f"({chosen_session.type}, paused={paused}) -> '{new_name}'"
        )

    async def _maybe_rename_channel(self, new_name: str):
        now = time.time()

        if self.last_channel_name is None:
            self.last_channel_name = self.cinema_channel.name

        if (
            new_name != self.last_channel_name
            and (now - self.last_rename_ts) >= self.rename_cooldown
        ):
            try:
                await self.cinema_channel.edit(
                    name=new_name,
                    reason="Update cinema name from Plex session",
                )
                self.last_channel_name = new_name
                self.last_rename_ts = now
                print(f"Updated channel name to: {new_name}")
            except Exception as e:
                print(f"Failed to rename channel: {e}")
        # else: cooldown not elapsed or name unchanged; do nothing


# Instantiate Plex and bot, then run
plex_server = PlexServer(PLEX_URL, PLEX_TOKEN)
client = CinemaBot(plex=plex_server, intents=intents)
client.run(DISCORD_TOKEN)
