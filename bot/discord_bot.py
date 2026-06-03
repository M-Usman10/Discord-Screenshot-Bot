import logging

import discord
from discord import app_commands

from bot.webhook import capture_and_post_all

log = logging.getLogger(__name__)


class ScreenshotBot(discord.Client):
    def __init__(self, cfg: dict) -> None:
        super().__init__(intents=discord.Intents.default())
        self.cfg = cfg
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        @self.tree.command(
            name="screenshot",
            description="Capture configured windows and post to Discord",
        )
        async def screenshot_cmd(interaction: discord.Interaction) -> None:
            await interaction.response.defer(thinking=True)
            results = await interaction.client.loop.run_in_executor(
                None,
                lambda: capture_and_post_all(self.cfg, source="/screenshot command"),
            )
            await interaction.followup.send(
                "\n".join(results) if results else "No windows configured."
            )

        guild_id = self.cfg.get("command_guild_id")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info("Slash commands synced to guild %s", guild_id)
        else:
            await self.tree.sync()
            log.info("Slash commands synced globally (may take up to 1 hour)")

    async def on_ready(self) -> None:
        log.info("Bot logged in as %s (id=%d)", self.user, self.user.id)
