#!/bin/bash
# Regenerate shell completions from argparse parsers
# Requires: shtab (pip install shtab), telethon, pyyaml
set -e

cd "$(dirname "$0")/.."

for shell in bash zsh; do
    if [ "$shell" = "zsh" ]; then
        out="completions/_telegram-cli"
    else
        out="completions/telegram-cli.${shell}"
    fi
    PYTHONPATH=. python -m shtab --prog "telegram-cli" "telegram_cli.build_parser" --shell "$shell" 2>/dev/null > "$out"
    echo "Generated $out"
done

# Fish completions (shtab doesn't support fish)
PYTHONPATH=. python -c "
from telegram_cli import build_parser

def gen_fish(prog, parser):
    lines = [f'# Completions for {prog}', '# AUTOMATICALLY GENERATED', '']
    for action in parser._subparsers._actions:
        if hasattr(action, '_parser_class'):
            for name, sub in action.choices.items():
                desc = (sub.description or '').replace(\"'\", \"\\\\\'\")
                lines.append(f\"complete -c {prog} -n '__fish_use_subcommand' -a '{name}' -d '{desc}'\")
    lines.append('')
    for action in parser._subparsers._actions:
        if hasattr(action, '_parser_class'):
            for name, sub in action.choices.items():
                for a in sub._actions:
                    for opt in a.option_strings:
                        if opt.startswith('--'):
                            flag = opt[2:]
                            desc = (a.help or '').replace(\"'\", \"\\\\\'\")
                            if a.choices:
                                choices = ' '.join(str(c) for c in a.choices)
                                lines.append(f\"complete -c {prog} -n '__fish_seen_subcommand_from {name}' -l {flag} -d '{desc}' -xa '{choices}'\")
                            elif getattr(a, 'nargs', None) == 0 or (hasattr(a, 'const') and a.const is True):
                                lines.append(f\"complete -c {prog} -n '__fish_seen_subcommand_from {name}' -l {flag} -d '{desc}'\")
                            else:
                                lines.append(f\"complete -c {prog} -n '__fish_seen_subcommand_from {name}' -l {flag} -d '{desc}' -r\")
    return '\n'.join(lines) + '\n'

with open('completions/telegram-cli.fish', 'w') as f:
    f.write(gen_fish('telegram-cli', build_parser()))
" 2>/dev/null

echo "Generated completions/telegram-cli.fish"
echo "Done."
