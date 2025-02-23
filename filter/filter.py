import discord
import json
import sqlite3
from redbot.core import commands, Config

class FilterStorage:
    def __init__(self):
        self.conn = sqlite3.connect("filter_storage.db")
        self.cursor = self.conn.cursor()
        self._setup()
    
    def _setup(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS filter_data (
            guild_id INTEGER,
            key TEXT,
            value TEXT,
            PRIMARY KEY (guild_id, key)
        )
        """)
        self.conn.commit()
    
    def get(self, guild_id, key):
        self.cursor.execute("SELECT value FROM filter_data WHERE guild_id = ? AND key = ?", (guild_id, key))
        result = self.cursor.fetchone()
        return json.loads(result[0]) if result else []
    
    def add(self, guild_id, key, value):
        data = self.get(guild_id, key)
        if value not in data:
            data.append(value)
            self.cursor.execute("REPLACE INTO filter_data (guild_id, key, value) VALUES (?, ?, ?)", (guild_id, key, json.dumps(data)))
            self.conn.commit()
            return True
        return False
    
    def remove(self, guild_id, key, value):
        data = self.get(guild_id, key)
        if value in data:
            data.remove(value)
            self.cursor.execute("REPLACE INTO filter_data (guild_id, key, value) VALUES (?, ?, ?)", (guild_id, key, json.dumps(data)))
            self.conn.commit()
            return True
        return False
    
    def clear(self, guild_id, key):
        self.cursor.execute("DELETE FROM filter_data WHERE guild_id = ? AND key = ?", (guild_id, key))
        self.conn.commit()

class FilterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.storage = FilterStorage()
        self.config.register_guild(
            logFiltered=True,
            logChannelId=None,
            ignorePrivateMessages=False,
            caseSensitive=False,
            muteCommand=False,
            tellPlayer=True,
            censorAndSend=False,
            muteAfterOffense=False,
            muteAfterOffenseType="TEMPORARY",
            muteAfterOffenseMinutes=5,
            muteAfterOffenseNumber=3,
            offenseExpireMinutes=30,
            offenses=[],
            deleteFromBots=False,
            deleteFromWebhooks=False,
            restrictToChannel=None,
            notifyOnDelete=True
        )

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog has been loaded.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot and not await self.config.deleteFromBots():
            return
        
        if message.webhook_id and not await self.config.deleteFromWebhooks():
            return
        
        if isinstance(message.channel, discord.DMChannel) and await self.config.ignorePrivateMessages():
            return
        
        restrict_channel = await self.config.restrictToChannel()
        if restrict_channel and message.channel.id != restrict_channel:
            return
        
        words = self.storage.get(message.guild.id, "words")
        case_sensitive = await self.config.caseSensitive()
        message_content = message.content if case_sensitive else message.content.lower()
        
        for word in words:
            word_check = word if case_sensitive else word.lower()
            if word_check in message_content:
                try:
                    await message.delete()
                    if await self.config.notifyOnDelete():
                        embed = discord.Embed(title="Message Deleted", description=f"Your message was deleted because it contained a filtered word: `{word}`", color=discord.Color.red())
                        await message.author.send(embed=embed)
                    log_channel_id = await self.config.logChannelId()
                    if log_channel_id:
                        log_channel = message.guild.get_channel(log_channel_id)
                        if log_channel:
                            log_embed = discord.Embed(title="Filtered Message", description=f"Deleted a message from {message.author.mention} containing a filtered word: `{word}`", color=discord.Color.red())
                            await log_channel.send(embed=log_embed)
                    return
                except discord.Forbidden:
                    await message.channel.send("I don't have permission to delete messages.", delete_after=5)
                except discord.HTTPException:
                    print("Failed to delete message due to an HTTP error")

    @commands.hybrid_group()
    async def filter(self, ctx):
        """Manage the filter system."""
        await ctx.send_help(ctx.command)

    @filter.command(name="addword")
    async def addword(self, ctx, word: str):
        """Add a word to the filter list."""
        if self.storage.add(ctx.guild.id, "words", word):
            await ctx.send(f"Added `{word}` to the filter list.")
        else:
            await ctx.send(f"`{word}` is already in the filter list.")

    @filter.command(name="removeword")
    async def removeword(self, ctx, word: str):
        """Remove a word from the filter list."""
        if self.storage.remove(ctx.guild.id, "words", word):
            await ctx.send(f"Removed `{word}` from the filter list.")
        else:
            await ctx.send(f"`{word}` was not found in the filter list.")

    @filter.command(name="listwords")
    async def listwords(self, ctx):
        """List all words in the filter."""
        words = self.storage.get(ctx.guild.id, "words")
        await ctx.send(f"Filtered words: {', '.join(words) if words else 'None'}")

    @filter.command(name="clearwords")
    async def clearwords(self, ctx):
        """Clear all words from the filter list."""
        self.storage.clear(ctx.guild.id, "words")
        await ctx.send("All filtered words have been cleared.")

    @filter.command(name="setlogchannel")
    async def setlogchannel(self, ctx, channel: discord.TextChannel):
        """Set the logging channel."""
        await self.config.logChannelId.set(channel.id)
        await ctx.send(f"Log channel set to {channel.mention}")

    @filter.command(name="listautomodrules")
    async def listautomodrules(self, ctx):
        """List all AutoMod rules in the server."""
        guild = ctx.guild
        if guild:
            rules = await guild.fetch_automod_rules()
            rule_names = [rule.name for rule in rules]
            await ctx.send(f"AutoMod Rules: {', '.join(rule_names) if rule_names else 'None'}")
        else:
            await ctx.send("This command must be used in a server.")

async def setup(bot):
    await bot.add_cog(FilterCog(bot))
