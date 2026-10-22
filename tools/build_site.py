"""Assemble index.html from src/app.template.html + data/data.json."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tpl = open(os.path.join(ROOT, 'src', 'app.template.html'), encoding='utf-8').read()
data = open(os.path.join(ROOT, 'data', 'data.json'), encoding='utf-8').read()
assert tpl.count('__DATA__') == 1

# The template's first part (title, fonts, style) belongs in <head>.
head, body = tpl.split('<div class="wrap">', 1)
head = head.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E"
           "%3Crect width='16' height='16' fill='%2315171c'/%3E"
           "%3Cpath d='M11 2h3v3l-6 6-1-1-2 2 1 1-1 1-3-3 1-1 1 1 2-2-1-1z' fill='%236fd3c3'/%3E%3C/svg%3E")

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Hidden item stats for Minecraft Dungeons II: weapon damage per hit, DPS, reach, armor effect pools and artifact cooldowns, from the game's data files.">
<link rel="icon" href="{FAVICON}">
<style>
:root {{ padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }}
body {{ margin: 0; }}
img {{ max-width: 100%; }}
[hidden] {{ display: none !important; }}
</style>
{head}</head>
<body>
<div class="wrap">{body.replace('__DATA__', data.replace('</', '<\\/'))}
</body>
</html>
"""
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(page)
print('index.html', len(page) // 1024, 'KB')
