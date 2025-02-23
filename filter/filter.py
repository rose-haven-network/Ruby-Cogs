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
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        self.conn.commit()
    
    def get(self, key):
        self.cursor.execute("SELECT value FROM filter_data WHERE key = ?", (key,))
        result = self.cursor.fetchone()
        return json.loads(result[0]) if result else []
    
    def add(self, key, value):
        data = self.get(key)
        if value not in data:
            data.append(value)
            self.cursor.execute("REPLACE INTO filter_data (key, value) VALUES (?, ?)", (key, json.dumps(data)))
            self.conn.commit()
    
    def remove(self, key, value):
        data = self.get(key)
        if value in data:
            data.remove(value)
            self.cursor.execute("REPLACE INTO filter_data (key, value) VALUES (?, ?)", (key, json.dumps(data)))
            self.conn.commit()
    
    def clear(self, key):
        self.cursor.execute("DELETE FROM filter_data WHERE key = ?", (key,))
        self.conn.commit()

class FilterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.storage = FilterStorage()
        self.config.register_global(
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
        )

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog has been loaded.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if isinstance(message.channel, discord.DMChannel) and await self.config.ignorePrivateMessages():
            return
        
        words = self.storage.get("words")
        case_sensitive = await self.config.caseSensitive()
        message_content = message.content if case_sensitive else message.content.lower()
        
        for word in words:
            word_check = word if case_sensitive else word.lower()
            if word_check in message_content:
                try:
                    await message.delete()
                    log_channel_id = await self.config.logChannelId()
                    if log_channel_id:
                        log_channel = message.guild.get_channel(log_channel_id)
                        if log_channel:
                            await log_channel.send(f"Deleted a message from {message.author.mention} containing a filtered word: `{word}`")
                    return
                except discord.Forbidden:
                    await message.channel.send("I don't have permission to delete messages.", delete_after=5)
                except discord.HTTPException:
                    print("Failed to delete message due to an HTTP error")

    @commands.hybrid_command()
    async def addword(self, ctx, word: str):
        """Add a word to the filter list."""
        self.storage.add("words", word)
        await ctx.send(f"Added `{word}` to the filter list.")

    @commands.hybrid_command()
    async def removeword(self, ctx, word: str):
        """Remove a word from the filter list."""
        self.storage.remove("words", word)
        await ctx.send(f"Removed `{word}` from the filter list.")

    @commands.hybrid_command()
    async def listwords(self, ctx):
        """List all words in the filter."""
        words = self.storage.get("words")
        await ctx.send(f"Filtered words: {', '.join(words) if words else 'None'}")

    @commands.hybrid_command()
    async def clearwords(self, ctx):
        """Clear all words from the filter list."""
        self.storage.clear("words")
        await ctx.send("All filtered words have been cleared.")

    @commands.hybrid_command()
    async def setlogchannel(self, ctx, channel: discord.TextChannel):
        """Set the logging channel."""
        await self.config.logChannelId.set(channel.id)
        await ctx.send(f"Log channel set to {channel.mention}")

    @commands.hybrid_command()
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
