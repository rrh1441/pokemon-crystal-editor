# Pokemon Save Editing on macOS

Complete guide for editing Pokemon saves on a Miyoo (or any retro handheld) from a Mac.

---

## Overview

There are two approaches:

1. **Python Script (Recommended)** - Full-featured editor, no dependencies, what we actually use
2. **PKHeX (GUI)** - Open source tool, requires Wine + .NET on Mac, only needed for legality checking

**TL;DR:** The Python script now does almost everything - items, money, shiny Pokemon, max stats, level changes. PKHeX is only needed if you need to check legality for trading/competitive play.

---

## Method 1: Python Scripts (Quick & Easy)

### Setup
No setup needed - just Python 3 (included on macOS).

### Scripts Available

| Script | Purpose |
|--------|---------|
| `pokemon_crystal_editor.py` | Full editor - items, money, balls, info |
| `add_masterballs.py` | Quick Master Ball add (original) |

### Full Editor Usage

```bash
# Find saves
python3 ~/temp_shadcn/tiny/pokemon_crystal_editor.py --find

# Show save info (player name, money, inventory)
python3 ~/temp_shadcn/tiny/pokemon_crystal_editor.py --info

# Show Pokemon team
python3 ~/temp_shadcn/tiny/pokemon_crystal_editor.py --pokemon

# Add specific items
python3 pokemon_crystal_editor.py --masterballs
python3 pokemon_crystal_editor.py --rarecandy
python3 pokemon_crystal_editor.py --allballs
python3 pokemon_crystal_editor.py --money
python3 pokemon_crystal_editor.py --healing
python3 pokemon_crystal_editor.py --stats
python3 pokemon_crystal_editor.py --all-items    # All item cheats at once

# Pokemon editing
python3 pokemon_crystal_editor.py --pokemon           # Show team
python3 pokemon_crystal_editor.py --pokemon-detailed  # Show with full stats
python3 pokemon_crystal_editor.py --shiny 1           # Make Pokemon #1 shiny
python3 pokemon_crystal_editor.py --shiny all         # Make ALL Pokemon shiny
python3 pokemon_crystal_editor.py --maxstats 1        # Max DVs/EVs for Pokemon #1
python3 pokemon_crystal_editor.py --maxstats all      # Max stats for all
python3 pokemon_crystal_editor.py --level 1 100       # Set Pokemon #1 to level 100
python3 pokemon_crystal_editor.py --heal              # Fully heal all Pokemon

# Combine anything
python3 pokemon_crystal_editor.py --shiny all --maxstats all --money

# Specify save file explicitly
python3 ~/temp_shadcn/tiny/pokemon_crystal_editor.py --masterballs "/Volumes/OTHER/path/to/save.srm"
```

### Quick Master Ball Script (Original)

```bash
python3 ~/temp_shadcn/tiny/add_masterballs.py                              # Auto-find, 99 balls
python3 ~/temp_shadcn/tiny/add_masterballs.py "/path/to/save.srm"          # Specific file
python3 ~/temp_shadcn/tiny/add_masterballs.py "/path/to/save.srm" 50       # Custom quantity
```

### For a Different SD Card

1. Insert SD card
2. Find what it's mounted as: `ls /Volumes/`
3. Find the save: `python3 ~/temp_shadcn/tiny/pokemon_crystal_editor.py --find`
4. Run: `python3 ~/temp_shadcn/tiny/pokemon_crystal_editor.py --all "/Volumes/YOURCARD/path/to/save.srm"`

---

## Method 2: PKHeX (Full GUI Editor) - Optional

> **Note:** We set this up but didn't need it. The Python script was sufficient for adding items. Only use PKHeX if you need to edit Pokemon directly, check legality, or do complex batch edits.

PKHeX is the most popular open-source Pokemon save editor. It supports ALL Pokemon games from Gen 1 to current.

**GitHub:** https://github.com/kwsch/PKHeX
**License:** MIT (fully open source)

