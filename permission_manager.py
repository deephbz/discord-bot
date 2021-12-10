"""
This module implements GuildManagerClient providing convenient role, channel permission management.
You could use it for backup / restore in batch.

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

from common import CachedGuild, BasicClient

MY_TOKEN = open('token.txt', 'r').read()


class GuildManager(CachedGuild):
    GUILD = "Real-UnknownDAO"  # discord server name
    SHALL_DUMP_MEMBER_STAT: bool = False

    PROTECT_CHANNEL_AGAINST_ROLE_IDS = [
        916307111963672597,  # builder
        916524340835672095,  # ACAT
        916492369715666985,  # DAOer
    ]
    def __init__(self, dry_run: bool) -> None:
        super().__init__()
        self.dry_run = dry_run

    async def manage_members(self, members: List[Member]):
        print("Manage all members:")
        print(f"{len(members)} members in {members[0].guild.name}!")
        self.my_cached_members = members

    async def manage_channels(self, channels: List[GuildChannel]):
        print("Manage all channels:")
        channels = sorted(channels, key=lambda c: c.position)
        for c in channels:
            if isinstance(c, CategoryChannel):
                print("=" * 20 + f"Category {c.name}" + "=" * 30)
            elif isinstance(c, (TextChannel, VoiceChannel)):
                print(f"Channel {c.name}")
                if not self.dry_run:
                    await self.set_channel_permission(c)
            else:
                print("=" * 20 + f"{type(c)} {c.name}" + "=" * 30)

    async def manage_roles(self, roles: List[Role]):
        print("Manage all roles:")
        self.role_id_to_role = {}
        for role in roles:
            print(f"{role.name:16s} \t {role.id:25d} \t {bin(role.permissions.value)}")
            self.role_id_to_role[role.id] = role

    async def set_channel_permission(self, c: GuildChannel) -> None:
        for role, perm in c.overwrites:
            print(f"{role.name}, {perm}")
        for role in c.changed_roles:
            print("changed role", role)
        for rid in self.PROTECT_CHANNEL_AGAINST_ROLE_IDS:
            role = self.role_id_to_role[rid]
            overwrite = c.overwrites_for(role)
            allow, deny = overwrite.pair()

            overwrite.manage_channels = False
            overwrite.manage_permissions = False
            overwrite.manage_threads = False
            if not self.dry_run:
                await c.set_permissions(role, overwrite=overwrite)
            print(f"overwrites_for {role.name}: ", bin(allow.value), bin(deny.value))
            print(
                overwrite.manage_channels,
                overwrite.manage_permissions,
                overwrite.view_channel,
            )


class GuildManagerClient(BasicClient, GuildManager):
    """Multi-inhert from BasicClient and GuildManager to separate concerns: 
        Permission management and Discord connection.

    """
    def __init__(self, *args, dry_run: bool = True, **kwargs):
        BasicClient.__init__(self, *args, **kwargs)
        GuildManager.__init__(self, dry_run=dry_run)

    async def on_ready(self):
        await super(GuildManagerClient, self).on_ready()
        await self.manage_guilds()

    async def get_guilds(self) -> List[Guild]:
        """"""
        return await self.fetch_guilds(limit=150).flatten()


def main():
    loop = asyncio.get_event_loop()
    if loop.is_running():  # in notebook
        client_loop = loop
        print(client_loop)
    else:
        client_loop = None

    intents = discord.Intents.default()
    intents.members = True
    client = GuildManagerClient(loop=client_loop, intents=intents, dry_run=True)

    client.run(MY_TOKEN)


if __name__ == "__main__":
    main()
