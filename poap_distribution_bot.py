"""
This module implements HistoricalMsgAnalysisClient which helps you to analyze historical messages (in order to to retroactive airdrops); and POAPDistributorClient, which helps you to distribute POAP claim codes (or anything else) to white-listed users.

- Discord.py API Reference: https://discordpy.readthedocs.io/en/latest/api.html#
- Get TOKEN of your bot: https://discord.com/developers/applications, select APP -> Bot -> reveal/create Token

"""
import asyncio
import json
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
import pickle
from typing import Dict, List, Optional

import discord
import pandas as pd
from discord import Guild, Message, Member, TextChannel

from common import CachedGuild, BasicClient

MY_TOKEN = open('token.txt', 'r').read()

MEMBERS_TO_MENTION = ['some_discord_username#1234']  # hard-coded name list for convenience use
ClaimableT = Dict[str, str]  # project name to claim code URL


@dataclass
class POAPClaimingClientConfig:
    project_name_to_discord_username_to_url_json_paths: Dict[str, Path]


class POAPDistributor(CachedGuild):
    """
    - React to claim spells by PM claim code, then persist who has claimed using which code;
    - Mention all whitelisted users.

    """
    GUILD = 916300758834630666  # "Real-UnknownDAO"  # discord server name
    poap_issue_claim_tutorial_link = "https://unknown-dao.notion.site/POAP-Issue-Claim-Tutorial-1b07698a43914229a228e9dfe7020990"
    CLAIM_MAGIC_SPELLS = [
        'WhereIsMyPOAP',
    ]
    MEMBER_STAT_SPELL = "Check it out"
    ADMIN_DIS_NAME = "₿ingnan.ΞTH#0369"
    SHALL_DUMP_MEMBER_STAT: bool = False

    def __init__(self) -> None:
        super().__init__(target_guild_id=self.GUILD)
        self.cfg: Optional[POAPClaimingClientConfig] = None
        self.project_name_to_name_url_map: POAP = {}

    def set_config(self, cfg: POAPClaimingClientConfig):
        """Custom configurations"""
        self.cfg = cfg
        for (
            project_name,
            path,
        ) in self.cfg.project_name_to_discord_username_to_url_json_paths.items():
            self.project_name_to_name_url_map[project_name] = json.load(open(path, "r"))

    async def on_message(self, msg: Message):
        """This callback is invoked EVERY TIME a member sends a message to this bot or in the server."""
        if any(msg.content.startswith(spell) for spell in self.CLAIM_MAGIC_SPELLS):
            await self._on_claim_poap(msg)

        if str(msg.author) == self.ADMIN_DIS_NAME and msg.content.startswith(self.MEMBER_STAT_SPELL):
            await self._on_member_stat(msg)

    async def manage_members_post(self, members: List[Member]):
        """Get list of members in the server. Then do custom statistics on it."""
        return
        BOT_CID = 916538023909412916
        channel = [c for c in self.channels if c.id == BOT_CID][0]
        for project_name, id2url in self.project_name_to_name_url_map.items():
            whitelisted_members = [
                m for m in self.members
                if (str(m.id) in id2url) or (str(m) in id2url)
            ]
            if not whitelisted_members:
                print(f"No whitelisted_members for {project_name}")
                continue
            if project_name == 'WhatTheFork Event POAP':
                continue
            await self._mention_whitelist_members(
                whitelisted_members, channel, project_name
            )

    async def _mention_whitelist_members(
        self, members_to_mention: List[Member], channel: TextChannel, project_name: str,
    ):
        assert members_to_mention, "members_to_mention is empty!"
        msg = "\n".join(
            [
                "Hey~ ",
                " ".join([m.mention for m in members_to_mention]),
                f"You are in **whitelist** of {project_name}, send `{self.CLAIM_MAGIC_SPELLS[0]}` to claim here.",
                "Ignore if you've already done it."
            ]
        )
        await self.send_maybe_long_msg(msg, channel, delete_after=3600 * 8)  # delete the msg after 8 hours

    async def send_maybe_long_msg(self, msg: str, channel: TextChannel, *args, **kwargs) -> None:
        MAX_LEN = 1950  # 4000 actually
        chunk_idx = 0
        while chunk_idx * MAX_LEN < len(msg):
            msg_piece = msg[chunk_idx * MAX_LEN: (chunk_idx + 1) * MAX_LEN]
            chunk_idx += 1
            await channel.send(msg_piece, *args, **kwargs)  


    async def _on_claim_poap(self, msg: Message) -> None:
        """Check if a user is in white list and DM him URL if so."""
        poaps_to_claim = await self._get_poaps_to_claim(msg.author)
        if not poaps_to_claim:
            await msg.channel.send(
                f"😑 **{msg.author}** is not a valid user to claim.", delete_after=3600 * 24
            )
        else:
            await msg.author.send(self._format_private_msg(poaps_to_claim))
            await msg.channel.send(
                f"👍 Succeeded. **{msg.author}** please check your DM :)", delete_after=60
            )
            self.persist(poaps_to_claim)

    async def _get_poaps_to_claim(self, m: Member) -> ClaimableT:
        project_name_to_urls = {}
        for (
            project_name,
            discord_users_to_claim_url_map,
        ) in self.project_name_to_name_url_map.items():
            url = ''
            if str(m.id) in discord_users_to_claim_url_map:
                url = discord_users_to_claim_url_map[str(m.id)]
            elif str(m) in discord_users_to_claim_url_map:
                url = discord_users_to_claim_url_map[str(m)]

            if url:
                project_name_to_urls[project_name] = url
        return project_name_to_urls

    def persist(self, project_name_to_poap_url: ClaimableT) -> str:
        pass

    def _format_private_msg(self, project_name_to_poap_url: ClaimableT) -> str:
        return "\n".join(
            [
                f"Click URLs to claim your POAP."
                f"(If you are not familiar with it, please refer to <POAP Issue & Claim Tutorial> at {self.poap_issue_claim_tutorial_link})",
                "; ".join(
                    [
                        f"**{project_name}**: {url}"
                        for project_name, url in project_name_to_poap_url.items()
                    ]
                ),
            ]
        )


