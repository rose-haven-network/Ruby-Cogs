from .modrinthtracker import ModrinthTracker

async def setup(bot):
    await bot.add_cog(ModrinthTracker(bot))
