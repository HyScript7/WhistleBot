import discord
from discord.ext import commands


class Example(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping", usage=".ping", description="Sends pong or your specified message"
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def commandName(self, ctx: commands.Context, msg: str = None):
        await ctx.send("Pong" if not msg else msg, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Example(bot))
