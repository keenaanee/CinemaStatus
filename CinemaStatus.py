import os
import sys
import time
import discord

def get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"ERROR: Required environment variable '{name}' is not set.")
        sys.exit(1)
    return value

# ====== CONFIG FROM ENVIRONMENT ======
TOKEN = get_required_env("DISCORD_TOKEN")
TARGET_USER_ID = int(get_required_env("TARGET_USER_ID"))          # e.g. 123456789012345678
CINEMA_CHANNEL_ID = int(get_required_env("CINEMA_CHANNEL_ID"))    # e.g. 234567890123456789
BASE_CHANNEL_NAME = os.environ.get("BASE_CHANNEL_NAME", "🎬 Cinema")
RENAME_COOLDOWN = int(os.environ.get("RENAME_COOLDOWN", "30"))    # seconds between renames
# =====================================

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.guilds = True

class CinemaBot(discord.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_channel_name = None
        self.last_rename_ts = 0
        self.rename_cooldown = RENAME_COOLDOWN

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"Watching user ID: {TARGET_USER_ID}")
        print(f"Cinema channel ID: {CINEMA_CHANNEL_ID}")
        print(f"Base channel name: {BASE_CHANNEL_NAME}")
        print(f"Rename cooldown: {self.rename_cooldown} seconds")

    async def on_presence_update(self, before, after):
        # Only care about the configured user
        if after.id != TARGET_USER_ID:
            return

        guild = after.guild
        if guild is None:
            return

        channel = guild.get_channel(CINEMA_CHANNEL_ID)
        if channel is None:
            print("Cinema channel not found.")
            return

        # DEBUG: show activities (remove or comment out if noisy)
        for act in after.activities:
            print(
                "ACTIVITY:",
                "name=", getattr(act, "name", None),
                "type=", getattr(act, "type", None),
                "details=", getattr(act, "details", None),
                "state=", getattr(act, "state", None),
            )

        # Find the non-streaming activity (ignore screen share / Go Live)
        movie_activity = None
        for act in after.activities:
            if act.type == discord.ActivityType.streaming:
                continue

            # If you want to be strict, uncomment and set your RP name, e.g. "Plex":
            # if act.name != "Plex":
            #     continue

            movie_activity = act
            break

        # Decide the new channel name
        if movie_activity is not None:
            title = getattr(movie_activity, "details", None) or getattr(movie_activity, "state", None)
            if title:
                new_name = f"{BASE_CHANNEL_NAME} – {title[:50]}"
            else:
                new_name = BASE_CHANNEL_NAME
        else:
            new_name = BASE_CHANNEL_NAME

        now = time.time()

        if self.last_channel_name is None:
            self.last_channel_name = channel.name

        # Only rename if name changed AND cooldown passed
        if new_name != self.last_channel_name and (now - self.last_rename_ts) >= self.rename_cooldown:
            try:
                await channel.edit(name=new_name, reason="Update cinema name from Rich Presence")
                self.last_channel_name = new_name
                self.last_rename_ts = now
                print(f"Updated channel name to: {new_name}")
            except Exception as e:
                print(f"Failed to rename channel: {e}")
        else:
            # Uncomment if you want to see skipped events:
            # print("Skipping rename (no change or cooldown not elapsed)")
            pass

client = CinemaBot(intents=intents)
client.run(TOKEN)