### When to Use PKHeX vs Python Script
| Task | Use |
|------|-----|
| Add Master Balls / items | Python script |
| Add Rare Candies | Python script |
| Max money | Python script |
| Make Pokemon shiny | Python script ✓ |
| Max Pokemon stats (DVs/EVs) | Python script ✓ |
| Set Pokemon level | Python script ✓ |
| Heal all Pokemon | Python script ✓ |
| Check if Pokemon is "legal" | PKHeX (only use case left) |

### One-Time Setup on macOS

#### 1. Install Wine
```bash
brew install --cask wine-stable
```

#### 2. Download .NET 9 Windows Runtime
Go to: https://dotnet.microsoft.com/download/dotnet/9.0
- Download "Windows x64" Desktop Runtime (.exe installer)
- Or direct link: windowsdesktop-runtime-9.0.x-win-x64.exe

#### 3. Install .NET in Wine
```bash
wine ~/Downloads/windowsdesktop-runtime-9.0.12-win-x64.exe /quiet /norestart
```
(Replace version number with what you downloaded)

#### 4. Download PKHeX
- Go to: https://github.com/kwsch/PKHeX/releases
- Download the latest `PKHeX-xx.xx.xx.zip`
- Unzip to a folder (e.g., ~/PKHeX/)

### Running PKHeX

```bash
wine ~/PKHeX/PKHeX.exe
```

A Windows-style GUI will open. You can:
- File > Open to load any Pokemon save file (.sav, .srm, .dsv, etc.)
- Edit Pokemon stats, items, money, badges, etc.
- File > Save to write changes

### PKHeX Features
- Edit any Pokemon (stats, moves, EVs, IVs, nature, shininess)
- Edit inventory (all items, balls, TMs, etc.)
- Edit trainer info (name, money, badges)
- Legality checker (useful for trading/competitive)
- Batch editor for bulk changes
- Plugin support

---

## What We Actually Did (Session Log)

1. **Tried PKHeX via Wine** - It needed .NET 9, lots of setup
2. **Realized:** We can just edit the save file directly with Python
3. **Found save file:** `/Volumes/JOE/Saves/CurrentProfile/saves/Gambatte/Pokemon - Crystal Version (USA, Europe) (Rev 1).srm`
4. **Wrote Python scripts** to edit items, money, Pokemon stats, shininess, etc.
5. **Result:** Full-featured save editor with zero dependencies

**Lesson learned:** Don't overcomplicate it. Python + knowledge of the save format = full control.

---

## Finding Save Files

### Miyoo SD Card Layout
```
/Volumes/<SD_NAME>/
├── Roms/
│   └── GBC/
│       └── Pokemon - Crystal Version (USA, Europe) (Rev 1).gbc
├── Saves/
│   └── CurrentProfile/
│       └── saves/
│           └── Gambatte/           # <-- GBC saves are here
│               └── Pokemon - Crystal Version (USA, Europe) (Rev 1).srm
└── RetroArch/
```

### Save File Extensions
| Extension | System |
|-----------|--------|
| .srm | SRAM save (RetroArch/Gambatte/most emulators) |
| .sav | Generic save (interchangeable with .srm usually) |
| .dsv | DeSmuME (DS) saves |
| .State | Save states (NOT the same as in-game saves) |

### Find Commands
```bash
# List mounted volumes
ls /Volumes/

# Find all save files
find /Volumes/<SDCARD> -name "*.srm" -o -name "*.sav" 2>/dev/null

# Find specific game
find /Volumes/<SDCARD> -iname "*crystal*" 2>/dev/null
```

---

## Pokemon Crystal Save Structure (Technical)

For those wanting to make custom scripts.

### File Format
- Total size: 32,768 bytes (32 KB)
- Contains two save slots (main + backup)
- Checksum protected

### Key Offsets (US/EU Version)

