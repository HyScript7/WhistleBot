import discord
from discord.ext import commands


class Administration(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping", usage=".ping", description="Sends pong or your specified message"
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def commandName(self, ctx: commands.Context, msg: str = None):
        await ctx.send("Pong" if not msg else msg, ephemeral=True)

    @commands.hybrid_group(
        name="whitelist",
        usage="whitelist ( list | ( add | remove  [session_id] [max_sessions] ) <name> )",
        description="Adds a new user to the whitelist",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def whitelist(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.reply(
                "Please provide a valid sub command: `add`, `remove`, `list`",
                ephemeral=True,
            )
            return

    @whitelist.command("list")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def whitelist_list(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        whitelisted = list(self.bot.wl_store.get_whitelist().list_users().keys())
        embed = discord.Embed(
            title=self.bot.wl_brand + " - Whitelist",
            description="({}) Whitelisted: {}".format(
                len(whitelisted), "\n- ".join([""] + whitelisted)
            ),
            color=0xFFFFFF,
        )
        await ctx.reply(embed=embed, ephemeral=True)

    @whitelist.command("add")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def whitelist_add(
        self,
        ctx: commands.Context,
        username: str,
        pretty: str = None,
        max_sessions: int = 1,
        session_id: discord.Member = None,
    ):
        await ctx.defer(ephemeral=True)
        pretty = pretty if pretty else username
        username = username.lower().replace(" ", "")
        white_list = self.bot.wl_store.get_whitelist()
        default_session = [session_id.id] if session_id else []
        default_session_is_taken = bool(
            False
            if len(default_session) == 0
            else white_list.get_session(default_session[0])
        )
        username_is_taken = white_list.get_user(username)
        error = (
            "Username is already whitelisted!"
            if username_is_taken
            else "The specified session_id already has a whitelist username assigned!"
        )
        if username_is_taken or default_session_is_taken:
            embed = discord.Embed(
                title=self.bot.wl_brand + " - Whitelist Add",
                description="Could not add {} to the whtielist!\n```diff\n- {} -\n```".format(
                    username, error
                ),
                color=0xFFFFFF,
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return
        white_list.add_user(username, pretty, max_sessions, default_session)
        user = white_list.get_user(username)
        embed = discord.Embed(
            title=self.bot.wl_brand + " - Whitelist Add",
            description="Added {} to the whitelist!".format(username),
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
        await ctx.reply(embed=embed, ephemeral=True)

    @whitelist.command("remove")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def whitelist_remove(
        self,
        ctx: commands.Context,
        username: str,
    ):
        await ctx.defer(ephemeral=True)
        username = username.lower().replace(" ", "")
        white_list = self.bot.wl_store.get_whitelist()
        username_is_taken = white_list.get_user(username)
        if not username_is_taken:
            embed = discord.Embed(
                title=self.bot.wl_brand + " - Whitelist Remove",
                description="Could not remove {} from the whtielist!\n```diff\n- There is no such whitelisted username -\n```".format(
                    username
                ),
                color=0xFFFFFF,
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return
        white_list.remove_user(username)
        embed = discord.Embed(
            title=self.bot.wl_brand + " - Whitelist Remove",
            description="Removed {} from the whitelist!".format(username),
            color=0xFFFFFF,
        )
        await ctx.reply(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="evict", usage=".evict", description="Clears someone elses session"
    )
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def session_term(self, ctx: commands.Context, target: discord.Member):
        white_list = self.bot.wl_store.get_whitelist()
        session = white_list.get_session(target.id)
        if session is None:
            await ctx.reply(
                f"{target.metnion} does not have any sessions!", ephemeral=True
            )
            return
        white_list.get_user(session).drop_session(target.id)
        await ctx.reply(f"Sessions cleared for {target.mention}", ephemeral=True)
        try:
            await target.edit(nick=None)
        except Exception as e:
            await ctx.reply(
                f"I could not change {target.mention}'s displayname!",
                ephemeral=True,
                delete_after=5.0,
            )

    @commands.hybrid_group(
        name="roles",
        usage=".roles ( sync [username] | ( link | unlink <username> <role> ) )",
        description="Links roles to whitelist usernames",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def roles(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.reply(
                "Please provide a valid sub command: `link`, `unlink`, `sync`",
                ephemeral=True,
            )
            return

    @roles.command(
        name="link",
        usage=".roles link <username> <role>",
        description="Links a role to an account",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def roles_link(
        self, ctx: commands.Context, username: str, role: discord.Role
    ):
        await ctx.defer(ephemeral=True)
        white_list = self.bot.wl_store.get_whitelist()
        user = white_list.get_user(username)
        if user is None:
            await ctx.reply("Username does not exist", ephemeral=True)
            return
        user.roles.append(role.id)
        await ctx.reply(
            f"Successfully linked {role.mention} to {user.username}!", ephemeral=True
        )

    @roles.command(
        name="unlink",
        usage=".roles unlink <username> <role>",
        description="Unlinks a role from an account",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def roles_unlink(
        self, ctx: commands.Context, username: str, role: discord.Role
    ):
        await ctx.defer(ephemeral=True)
        white_list = self.bot.wl_store.get_whitelist()
        user = white_list.get_user(username)
        if user is None:
            await ctx.reply("Username does not exist", ephemeral=True)
            return
        if role.id in user.roles:
            user.roles.remove(role.id)
            await ctx.reply(
                f"Successfully unlinked {role.mention} from {user.username}!",
                ephemeral=True,
            )
            return
        await ctx.reply(
            f"Failed: {role.mention} is not linked to {user.username}!", ephemeral=True
        )

    @roles.command(
        name="sync",
        usage=".roles sync [username]",
        description="Makes sure the specific account(s) have their linked roles attached to users.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def roles_sync(self, ctx: commands.Context, username: str = None):
        await ctx.defer(ephemeral=True)
        white_list = self.bot.wl_store.get_whitelist()
        if username:
            user = white_list.get_user(username)
            if user is None:
                await ctx.reply("Username does not exist", ephemeral=True)
                return
            users = [user]
        else:
            users = white_list.get_users().values()
        for user in users:
            roles = [ctx.guild.get_role(roleid) for roleid in user.roles]
            for member_id in user.list_sessions():
                member = await ctx.guild.fetch_member(member_id)
                await member.add_roles(*roles)
        if username:
            await ctx.reply(
                f"Synced all sessions of {user.username}!",
                ephemeral=True,
            )
        else:
            await ctx.reply(
                f"Synced all sessions of all whitelisted usernames!",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Administration(bot))
