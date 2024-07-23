"""
Last Ticket Modmail plugin
Copyright (C) 2024  khakers
https://github.com/khakers/modmail-plugins

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
from typing import Union, Optional

import discord.utils
from discord.ext import commands

from core.models import getLogger
from core.thread import Thread


class GuaranteedDelivery(commands.Cog):

    def __init__(self, bot):
        self.bot: bot.ModmailBot = bot
        self.logger = getLogger("GuaranteedDelivery")
        self.logger.info("Loaded GuaranteedDelivery")

    @commands.Cog.listener()
    async def on_thread_reply(self, thread: Thread, from_mod: bool, message, anonymous: bool, plain: bool):
        key = "last_processed_reply_message_id" if from_mod else "last_processed_user_message_id"
        self.logger.debug(f"Thread {thread.id} last processed {key} updated to {message.id}")
        self.bot.api.logs.update_one(
            {"$and": [
                {"recipient.id": str(thread.id)},
                {"open": True}
            ]},
            {"$set": {key: message.id}})

    @commands.Cog.listener()
    async def on_thread_create(self, thread: Thread):
        self.logger.info(f"Thread {thread.id} is created with channel {thread.channel.id}")

        res = await self.bot.api.logs.find_one(
            {"$and": [
                {"recipient.id": str(thread.id)},
                {"open": True}
            ]},
            {"dm_channel_id": 1, "last_processed_user_message_id": 1})
        self.logger.debug(f"got result {res} for thread {thread.id}")

        last_processed_user_message_id = await self.get_last_processed_message_id(recipient_id=thread.id)

        if last_processed_user_message_id is not None:

            # Get the DM channel
            dm_channel = await self.bot.create_dm(thread.recipient)
            self.logger.debug(f"Got dm_channel {dm_channel} for thread {thread.id}")
            if dm_channel is None:
                self.logger.error(f"Could not get dm_channel for thread {thread.id}")
                return False
            await self.process_missed_messages(dm_channel, last_processed_user_message_id)

    async def process_missed_messages(self, channel, last_processed_user_message_id: int):
        if last_processed_user_message_id is None:
            # This is really an error
            self.logger.error(f"last_processed_user_message_id is None for channel {channel.id}")
            return

        after_time = discord.utils.snowflake_time(last_processed_user_message_id)
        # todo allow configurable limit
        messages = channel.history(after=after_time, limit=15)
        last_message_id = None
        async for message in messages:
            if message.author == self.bot.user:
                self.logger.debug(f"Skipping bot message {message.id}")
                continue
            self.logger.info(f"Processing missed message {message.id} for channel {channel.id}")
            await self.bot.process_dm_modmail(message)
            last_message_id = message.id



    async def get_last_processed_message_id(self, dm_channel_id: int | None = None, recipient_id: int | None = None) -> Optional[int]:
        if dm_channel_id is None and recipient_id is None:
            return None
        if dm_channel_id is not None:
            self.logger.debug(f"Getting last_processed_user_message_id for dm_channel_id {dm_channel_id}")
            res = await self.bot.api.logs.find_one(
                {"$and": [
                    {"dm_channel_id": str(dm_channel_id)},
                    {"open": True}
                ]},
                {"last_processed_user_message_id": 1})
        else:
            self.logger.debug(f"Getting last_processed_user_message_id for recipient_id {recipient_id}")
            res = await self.bot.api.logs.find_one(
                {"$and": [
                    {"recipient.id": str(recipient_id)},
                    {"open": True}
                ]},
                {"last_processed_user_message_id": 1})
        if res is None:
            self.logger.error(f"Could not find last_processed_user_message_id for dm_channel_id {dm_channel_id} or "
                              f"recipient_id {recipient_id}")
            return None
        return res["last_processed_user_message_id"] if "last_processed_user_message_id" in res else None

async def setup(bot):
    await bot.add_cog(GuaranteedDelivery(bot))
