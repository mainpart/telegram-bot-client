# Completions for telegram-cli
# AUTOMATICALLY GENERATED

complete -c telegram-cli -l help -d 'show this help message and exit'
complete -c telegram-cli -l init -d 'Login and generate StringSession token.'
complete -c telegram-cli -l list-chats -d 'List recent chats.'
complete -c telegram-cli -l search-messages -d 'Search message text across all chats.' -r
complete -c telegram-cli -l search-contacts -d 'Search users, groups, channels by name or username.' -r
complete -c telegram-cli -l search-chat -d 'Search messages within a specific chat (requires --chat).' -r
complete -c telegram-cli -l chat -d 'Chat username or ID.' -r
complete -c telegram-cli -l from-id -d 'Start message ID.' -r
complete -c telegram-cli -l to-id -d 'End message ID.' -r
complete -c telegram-cli -l inclusive -d 'Include boundary messages.'
complete -c telegram-cli -l forward -d 'Read newer messages.'
complete -c telegram-cli -l backward -d 'Read older messages.'
complete -c telegram-cli -l send-message -d 'Text to send.' -r
complete -c telegram-cli -l send-files -d 'Files to send.' -r
complete -c telegram-cli -l reply-to -d 'Message ID to reply to.' -r
complete -c telegram-cli -l target-chat -d 'Target chat for forward/cross-chat reply.' -r
complete -c telegram-cli -l click-button -d 'Button text to click.' -r
complete -c telegram-cli -l message-id -d 'Message ID for actions.' -r
complete -c telegram-cli -l forward-message -d 'Forward message.'
complete -c telegram-cli -l reply-message -d 'Reply text.' -r
complete -c telegram-cli -l download -d 'Download file from message.'
complete -c telegram-cli -l add-reaction -d 'Add reaction emoji.' -r
complete -c telegram-cli -l edit-message -d 'New text for message.' -r
complete -c telegram-cli -l delete-message -d 'Delete a message. Requires --chat and --message-id.'
complete -c telegram-cli -l get-entities -d 'Get info for users/chats by ID or username.' -r
complete -c telegram-cli -l filter -d 'Media type filter.' -xa 'photo video document url voice gif music round_video mentions pinned'
complete -c telegram-cli -l min-date -d 'Min date in ISO format (e.g. 2026-01-01).' -r
complete -c telegram-cli -l max-date -d 'Max date in ISO format.' -r
complete -c telegram-cli -l groups-only -d 'Search in groups only.'
complete -c telegram-cli -l users-only -d 'Search in private chats only.'
complete -c telegram-cli -l broadcasts-only -d 'Search in channels only.'
complete -c telegram-cli -l limit -d 'Number of items to fetch.' -r
complete -c telegram-cli -l profile -d 'Filtering profile from profiles.json.' -r
complete -c telegram-cli -l bot -d 'Bot mode (token from config.yaml telegram.bot_token).'
complete -c telegram-cli -l incoming-only -d 'Filter only incoming messages.'
complete -c telegram-cli -l outgoing-only -d 'Filter only outgoing messages.'
complete -c telegram-cli -l from-user -d 'Filter messages from specific user ID.' -r
complete -c telegram-cli -l pattern -d 'Filter messages matching regex pattern.' -r
complete -c telegram-cli -l has-media -d 'Filter messages with media only.'
complete -c telegram-cli -l forwarded-only -d 'Filter only forwarded messages.'
complete -c telegram-cli -l replies-only -d 'Filter only reply messages.'
complete -c telegram-cli -l has-reactions -d 'Filter messages with reactions only.'
