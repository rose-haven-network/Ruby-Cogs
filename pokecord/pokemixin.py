from redbot.core import commands


@commands.group(name="poke")
async def poke(self, ctx: commands.Context):
    """
    Ava's Pokemon commands
    """


class PokeMixin:
    """This is mostly here to easily mess with things..."""

    c = poke
