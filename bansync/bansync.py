import asyncio
import logging
from datetime import datetime

import discord
from redbot.core import commands

log = logging.getLogger("red.pcxcogs.bansync")

class BanSync(commands.Cog):
    """Automatically sync moderation actions across servers."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def import_existing_bans(self) -> None:
        """Import existing bans into every server with BanSync enabled."""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            try:
                bans = await guild.bans()
                for ban_entry in bans:
                    user = ban_entry.user
                    log.info(f"Importing ban for {user} from {guild.name}")
                    await self._sync_ban_to_other_servers(guild, user)
            except discord.Forbidden:
                log.warning(f"Missing permissions to fetch bans in {guild.name}")
            except discord.HTTPException as e:
                log.error(f"Failed to fetch bans in {guild.name}: {e}")

    async def _sync_ban_to_other_servers(self, source_guild: discord.Guild, user: discord.User) -> None:
        """Sync a ban to other servers that have BanSync enabled."""
        for guild in self.bot.guilds:
            if guild.id != source_guild.id:
                try:
                    await guild.ban(user, reason=f"BanSync: Imported from {source_guild.name}")
                    log.info(f"Applied ban for {user} in {guild.name} from {source_guild.name}")
                except discord.Forbidden:
                    log.warning(f"Missing permissions to ban {user} in {guild.name}")
                except discord.HTTPException as e:
                    log.error(f"Failed to ban {user} in {guild.name}: {e}")

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def importbans(self, ctx: commands.Context) -> None:
        """Manually trigger the import of existing bans."""
        await ctx.send("Starting ban import...")
        await self.import_existing_bans()
        await ctx.send("Ban import completed.")
