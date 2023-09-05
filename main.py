import asyncio

import discord
from discord.ext import commands

from whistle_config import wl_brand, wl_token
from whistle_store import WLSTORE_FILENAME, wlStore


class wlBot(commands.Bot):
    wl_version: str = "v1.0.0"
    wl_brand: str = wl_brand
    wl_store: wlStore
    __wl_store_autosaver: asyncio.Task

    def __init__(
        self,
        command_prefix: str = ".",
        intents: discord.Intents = discord.Intents.all(),
    ):
        super().__init__(command_prefix, intents=intents)
        self.wl_store = wlStore(WLSTORE_FILENAME)

    async def on_ready(self):
        # Announce our user
        print(f"Logged in as {self.user}")
        # Run wlStore Auto Saver
        print("Running wlStore Autosaver...", end="\r")
        self.__wl_store_autosaver = asyncio.get_event_loop().create_task(
            self.wl_store.autosaver(), name="wlStore Autosaver"
        )
        print("Running wlStore Autosaver...DONE!")
        # Wait until we're ready
        print("Waiting for client...", end="\r")
        await self.wait_until_ready()
        print("Waiting for client...DONE!")
        # Sync our command tree
        print("Syncing commands...", end="\r")
        await self.tree.sync()
        print("Syncing commands...DONE!")
        # Set our presence status
        print("Setting activity...", end="\r")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name=f"the whitelist"
            )
        )
        print("Setting activity...DONE!")
        # Announce we're ready
        print("Ready!")

    async def load_modules(self):
        modules = ["admin", "session"]
        print("Loading modules, please wait.")
        for i in modules:
            print(f"Loading module {i}...", end="\r")
            try:
                await self.load_extension(f"modules.{i}")
                print(f"Loading module {i}...OK")
            except Exception as e:
                print(
                    f"Loading module {i}...ERROR\nCould not load module {i} because it raised an exception: {e}"
                )
        print("Modules loaded! Read above for more details.")


bot = wlBot()

asyncio.run(bot.load_modules())
bot.run(wl_token)
