import discord
import aiohttp
from redbot.core import commands, Config, checks

BASE_URL = "https://api.modrinth.com/v2/project/"

class ModrinthTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_global(tracked_projects={})

    @commands.group()
    @checks.admin()
    async def modrinth(self, ctx):
        pass

    @modrinth.command()
    async def add(self, ctx, project_id: str, channel: discord.TextChannel):
        tracked_projects = await self.config.tracked_projects()
        if project_id in tracked_projects:
            await ctx.send("This project is already being tracked.")
            return

        tracked_projects[project_id] = {"channel": channel.id, "latest_version": None}
        await self.config.tracked_projects.set(tracked_projects)
        await ctx.send(f"Tracking project `{project_id}` in {channel.mention}.")

    @modrinth.command()
    async def remove(self, ctx, project_id: str):
        tracked_projects = await self.config.tracked_projects()
        if project_id not in tracked_projects:
            await ctx.send("This project is not being tracked.")
            return

        del tracked_projects[project_id]
        await self.config.tracked_projects.set(tracked_projects)
        await ctx.send(f"Stopped tracking project `{project_id}`.")

    async def check_updates(self):
        async with aiohttp.ClientSession() as session:
            tracked_projects = await self.config.tracked_projects()
            for project_id, data in tracked_projects.items():
                url = BASE_URL + project_id
                async with session.get(url) as response:
                    if response.status != 200:
                        continue

                    project_data = await response.json()
                    latest_version = project_data.get("latest_version")
                    if not latest_version or latest_version == data.get("latest_version"):
                        continue

                    channel = self.bot.get_channel(data["channel"])
                    if channel:
                        await channel.send(f"New update for `{project_data['title']}`: `{latest_version}`\n{project_data['id']}")

                    tracked_projects[project_id]["latest_version"] = latest_version

            await self.config.tracked_projects.set(tracked_projects)

    @commands.Cog.listener()
    async def on_ready(self):
        while True:
            await self.check_updates()
            await discord.utils.sleep_until(discord.utils.utcnow().replace(second=0, microsecond=0) + timedelta(minutes=5))

async def setup(bot):
    cog = ModrinthTracker(bot)
    bot.add_cog(cog)
