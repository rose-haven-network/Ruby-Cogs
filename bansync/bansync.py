import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core import Config

class BanSync(commands.Cog):
    """A cog for syncing bans across multiple servers."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {
            "sync_bans": True,
            "ban_list": []
        }
        self.config.register_guild(**default_guild)

    async def initialize(self):
        """Optional initialization if needed"""
        pass  # Add setup logic if required

    @commands.command()
    @commands.admin_or_permissions(ban_members=True)
    async def baninfo(self, ctx: commands.Context, user_id: int):
        """Get information about a banned user."""
        try:
            ban_list = await ctx.guild.bans()
            for entry in ban_list:
                if entry.user.id == user_id:
                    await ctx.send(f"🔨 User `{entry.user}` is banned for: {entry.reason or 'No reason provided.'}")
                    return
            await ctx.send("✅ User is not banned.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to view the ban list.")
        except Exception as e:
            await ctx.send(f"⚠ An error occurred: {e}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Sync bans across all servers when a user is banned."""
        sync_enabled = await self.config.guild(guild).sync_bans()
        if not sync_enabled:
            return
        
        reason = None
        try:
            ban_entry = await guild.fetch_ban(user)
            reason = ban_entry.reason
        except discord.NotFound:
            pass  # If ban details can't be fetched, continue without a reason

        for g in self.bot.guilds:
            if g != guild and g.me.guild_permissions.ban_members:
                try:
                    await g.ban(user, reason=f"Synced Ban: {reason or 'No reason provided.'}")
                    await self.config.guild(g).ban_list.set(await self.config.guild(g).ban_list() + [user.id])
                except discord.Forbidden:
                    continue  # Skip if bot lacks permissions
                except Exception as e:
                    print(f"Error banning {user} in {g.name}: {e}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Sync unbans across all servers when a user is unbanned."""
        sync_enabled = await self.config.guild(guild).sync_bans()
        if not sync_enabled:
            return

        for g in self.bot.guilds:
            if g != guild and g.me.guild_permissions.ban_members:
                try:
                    await g.unban(user, reason="Synced Unban")
                    async with self.config.guild(g).ban_list() as ban_list:
                        if user.id in ban_list:
                            ban_list.remove(user.id)
                except discord.Forbidden:
                    continue  # Skip if bot lacks permissions
                except Exception as e:
                    print(f"Error unbanning {user} in {g.name}: {e}")

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(administrator=True)
    async def syncbans(self, ctx: commands.Context, enabled: bool):
        """Enable or disable automatic ban syncing."""
        await self.config.guild(ctx.guild).sync_bans.set(enabled)
        status = "enabled" if enabled else "disabled"
        await ctx.send(f"🔄 Ban sync has been {status} for this server.")

async def setup(bot: Red):
    """Setup function for the cog."""
    cog = BanSync(bot)
    await cog.initialize()
    bot.add_cog(cog)
