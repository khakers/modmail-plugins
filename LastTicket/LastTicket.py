"""
Last Ticket Modmail plugin
Copyright (C) 2023  khakers

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


import datetime
import typing
import urllib.parse

import discord
from discord.ext import commands

import core.thread
from core.models import getLogger

logger = getLogger(__name__)


class LastTicket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_url(self, log_data: dict) -> str:
        prefix = self.bot.config["log_url_prefix"].strip("/")

        return urllib.parse.urljoin(self.bot.config["log_url"], prefix + '/' + log_data["_id"])

    @commands.Cog.listener()
    async def on_thread_ready(
        self,
        thread: core.thread.Thread,
        creator: typing.Union[discord.Member, discord.User],
        category: discord.CategoryChannel,
        initial_message,
    ):
        logger.debug("thread %s, %s", thread, type(thread))
        logger.debug("creator %s, %s", creator, type(creator))
        logger.debug("category %s, %s", category, type(category))
        logger.debug("initial_message %s, %s", initial_message, type(initial_message))

        # The type hinting is wrong, this could also be an int
        channel = thread.channel
        # user = thread.recipient
        user_id = thread.id

        # self.bot.threads.find(recipient_id=user_id)

        # if type(user) == int:
        #     logger.debug("User was an int and not a discord object, fetching user from discord api")
        #     user_id = user
        # else:
        #     user_id = user.id
        # search get last ticket
        # logger.debug("Searching for previous ticket for recipient %s, type %s", user, type(user))
        logger.debug("Searching for previous ticket for recipient id %s", user_id)

        # we could  do a projection to reduce the amount of data we get back in the future
        previous_ticket = self.bot.db.logs.find(
            filter={"creator.id": str(user_id)},
            sort=[("created_at", -1)],
        )
        # Skip the first result, as it is the current ticket
        # Would've liked to do this another way, but this seemed like the only way with the terrible data modmail gives us
        previous_ticket.skip(skip=1)
        previous_ticket = await previous_ticket.to_list(length=1)
        previous_ticket = previous_ticket[0] if len(previous_ticket) > 0 else None

        if previous_ticket is not None:
            logger.debug(str(previous_ticket))
            logger.debug("Previous ticket found for user %s", user_id)
            log_url = self.get_log_url(previous_ticket)
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="View Previous log",
                    url=log_url,
                    style=discord.ButtonStyle.url,
                )
            )
            recipient_name = previous_ticket['recipient']['name']
            if previous_ticket['recipient']['discriminator'] != '0':
                recipient_name += f"#{previous_ticket['recipient']['discriminator']}"
#{recipient_name}({previous_ticket['recipient']['id']}
            await channel.send(
                embed=discord.Embed(
                    title="Previous Ticket",
                    description=f"<@{previous_ticket['recipient']['id']}>:\n"+previous_ticket["messages"][0]["content"][0:120],
                    url=log_url,
                    timestamp=datetime.datetime.fromisoformat(previous_ticket["created_at"]),
                ),
                view=view,
            )
        else:
            logger.debug("No previous ticket found for user %s", user_id)
            logger.debug(previous_ticket)


async def setup(bot):
    await bot.add_cog(LastTicket(bot))
