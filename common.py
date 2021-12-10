"""
Reference:
- Discord.py API Reference: https://discordpy.readthedocs.io/en/latest/api.html#
- Get TOKEN of your bot: https://discord.com/developers/applications, select APP -> Bot -> reveal/create Token

"""
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import discord
import pandas as pd
from discord import (
    CategoryChannel,
    Guild,
    Member,
    PermissionOverwrite,
    Permissions,
    Role,
    TextChannel,
    VoiceChannel,
)
from discord.abc import GuildChannel

MY_TOKEN = open('token.txt', 'r').read()


class BasicClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print("Connected!")
        print("Username: {0.name}\nID: {0.id}".format(self.user))

    async def on_message(self, msg):
        """This callback is invoked EVERY TIME a member sends a message to this bot or in the server."""
        print(msg)


class CachedGuild(ABC):

    def __init__(self):
        super().__init__()
        self.roles: List[Role] = []
        self.members: List[Member] = []
        self.channels: List[GuildChannel] = []

    @abstractmethod
    async def get_guilds(self) -> List[Guild]:
        """"""

    async def manage_guilds(self):
        """Get list of members in the server. Then do custom statistics on it."""
        guilds = await self.get_guilds()
        for guild in guilds:
            if guild.name != self.GUILD:
                continue
            await self.manage_guild(guild)

    async def manage_guild(self, guild: Guild):
        """Dump to dataframe for later data analysis"""
        self.roles = await guild.fetch_roles()
        await self.manage_roles(self.roles)

        self.members = await guild.fetch_members(limit=3500).flatten()
        await self.manage_members(self.members)

        self.channels = await guild.fetch_channels()
        await self.manage_channels(self.channels)

    async def manage_members(self, members: List[Member]):
        pass

    async def manage_channels(self, channels: List[GuildChannel]):
        pass

    async def manage_roles(self, roles: List[Role]):
        pass

