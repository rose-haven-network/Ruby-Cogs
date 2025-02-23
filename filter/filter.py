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
            guild_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (guild_id, key, value)
        )
        """)
        self.conn.commit()
    
    def get(self, guild_id, key):
        self.cursor.execute("SELECT value FROM filter_data WHERE guild_id = ? AND key = ?", (guild_id, key))
        result = self.cursor.fetchall()
        return [json.loads(row[0]) for row in result] if result else []
    
    def add(self, guild_id, key, value):
        if value not in self.get(guild_id, key):
            self.cursor.execute("INSERT INTO filter_data (guild_id, key, value) VALUES (?, ?, ?)", (guild_id, key, json.dumps(value)))
            self.conn.commit()
            return True
        return False
    
    def remove(self, guild_id, key, value):
        if value in self.get(guild_id, key):
            self.cursor.execute("DELETE FROM filter_data WHERE guild_id = ? AND key = ? AND value = ?", (guild_id, key, json.dumps(value)))
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

    @commands.hybrid_command()
    async def importconfig(self, ctx, json_data: str):
        """Import a configuration from a JSON string."""
        try:
            config_data = json.loads(json_data)
            await self.config.guild(ctx.guild).set(config_data)
            await ctx.send("Configuration imported successfully.")
        except json.JSONDecodeError:
            await ctx.send("Invalid JSON format.")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog has been loaded.")

async def setup(bot):
    await bot.add_cog(FilterCog(bot))
