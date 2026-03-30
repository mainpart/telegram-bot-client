# Completions for telegram-cli
# AUTOMATICALLY GENERATED

complete -c telegram-cli -n '__fish_use_subcommand' -a 'init' -d 'telegram-cli init [-h]'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'chats' -d 'telegram-cli chats [-h] [--limit LIMIT] [--profile PROFILE] [--bot]'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'read' -d 'telegram-cli read [-h] [--from-id FROM_ID] [--to-id TO_ID] [--forward]
                         [--backward] [--inclusive] [--limit LIMIT]
                         [--profile PROFILE] [--bot] [--incoming-only]
                         [--outgoing-only] [--from-user FROM_USER]
                         [--pattern PATTERN] [--has-media] [--forwarded-only]
                         [--replies-only] [--has-reactions]
                         chat'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'send' -d 'telegram-cli send [-h] [--files FILES [FILES ...]]
                         [--reply-to REPLY_TO] [--bot]
                         chat [text]'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'edit' -d 'telegram-cli edit [-h] [--bot] chat message_id text'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'delete' -d 'telegram-cli delete [-h] [--bot] chat message_id'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'forward' -d 'telegram-cli forward [-h] [--bot] chat message_id target_chat'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'reply' -d 'telegram-cli reply [-h] [--files FILES [FILES ...]]
                          [--target-chat TARGET_CHAT] [--bot]
                          chat message_id [text]'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'react' -d 'telegram-cli react [-h] [--bot] chat message_id emoji'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'click' -d 'telegram-cli click [-h] [--bot] chat message_id button_text'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'download' -d 'telegram-cli download [-h] [--bot] chat message_id'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'search-messages' -d 'telegram-cli search-messages [-h] [--limit LIMIT]
                                    [--filter {photo,video,document,url,voice,gif,music,round_video,mentions,pinned}]
                                    [--min-date MIN_DATE]
                                    [--max-date MAX_DATE] [--groups-only]
                                    [--users-only] [--broadcasts-only]
                                    [--profile PROFILE] [--bot]
                                    query'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'search-contacts' -d 'telegram-cli search-contacts [-h] [--limit LIMIT] [--profile PROFILE]
                                    [--bot]
                                    query'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'search-chat' -d 'telegram-cli search-chat [-h] [--limit LIMIT]
                                [--filter {photo,video,document,url,voice,gif,music,round_video,mentions,pinned}]
                                [--from-user FROM_USER] [--min-date MIN_DATE]
                                [--max-date MAX_DATE] [--profile PROFILE]
                                [--bot]
                                chat query'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'info' -d 'telegram-cli info [-h] [--profile PROFILE] [--bot] entity [entity ...]'
complete -c telegram-cli -n '__fish_use_subcommand' -a 'listen' -d 'telegram-cli listen [-h] [--chat CHAT] [--private-only]
                           [--mentioned-only] [--profile PROFILE] [--bot]
                           [--incoming-only] [--outgoing-only]
                           [--from-user FROM_USER] [--pattern PATTERN]
                           [--has-media] [--forwarded-only] [--replies-only]
                           [--has-reactions]'

complete -c telegram-cli -n '__fish_seen_subcommand_from init' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from chats' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from chats' -l limit -d 'Number of chats (default: 100).' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from chats' -l profile -d 'Filtering profile.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from chats' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l from-id -d 'Start message ID.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l to-id -d 'End message ID.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l forward -d 'Read newer messages.'
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l backward -d 'Read older messages.'
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l inclusive -d 'Include boundary messages.'
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l limit -d 'Number of messages.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l profile -d 'Filtering profile.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l incoming-only -d 'Only incoming messages.'
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l outgoing-only -d 'Only outgoing messages.'
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l from-user -d 'Messages from specific user ID.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l pattern -d 'Filter by regex pattern.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l has-media -d 'Only messages with media.'
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l forwarded-only -d 'Only forwarded messages.'
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l replies-only -d 'Only replies.'
complete -c telegram-cli -n '__fish_seen_subcommand_from read' -l has-reactions -d 'Only messages with reactions.'
complete -c telegram-cli -n '__fish_seen_subcommand_from send' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from send' -l files -d 'Files to send.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from send' -l reply-to -d 'Message ID to reply to.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from send' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from edit' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from edit' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from delete' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from delete' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from forward' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from forward' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from reply' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from reply' -l files -d 'Files to send.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from reply' -l target-chat -d 'Target chat for cross-chat reply.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from reply' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from react' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from react' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from click' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from click' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from download' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from download' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from search-messages' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from search-messages' -l limit -d 'Max results.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from search-messages' -l filter -d 'Media type filter.' -xa 'photo video document url voice gif music round_video mentions pinned'
complete -c telegram-cli -n '__fish_seen_subcommand_from search-messages' -l min-date -d 'Min date (YYYY-MM-DD).' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from search-messages' -l max-date -d 'Max date (YYYY-MM-DD).' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from search-messages' -l groups-only -d 'Groups only.'
complete -c telegram-cli -n '__fish_seen_subcommand_from search-messages' -l users-only -d 'Private chats only.'
complete -c telegram-cli -n '__fish_seen_subcommand_from search-messages' -l broadcasts-only -d 'Channels only.'
complete -c telegram-cli -n '__fish_seen_subcommand_from search-messages' -l profile -d 'Filtering profile.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from search-messages' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from search-contacts' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from search-contacts' -l limit -d 'Max results.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from search-contacts' -l profile -d 'Filtering profile.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from search-contacts' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from search-chat' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from search-chat' -l limit -d 'Max results.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from search-chat' -l filter -d 'Media type filter.' -xa 'photo video document url voice gif music round_video mentions pinned'
complete -c telegram-cli -n '__fish_seen_subcommand_from search-chat' -l from-user -d 'From specific user ID.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from search-chat' -l min-date -d 'Min date (YYYY-MM-DD).' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from search-chat' -l max-date -d 'Max date (YYYY-MM-DD).' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from search-chat' -l profile -d 'Filtering profile.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from search-chat' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from info' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from info' -l profile -d 'Filtering profile.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from info' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l help -d 'show this help message and exit'
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l chat -d 'Chat to listen (repeatable).' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l private-only -d 'Private messages only.'
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l mentioned-only -d 'Only messages mentioning me.'
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l profile -d 'Filtering profile.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l bot -d 'Bot mode (uses bot_token from config).'
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l incoming-only -d 'Only incoming messages.'
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l outgoing-only -d 'Only outgoing messages.'
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l from-user -d 'Messages from specific user ID.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l pattern -d 'Filter by regex pattern.' -r
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l has-media -d 'Only messages with media.'
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l forwarded-only -d 'Only forwarded messages.'
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l replies-only -d 'Only replies.'
complete -c telegram-cli -n '__fish_seen_subcommand_from listen' -l has-reactions -d 'Only messages with reactions.'
