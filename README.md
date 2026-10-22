# Loot Ledger

A phone-friendly lookup for the hidden item stats in **Minecraft Dungeons II**: weapon damage per hit, combo time, DPS, reach, armor effect pools, and artifact cooldowns.

Live at **https://md2loot.th3dan.com**

The whole site is one static file, `index.html`, with the data embedded. No build step is needed to host it.

## Where the numbers come from

- **[MetaBot.gg](https://metabot.gg/en/minecraft-dungeons-2/methodology)** reads the game's data files (build 1.1.1.0 as of Oct 2026). Weapons, armor, uniques, artifacts.
- **[Dungeons II Stats Mod](https://github.com/operator1212/dungeons2-stats-mod)** data file. Hit-by-hit damage, combo time, jump attack, ammo cooldown.

When the two disagree, the site shows both numbers and flags the item. Nothing is estimated or filled in by hand.

These are base stats. In game, Item Power, enchantments, and gear effects change them.

## Updating after a game patch

```bash
bash tools/update.sh      # fetch sources, rebuild data/data.json and index.html
git diff --stat data/     # see what changed
```

Then commit and push. Cloudflare Pages redeploys on push.

| File | What it does |
|---|---|
| `tools/fetch_sources.sh` | Downloads source pages into `sources/` (not committed) |
| `tools/build_artifacts.py` | Pulls artifact stats out of the downloaded artifact pages |
| `tools/build_data.py` | Merges both sources, flags conflicts, writes `data/data.json` |
| `tools/build_site.py` | Builds `index.html` from `src/app.template.html` and the data |

Fan project. Not affiliated with Mojang or Microsoft.