#     async def on_message_delete(self, message):
#         fmt = '{0.author} has deleted the message: {0.content}'
#         await message.channel.send(fmt.format(message))


class HistoricalMsgProcessor(CachedGuild):
    target_channel_id = 916306940517285939  # 🚀│频道建设讨论
    output_dir = Path('historical_msgs')

    async def manage_guild(self, guild: Guild):
        await super().manage_guild(guild)

        for c in self.channels:
            # channel = guild.get_channel(self.target_channel_id)
            if c.id == self.target_channel_id:
                channel = c

            if not isinstance(c, TextChannel):
                continue
            # await self.dump_channel_history(c)


    async def dump_channel_history(self, c: TextChannel):
        msgs: List[Message] = []
        async for m in c.history(limit=5000):
            # msgs.append(m)
            msgs.append({
                'channel': m.channel.name,
                'channel_id': m.channel.id,
                'content': m.content,
                'created_at': m.created_at,
                'author': m.author.name,
                'author_dis': m.author.discriminator,
                'author_id': m.author.id,
            })
        _out_fp = self.output_dir / str(c.id)
        pd.DataFrame(msgs).to_parquet(_out_fp)
        print(f'Dumped {c.name} to {_out_fp}')

    async def manage_members(self, members: List[Member]):
        dfs = []
        for m in members:
            dfs.append({
                'member': m.name,
                'member_dis': m.discriminator,
                'member_id': m.id,
                'joined_at': m.joined_at,
                'created_at': m.created_at,
                'is_bot': m.bot,
            })
        _out_fp = self.output_dir / 'members.parquet'
        pd.DataFrame(dfs).to_parquet(_out_fp)
        print(f'dumped to {_out_fp}')


class HistoricalMsgAnalysisClient(BasicClient, HistoricalMsgProcessor):
    """Multi-inhert from BasicClient and GuildManager to separate concerns: 
        Permission management and Discord connection.

    """
    GUILD = 916300758834630666  # "Real-UnknownDAO"  # discord server name
    def __init__(self, *args, dry_run: bool = True, **kwargs):
        BasicClient.__init__(self, *args, **kwargs)
        HistoricalMsgProcessor.__init__(self, self.GUILD)

    async def on_ready(self):
        await BasicClient.on_ready(self)
        await self.manage_guilds()

    async def get_guilds(self) -> List[Guild]:
        """"""
        return await self.fetch_guilds(limit=150).flatten()


class POAPDistributorClient(BasicClient, POAPDistributor):
    """Multi-inhert from BasicClient and GuildManager to separate concerns: 
        Permission management and Discord connection.

    """
    def __init__(self, *args, dry_run: bool = True, **kwargs):
        BasicClient.__init__(self, *args, **kwargs)
        POAPDistributor.__init__(self)

    async def on_ready(self):
        await BasicClient.on_ready(self)
        await self.manage_guilds()

    async def get_guilds(self) -> List[Guild]:
        """"""
        return await self.fetch_guilds(limit=150).flatten()

    async def on_message(self, msg):
        await BasicClient.on_message(self, msg)
        await POAPDistributor.on_message(self, msg)


def main():
    loop = asyncio.get_event_loop()
    if loop.is_running():  # in notebook
        client_loop = loop
        print(client_loop)
    else:
        client_loop = None

    intents = discord.Intents.default()
    intents.members = True
    client = POAPDistributorClient(loop=client_loop, intents=intents)

    '''POAPClaimingClientConfig is a dict of event_name (str) -> JSON filepath,
           each JSON is a dict from Discord user name (str) -> POAP claim link (str)
    '''
    poap_config = POAPClaimingClientConfig(
        project_name_to_discord_username_to_url_json_paths={
            'WhatTheFork Event POAP': r'C:\Users\admin\Pictures\POAPs\WhatTheFork\discord_users_to_claim_url_map_T=2021-12-11 12:59.json',
            '2021-11-27上海线下活动': r'C:\Users\admin\Pictures\POAPs\1127上海线下\discord_users_to_claim_url_map_T=2021-12-11 18:27.json',
            '昆明线下活动': r'C:\Users\admin\Pictures\POAPs\昆明线下\discord_users_to_claim_url_map_T=2021-12-11 18:29.json',
        }
    )
    client = POAPDistributorClient(loop=client_loop, intents=intents)
    client.set_config(poap_config)

    # client = HistoricalMsgAnalysisClient(loop=client_loop, intents=intents)

    client.run(MY_TOKEN)


if __name__ == "__main__":
    main()

