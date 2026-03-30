#!/bin/bash
# Regenerate shell completions from argparse parsers
# Requires: shtab (pip install shtab), telethon, pyyaml
set -e

cd "$(dirname "$0")/.."

for shell in bash zsh; do
    for prog in telegram-cli telegram-listen; do
        module="${prog//-/_}"
        if [ "$shell" = "zsh" ]; then
            out="completions/_${prog}"
        else
            out="completions/${prog}.${shell}"
        fi
        PYTHONPATH=. python -m shtab --prog "$prog" "${module}.build_parser" --shell "$shell" 2>/dev/null > "$out"
        echo "Generated $out"
    done
done

# Fish completions (shtab doesn't support fish)
PYTHONPATH=. python -c "
from telegram_cli import build_parser
from telegram_listen import build_parser as build_listen_parser

def gen_fish(prog, parser):
    lines = [f'# Completions for {prog}', '# AUTOMATICALLY GENERATED', '']
    for action in parser._actions:
        for opt in action.option_strings:
            if opt.startswith('--'):
                flag = opt[2:]
                desc = (action.help or '').replace(\"'\", \"\\\\\'\")
                if action.choices:
                    choices = ' '.join(str(c) for c in action.choices)
                    lines.append(f\"complete -c {prog} -l {flag} -d '{desc}' -xa '{choices}'\")
                elif action.nargs == 0 or (hasattr(action, 'const') and action.const is True):
                    lines.append(f\"complete -c {prog} -l {flag} -d '{desc}'\")
                else:
                    lines.append(f\"complete -c {prog} -l {flag} -d '{desc}' -r\")
    return '\n'.join(lines) + '\n'

with open('completions/telegram-cli.fish', 'w') as f:
    f.write(gen_fish('telegram-cli', build_parser()))
with open('completions/telegram-listen.fish', 'w') as f:
    f.write(gen_fish('telegram-listen', build_listen_parser()))
" 2>/dev/null

echo "Generated completions/telegram-cli.fish"
echo "Generated completions/telegram-listen.fish"
echo "Done."
