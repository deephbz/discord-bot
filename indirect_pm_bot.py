"""
This module implements IndirectMessageClient which helps transfer users' msgs anonymously.

- Discord.py API Reference: https://discordpy.readthedocs.io/en/latest/api.html#
- Get TOKEN of your bot: https://discord.com/developers/applications, select APP -> Bot -> reveal/create Token

"""
import asyncio
import json
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
import pickle
from typing import Dict, List, Optional, Union, Tuple

import discord
import pandas as pd
from discord import Guild, Message, Member, TextChannel, Thread, DMChannel

from common import CachedGuild, BasicClient

MY_TOKEN = open('token.txt', 'r').read()


class FormatError(Exception):
    """"""


class IndirectMessager(CachedGuild):
    """
    - React to pm in format "IndirectMsg|<target_user_id>|<msg>"

    """
    GUILD = 916300758834630666  # "Real-UnknownDAO"  # discord server name
    DELIMITER = '|'
    START = "IndirectMsg" + DELIMITER

    def __init__(self) -> None:
        super().__init__(target_guild_id=self.GUILD)

    async def on_message(self, msg: Message):
        """This callback is invoked EVERY TIME a member sends a message to this bot or in the server."""
        if msg.author == self.user:  # skip self to avoid recursion
            return
        if not isinstance(msg.channel, DMChannel):
            print('guild msg', msg.content, type(msg.channel))
            return

        await self.on_dm(msg)

    async def on_dm(self, msg: Message):
        await msg.channel.send('Your DM well received, thinking...')
        content = msg.content
        if content.startswith(self.START):
            await self.on_indirect_msg_command(msg)

    async def on_indirect_msg_command(self, msg: Message):
        command_arg = msg.content[len(self.START):]
        try:
            target_user_id, msg_to_send = self._extract_info(command_arg, self.DELIMITER)
        except FormatError as e:
            await msg.channel.send(str(e))
            return
            
        the_dst_member = [
            m for m in self.members 
            if (isinstance(target_user_id, int) and m.id == target_user_id) 
                or (isinstance(target_user_id, str) and str(m) == target_user_id)
        ]
        if not the_dst_member:
            await msg.channel.send(f"{target_user_id} not found in GUILD {self.GUILD}")
            return
        the_dst_member = the_dst_member[0]
        await the_dst_member.send(msg_to_send)
        await msg.channel.send(f"Successfully sent to {target_user_id}: \"{msg_to_send}\"")

    @staticmethod
    def _extract_info(s: str, delimiter: str) -> Tuple[int, str]:
        tokens = s.split(delimiter)
        if len(tokens) < 2:
            raise FormatError(f"less than 2 parts after splitted by {delimiter}: {s}")
        first, *rest = tokens
        if '#' in first:  # user_name#xxxx
            target_user_id = first
        else:  # user_id
            try:
                target_user_id = int(first)
            except Exception as e:
                raise FormatError(f"Cannot convert {first} to int user ID, errror: {str(e)}")
        msg_to_send = delimiter.join(rest)
        return target_user_id, msg_to_send


class IndirectMessageClient(BasicClient, IndirectMessager):
    """Multi-inhert from BasicClient and GuildManager to separate concerns: 
        Permission management and Discord connection.

    """
    def __init__(self, *args, dry_run: bool = True, **kwargs):
        BasicClient.__init__(self, *args, **kwargs)
        IndirectMessager.__init__(self)

    async def on_ready(self):
        await BasicClient.on_ready(self)
        await self.manage_guilds()

    async def get_guilds(self) -> List[Guild]:
        """"""
        return await self.fetch_guilds(limit=150).flatten()

    async def on_message(self, msg):
        await BasicClient.on_message(self, msg)
        await IndirectMessager.on_message(self, msg)


def main():
    loop = asyncio.get_event_loop()
    if loop.is_running():  # in notebook
        client_loop = loop
        print(client_loop)
    else:
        client_loop = None

    intents = discord.Intents.default()
    intents.members = True
    intents.dm_messages = True

    client = IndirectMessageClient(loop=client_loop, intents=intents)

    client.run(MY_TOKEN)


if __name__ == "__main__":
    main()