| Offset | Size | Description |
|--------|------|-------------|
| 0x2009 | - | Checksum data start |
| 0x200A | 11 | Player name |
| 0x2021 | 2 | Trainer ID |
| 0x23DB | 3 | Money (BCD encoded) |
| 0x241A | 1 | Item pocket count |
| 0x241B | 40 | Item pocket data |
| 0x2449 | 1 | Key items count |
| 0x2465 | 1 | Ball pocket count |
| 0x2466 | 24 | Ball pocket data (12 slots x 2 bytes) |
| 0x247D | 1 | TM/HM count |
| 0x2D69 | 2 | Checksum (little-endian) |

### Item Data Format
Each item entry is 2 bytes:
```
[item_id] [quantity]
```

### Ball Item IDs
| ID | Ball |
|----|------|
| 0x01 | Master Ball |
| 0x02 | Ultra Ball |
| 0x03 | Great Ball |
| 0x04 | Poke Ball |
| 0xA0 | Level Ball |
| 0xA1 | Lure Ball |
| 0xA2 | Fast Ball |
| 0xA4 | Friend Ball |
| 0xA5 | Moon Ball |
| 0xA6 | Love Ball |

### Checksum Calculation
```python
def calculate_checksum(data):
    checksum = 0
    for i in range(0x2009, 0x2D69):
        checksum = (checksum + data[i]) & 0xFFFF
    return checksum
```

---

## Extending the Script

The `pokemon_crystal_editor.py` is designed to be extended. Here's how:

### Adding a New Item Type

```python
# In pokemon_crystal_editor.py, add a function:
def add_my_item(data, qty=99):
    """Add my custom item."""
    result = add_item_to_pocket(data, 'items', 0xXX, qty)  # Replace 0xXX with item ID
    print(f"My Item: {result}")

# Then add to main():
if '--myitem' in args:
    add_my_item(data)
    modified = True
```

### Pocket Types
| Pocket | Use For |
|--------|---------|
| `'items'` | Potions, Rare Candy, etc |
| `'balls'` | Poke Balls |
| `'key_items'` | Key items |
| `'tm_hm'` | TMs and HMs |

### Common Item IDs
| ID | Item |
|----|------|
| 0x01 | Master Ball |
| 0x02 | Ultra Ball |
| 0x03 | Great Ball |
| 0x04 | Poke Ball |
| 0x08 | Rare Candy |
| 0x0D | Max Potion |
| 0x0E | Full Restore |
| 0x10 | Max Revive |
| 0x12 | Max Elixir |
| 0x19 | Full Heal |
| 0x1E | Nugget |
| 0x2D | HP Up |
| 0x2E | Protein |
| 0x2F | Iron |
| 0x30 | Carbos |
| 0x31 | Calcium |
| 0x4A | PP Max |

### Full Item List
See: https://bulbapedia.bulbagarden.net/wiki/List_of_items_by_index_number_(Generation_II)

---

## Troubleshooting

### "Save file not found"
- Check SD card is mounted: `ls /Volumes/`
- The save might be in a different folder - use `find` to search

### Game shows corrupted save
1. Restore backup: `cp save.srm.backup_before_masterballs save.srm`
2. Different ROM versions have different offsets - verify you're using US/EU Crystal

### PKHeX won't open
- Make sure .NET was installed via Wine (not native macOS .NET)
- Try running with console output: `wine ~/PKHeX/PKHeX.exe 2>&1`

### Changes don't appear in game
- Safely eject SD card before removing
- Make sure you edited the right save file (not a backup)
- Some handhelds cache saves - fully restart the game

---

## Resources

- **PKHeX Source Code:** https://github.com/kwsch/PKHeX
- **PKHeX.Core NuGet:** For building your own tools
- **Bulbapedia Save Structure:** https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_II)
- **Gen 2 Item IDs:** https://bulbapedia.bulbagarden.net/wiki/List_of_items_by_index_number_(Generation_II)
