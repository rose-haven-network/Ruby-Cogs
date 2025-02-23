import discord
import json
import io
from redbot.core import commands, Config

class FilterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_global(
            regexes=[],
            phrases=[],
            words=[],
            standAloneWords=[],
            replacementChars=[],
            mutedPlayers=[],
            tempMutedPlayers=[],
            ignoredPlayers=[],
            logFiltered=True,
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

    @commands.hybrid_command()
    async def addword(self, ctx, word: str):
        """Add a word to the filter list."""
        async with self.config.words() as words:
            words.append(word)
        await ctx.send(f"Added `{word}` to the filter list.")

    @commands.hybrid_command()
    async def removeword(self, ctx, word: str):
        """Remove a word from the filter list."""
        async with self.config.words() as words:
            if word in words:
                words.remove(word)
                await ctx.send(f"Removed `{word}` from the filter list.")
            else:
                await ctx.send(f"`{word}` was not found in the filter list.")

    @commands.hybrid_command()
    async def listwords(self, ctx):
        """List all words in the filter."""
        words = await self.config.words()
        await ctx.send(f"Filtered words: {', '.join(words) if words else 'None'}")

    @commands.hybrid_command()
    async def clearwords(self, ctx):
        """Clear all words from the filter list."""
        await self.config.words.set([])
        await ctx.send("All filtered words have been cleared.")

    @commands.hybrid_command()
    async def importconfig(self, ctx, file: discord.Attachment):
        """Import a config file."""
        if file.filename.endswith(".json"):
            try:
                data = await file.read()
                config_data = json.loads(data.decode("utf-8"))
                async with self.config.all() as config:
                    for key in config.keys():
                        if key in config_data:
                            config[key] = config_data[key]
                await ctx.send("Config imported successfully.")
            except Exception as e:
                await ctx.send(f"Failed to import config: {str(e)}")
        else:
            await ctx.send("Please upload a JSON file.")

    @commands.hybrid_command()
    async def exportconfig(self, ctx):
        """Export the current config as a JSON file."""
        config_data = await self.config.all()
        file = discord.File(io.BytesIO(json.dumps(config_data, indent=4).encode()), filename="config.json")
        await ctx.send("Here is the current configuration:", file=file)

    @commands.hybrid_command()
    async def togglelogging(self, ctx):
        """Toggle logging on or off."""
        current = await self.config.logFiltered()
        await self.config.logFiltered.set(not current)
        await ctx.send(f"Logging is now {'enabled' if not current else 'disabled'}.")

    @commands.hybrid_command()
    async def setmuteoffense(self, ctx, number: int):
        """Set the number of offenses before muting a user."""
        await self.config.muteAfterOffenseNumber.set(number)
        await ctx.send(f"Users will now be muted after {number} offenses.")

    @commands.hybrid_command()
    async def listautomodrules(self, ctx):
        """List all AutoMod rules in the server."""
        guild = ctx.guild
        if guild:
            rules = await guild.automod_rules()
            rule_names = [rule.name for rule in rules]
            await ctx.send(f"AutoMod Rules: {', '.join(rule_names) if rule_names else 'None'}")
        else:
            await ctx.send("This command must be used in a server.")

async def setup(bot):
    await bot.add_cog(FilterCog(bot))
