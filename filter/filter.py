import discord
import json
import re
from redbot.core import commands, Config

class FilterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(
            phrases=[],
            words=[],
            standAloneWords=[],
            targetChannelId=None,
            logChannelId=None,
            deleteFromBots=False,
            deleteFromUsers=True,
            targetChannelOnly=False,
            logFiltered=False,
            ignorePrivateMessages=True,
            caseSensitive=False,
            muteAfterOffense=False,
            muteAfterOffenseType="mute",
            muteAfterOffenseMinutes=10,
            muteAfterOffenseNumber=3,
            offenseExpireMinutes=60
        )

    async def send_log(self, log_channel_id, message):
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            embed = discord.Embed(title="Log", description=message, color=0x00ff00)
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        config = await self.config.all()
        
        if config["targetChannelOnly"] and message.channel.id != config["targetChannelId"]:
            return

        triggers = config["phrases"] + config["words"]
        standalone_triggers = [rf"\b{word}\b" for word in config["standAloneWords"]]

        if any(trigger.lower() in message.content.lower() for trigger in triggers) or \
           any(re.search(trigger, message.content, re.IGNORECASE) for trigger in standalone_triggers):
            try:
                await message.delete()
                log_message = f"Deleted message from user **{message.author.name}** (ID: {message.author.id}) due to inappropriate content."
                await message.channel.send(f"{message.author.mention}, your message was removed due to inappropriate content.")
                if config["logFiltered"]:
                    await self.send_log(config["logChannelId"], log_message)
            except discord.errors.Forbidden:
                print("Missing permissions to delete messages.")

    @commands.command()
    async def addword(self, ctx, *, word: str):
        async with self.config.words() as words:
            words.append(word)
        await ctx.send(f"Added `{word}` to the filter list.")

    @commands.command()
    async def removeword(self, ctx, *, word: str):
        async with self.config.words() as words:
            if word in words:
                words.remove(word)
                await ctx.send(f"Removed `{word}` from the filter list.")
            else:
                await ctx.send(f"`{word}` was not found in the filter list.")

async def setup(bot):
    await bot.add_cog(FilterCog(bot))
