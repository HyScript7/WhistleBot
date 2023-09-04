import discord
from discord.ext import commands


class User(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="login",
        usage=".login <username>",
        description="Adds you to the session of the specified username.",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def session_set(self, ctx: commands.Context, username: str):
        await ctx.defer(ephemeral=True)
        white_list = self.bot.wl_store.get_whitelist()
        session = white_list.get_session(ctx.author.id)
        if session is not None:
            await ctx.reply("You already have a session!", ephemeral=True)
            return
        username = username.lower().replace(" ", "")
        user = white_list.get_user(username)
        if user is None:
            await ctx.reply("Username does not exist", ephemeral=True)
            return
        try:
            user.create_session(ctx.author.id)
        except Exception as e:
            await ctx.reply(
                "This username cannot have any more sessions!", ephemeral=True
            )
            return
        await ctx.reply(f"Logged in as {user.pretty}", ephemeral=True)
        try:
            await ctx.author.edit(nick=user.pretty)
        except Exception as e:
            await ctx.reply(
                f"I could not change your displayname!",
                ephemeral=True,
                delete_after=5.0,
            )

    @commands.hybrid_command(
        name="logout", usage=".logout", description="Clears your sessions"
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def session_clear(self, ctx: commands.Context):
        white_list = self.bot.wl_store.get_whitelist()
        session = white_list.get_session(ctx.author.id)
        if session is None:
            await ctx.reply("You do not have any sessions!", ephemeral=True)
            return
        white_list.get_user(session).drop_session(ctx.author.id)
        await ctx.reply("Sessions cleared", ephemeral=True)
        try:
            await ctx.author.edit(nick=None)
        except Exception as e:
            await ctx.reply(
                f"I could not change your displayname!",
                ephemeral=True,
                delete_after=5.0,
            )

    @commands.hybrid_command(
        name="whois",
        usage=".whois <username>",
        description="Shows information about a whitelisted user.",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def session_set(self, ctx: commands.Context, username: str):
        await ctx.defer(ephemeral=True)
        white_list = self.bot.wl_store.get_whitelist()
        username = username.lower().replace(" ", "")
        user = white_list.get_user(username)
        if user is None:
            await ctx.reply("Username does not exist", ephemeral=True)
            return
        embed = discord.Embed(
            title=self.bot.wl_brand + " - Whitelist WhoIS",
            description="Showing information about {}".format(username),
            color=0xFFFFFF,
        )
        embed.add_field(
            name="Session Limit", value=user.get_session_limit(), inline=True
        )
        embed.add_field(
            name="Sessions",
            value="\n- ".join([""] + [f"<@{id}>" for id in user.list_sessions()]),
            inline=True,
        )
        embed.add_field(
            name="Displayname",
            value=user.pretty,
            inline=False,
        )
        await ctx.reply(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(User(bot))
