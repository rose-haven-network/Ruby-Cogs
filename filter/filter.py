import discord
import json
import re
from redbot.core import commands, Config
import asyncio

class FilterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
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
            offenseExpireMinutes=60,
            offenses={}
        )

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog has been loaded.")

    async def send_log(self, log_channel_id, message):
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            embed = discord.Embed(title="Log", description=message, color=0x00ff00)
            await log_channel.send(embed=embed)
        else:
            print(f"Log channel {log_channel_id} not found.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot and not await self.config.deleteFromBots():
            return

        if message.channel.type == discord.ChannelType.private and await self.config.ignorePrivateMessages():
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

            if config["muteAfterOffense"]:
                async with self.config.offenses() as offenses:
                    if message.author.id not in offenses:
                        offenses[message.author.id] = 0
                    offenses[message.author.id] += 1

                    if offenses[message.author.id] >= config["muteAfterOffenseNumber"]:
                        if message.guild:
                            muted_role = discord.utils.get(message.guild.roles, name="Muted")
                            if muted_role:
                                await message.author.add_roles(muted_role)
                                await asyncio.sleep(config["muteAfterOffenseMinutes"] * 60)
                                await message.author.remove_roles(muted_role)
                                offenses[message.author.id] = 0

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

    @commands.command()
    async def addphrase(self, ctx, *, phrase: str):
        async with self.config.phrases() as phrases:
            phrases.append(phrase)
        await ctx.send(f"Added `{phrase}` to the filter list.")

    @commands.command()
    async def removephrase(self, ctx, *, phrase: str):
        async with self.config.phrases() as phrases:
            if phrase in phrases:
                phrases.remove(phrase)
                await ctx.send(f"Removed `{phrase}` from the filter list.")
            else:
                await ctx.send(f"`{phrase}` was not found in the filter list.")

    @commands.command()
    async def addstandaloneword(self, ctx, *, word: str):
        async with self.config.standAloneWords() as standalone_words:
            standalone_words.append(word)
        await ctx.send(f"Added `{word}` to the standalone words filter list.")

    @commands.command()
    async def removestandaloneword(self, ctx, *, word: str):
        async with self.config.standAloneWords() as standalone_words:
            if word in standalone_words:
                standalone_words.remove(word)
                await ctx.send(f"Removed `{word}` from the standalone words filter list.")
            else:
                await ctx.send(f"`{word}` was not found in the standalone words filter list.")

    @commands.command()
    async def settargetchannel(self, ctx, channel: discord.TextChannel):
        await self.config.targetChannelId.set(channel.id)
        await ctx.send(f"Target channel set to {channel.mention}.")

    @commands.command()
    async def setlogchannel(self, ctx, channel: discord.TextChannel):
        await self.config.logChannelId.set(channel.id)
        await ctx.send(f"Log channel set to {channel.mention}.")

async def setup(bot):
    await bot.add_cog(FilterCog(bot))
