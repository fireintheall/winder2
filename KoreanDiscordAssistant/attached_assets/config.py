import os

# Bot configuration
PREFIX = os.environ.get("BOT_PREFIX", "!")

# Environment settings
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# Discord related configuration
GUILD_ID = os.environ.get("GUILD_ID")  # Optional: For guild-specific command registration
