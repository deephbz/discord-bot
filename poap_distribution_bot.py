"""
- Discord.py API Reference: https://discordpy.readthedocs.io/en/latest/api.html#
- Get TOKEN of your bot: https://discord.com/developers/applications, select APP -> Bot -> reveal/create Token

"""
import asyncio
import json
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import discord
import pandas as pd
from discord import Guild

MY_TOKEN = ""

MEMBERS_TO_MENTION = ['some_discord_username#1234']  # hard-coded name list for convenience use


@dataclass
class POAPClaimingClientConfig:
    project_name_to_discord_username_to_url_json_paths: Dict[str, Path]


class POAPClaimingClient(discord.Client):
    poap_issue_claim_tutorial_link = "https://unknown-dao.notion.site/POAP-Issue-Claim-Tutorial-1b07698a43914229a228e9dfe7020990"
    CLAIM_MAGIC_SPELLS = [
        "领取-我和我的领航猫-POAP",
        #         'ClaimPOAP',
        #         '拿来吧你',
        #         '看蓝猫，学蓝猫，分享知识我自豪！',
        #         'Here comes a honorable designer.'
    ]
    MEMBER_STAT_SPELL = "Check it out"
    ADMIN_DIS_NAME = "₿ingnan.ΞTH#0369"
    GUILD = "Unknown DAO"  # discord server name
    SHALL_DUMP_MEMBER_STAT: bool = False

    def set_config(self, cfg: POAPClaimingClientConfig):
        """Custom configurations"""
        self.cfg = cfg
        self.project_name_to_name_url_map = {}
        for (
            project_name,
            path,
        ) in self.cfg.project_name_to_discord_username_to_url_json_paths.items():
            self.project_name_to_name_url_map[project_name] = json.load(open(path, "r"))
        self.my_cached_members = []

    async def on_ready(self):
        print("Connected!")
        print("Username: {0.name}\nID: {0.id}".format(self.user))

    async def on_message(self, msg):
        """This callback is invoked EVERY TIME a member sends a message to this bot or in the server."""
        if any(msg.content.startswith(spell) for spell in self.CLAIM_MAGIC_SPELLS):
            await self._on_claim_poap(msg)
        if str(msg.author) == self.ADMIN_DIS_NAME and msg.content.startswith(
            self.MEMBER_STAT_SPELL
        ):
            await self._on_member_stat(msg)

    async def _on_member_stat(self, msg):
        """Get list of members in the server. Then do custom statistics on it."""
        guilds = await self.fetch_guilds(limit=150).flatten()
        for guild in guilds:
            if guild.name != self.GUILD:
                continue
            await self._stat_single_guild(guild)
        self._send_msg_and_mention_target_members(
            [
                m
                for m in self.my_cached_members
                #                               if str(m) in MEMBERS_TO_MENTION
                if any(
                    str(m).startswith(mention.split("#")[0])
                    for mention in MEMBERS_TO_MENTION
                )
            ]
        )

    async def _send_msg_and_mention_target_members(self, members_to_mention):
        await msg.channel.send(
            "\n".join(
                [
                    "Hey guys:",
                    " ".join([m.mention for m in members_to_mention]),
                    f"You are already added to **whitelist**, send `{self.CLAIM_MAGIC_SPELLS[0]}` to claim here.",
                    "Ignore if you've already done it."
                    #                 '最后一只未售出的AstroCat的免费获取资格，将于今晚从107位之前参与转发活动的人中抽取。让我们拭目以待欧皇的诞生！',
                    #                 f'其中{len(members_to_mention)}人填写了discordID（没填写不影响抽奖）：艾特你们请保持关注 <#904708888404848720> 噢',
                    #                 ' '.join([m.mention for m in members_to_mention]),
                ]
            ),
            delete_after=3600 * 8,
        )  # delete the msg after 8 hours

    async def _stat_single_guild(self, guild: Guild):
        """Dump to dataframe for later data analysis"""
        members = await guild.fetch_members(limit=1500).flatten()
        print(f"{len(members)} members in {guild.name}!")

        self.my_cached_members = members
        if self.SHALL_DUMP_MEMBER_STAT:
            dfs = []
            for member in members:
                dfs.append(
                    {
                        "name": str(member),
                        "joined_at": member.joined_at,
                        "created_at": member.created_at,
                        "is_bot": member.bot,
                    }
                )
            pd.DataFrame(dfs).to_parquet(f"member_stats.parquet")

    async def _on_claim_poap(self, msg):
        """Check if a user is in white list and DM him URL if so."""
        print(type(msg.author), repr(msg.author), str(msg.author))
        print(msg.content)
        author = str(msg.author)
        project_name_to_urls = {}
        for (
            project_name,
            discord_users_to_claim_url_map,
        ) in self.project_name_to_name_url_map.items():
            url = discord_users_to_claim_url_map.get(author, "")
            if url:
                project_name_to_urls[project_name] = url

        if project_name_to_urls:
            await msg.author.send(self._format_private_msg(project_name_to_urls))
            await msg.channel.send(
                f"👍 Succeeded. **{author}** please check your DM :)", delete_after=60
            )
        else:
            await msg.channel.send(
                f"😑 **{author}** is not a valid user to claim.", delete_after=3600 * 24
            )

    def _format_private_msg(self, project_name_to_poap_url: Dict[str, str]) -> str:
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


def main():
    intents = discord.Intents.default()
    intents.members = True
    '''POAPClaimingClientConfig is a dict of event_name (str) -> JSON filepath,
           each JSON is a dict from Discord user name (str) -> POAP claim link (str)
    '''
    config = POAPClaimingClientConfig(
        {
            #             '2021-10-18&23 NFT Workshop': r'C:\Users\admin\Pictures\POAPs\UnknownDAO 2021-10-23 NFT Workshop\discord_users_to_claim_url_map_T=2021-10-26 22:29.json',
            #             'Designer Badges': r'C:\Users\admin\Pictures\POAPs\UnknownDAO Designer Workshop #1 POAP Badges\discord_users_to_claim_url_map_T=2021-10-25 19:51.json',
            "我和我的领航猫": r"C:\Users\admin\Pictures\POAPs\我和我的领航猫\discord_users_to_claim_url_map_T=2021-11-07 22:08.json"
        }
    )
    loop = asyncio.get_event_loop()
    if loop.is_running():  # in notebook
        client_loop = loop
        print(client_loop)
    else:
        client_loop = None
    client = POAPClaimingClient(loop=client_loop, intents=intents)
    client.set_config(config)
    print(
        "Ask users to send following commands: ",
        ", ".join([f"`{s}`" for s in client.CLAIM_MAGIC_SPELLS]),
    )
    client.run(MY_TOKEN)
    print("client.run finished")
    # guilds is now a list of Guild...


if __name__ == "__main__":
    main()

