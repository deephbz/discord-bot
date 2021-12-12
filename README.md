# discord-bot
Send custom messages in batch; React to specific commands, distribute POAP claim links, etc.

- `common.py`: Reusable base classes
- `permission_manager.py`: Implements GuildManagerClient providing convenient role, channel permission management. You could use it for backup / restore in batch.
- `poap_distribution_bot.py`: This module implements HistoricalMsgAnalysisClient which helps you to analyze historical messages (in order to to retroactive airdrops); and POAPDistributorClient, which helps you to distribute POAP claim codes (or anything else) to white-listed users.

