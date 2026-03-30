# Completions for telegram-listen
# AUTOMATICALLY GENERATED

complete -c telegram-listen -l help -d 'show this help message and exit'
complete -c telegram-listen -l chat -d 'Chat to listen (ID or username). Can be repeated.' -r
complete -c telegram-listen -l private-only -d 'Listen to private messages only.'
complete -c telegram-listen -l mentioned-only -d 'Only messages mentioning me.'
complete -c telegram-listen -l profile -d 'Filtering profile from profiles.json.' -r
complete -c telegram-listen -l bot -d 'Bot mode (token from config.yaml telegram.bot_token).'
complete -c telegram-listen -l incoming-only -d 'Filter only incoming messages.'
complete -c telegram-listen -l outgoing-only -d 'Filter only outgoing messages.'
complete -c telegram-listen -l from-user -d 'Filter messages from specific user ID.' -r
complete -c telegram-listen -l pattern -d 'Filter messages matching regex pattern.' -r
complete -c telegram-listen -l has-media -d 'Filter messages with media only.'
complete -c telegram-listen -l forwarded-only -d 'Filter only forwarded messages.'
complete -c telegram-listen -l replies-only -d 'Filter only reply messages.'
complete -c telegram-listen -l has-reactions -d 'Filter messages with reactions only.'
