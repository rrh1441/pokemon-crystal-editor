# Pokemon Crystal Save Editor - Checksum Bug Fix

## The Problem

Master Ball modifications (and other item edits) weren't persisting in-game. The game would show 1 Master Ball instead of 99, even though the editor reported success.

## Root Cause

**Two bugs were found:**

### Bug 1: Wrong Checksum Offsets for Bank 1

The code was using incorrect memory offsets for Bank 1's checksum:

```python
# WRONG (old values)
CHECKSUM_OFFSET_BANK1 = 0x1F69
CHECKSUM_DATA_END_BANK1 = 0x1F68

# CORRECT (fixed values)
CHECKSUM_OFFSET_BANK1 = 0x1F0D
CHECKSUM_DATA_END_BANK1 = 0x1D82
```

The checksum start offset (0x1209) was correct, but the end and storage offsets were wrong.

### Bug 2: Terminology Confusion (Primary vs Secondary)

The code comments incorrectly labeled which bank was primary:

| Address Range | Old Label | Correct Label |
|---------------|-----------|---------------|
| 0x1200+ (Bank 1) | "primary" | **secondary/backup** |
| 0x2000+ (Bank 2) | "backup" | **primary** (loaded first) |

## Why Modifications Failed

1. Editor modified items at 0x1665 (Bank 1) and 0x2465 (Bank 2) correctly
2. Editor calculated checksum for Bank 1 using wrong range (0x1209-0x1F68)
3. Editor wrote checksum to wrong location (0x1F69 instead of 0x1F0D)
4. Game loaded, found Bank 1 checksum invalid at 0x1F0D
5. Game checked Bank 2 - but our Bank 2 checksum WAS valid
6. However, the game's save loading priority meant it still saw issues
7. Result: modifications didn't appear correctly in-game

## The Fix

In `pokemon_crystal_editor.py`, lines 41-45:

```python
# Checksum - Bank 1 (secondary/backup)
# Note: Despite the lower address range, this is the BACKUP bank
# The game loads Bank 2 (0x2000+) first; Bank 1 is fallback
CHECKSUM_OFFSET_BANK1 = 0x1F0D      # Was 0x1F69
CHECKSUM_DATA_START_BANK1 = 0x1209  # Unchanged
CHECKSUM_DATA_END_BANK1 = 0x1D82    # Was 0x1F68
```

## Pokemon Crystal Save Structure Reference

### Bank 1 (Secondary/Backup) - 0x1200 range
| Data | Offset |
|------|--------|
| Checksum data start | 0x1209 |
| Items pocket count | 0x161A |
| Balls pocket count | 0x1665 |
| Checksum data end | 0x1D82 |
| Checksum storage | 0x1F0D |

### Bank 2 (Primary) - 0x2000 range
| Data | Offset |
|------|--------|
| Checksum data start | 0x2009 |
| Player name | 0x200B |
| Money (BCD) | 0x23DC |
| Items pocket count | 0x241A |
| Balls pocket count | 0x2465 |
| Party count | 0x2865 |
| Party data | 0x286D |
| Checksum data end | 0x2D68 |
| Checksum storage | 0x2D69 |

## Verification Commands

To verify checksums are valid:

```python
python3 -c "
data = open('savefile.srm', 'rb').read()

# Bank 1 (secondary)
calc1 = sum(data[0x1209:0x1D83]) & 0xFFFF
stored1 = data[0x1F0D] | (data[0x1F0E] << 8)
print(f'Bank 1: calc=0x{calc1:04X} stored=0x{stored1:04X} - {\"OK\" if calc1==stored1 else \"BAD\"}')

# Bank 2 (primary)
calc2 = sum(data[0x2009:0x2D69]) & 0xFFFF
stored2 = data[0x2D69] | (data[0x2D6A] << 8)
print(f'Bank 2: calc=0x{calc2:04X} stored=0x{stored2:04X} - {\"OK\" if calc2==stored2 else \"BAD\"}')
"
```

## Creating a Working Backup

After applying edits with the fixed script:

```bash
# Create a "golden" backup you can restore from
cp "Pokemon - Crystal Version (USA, Europe) (Rev 1).srm" \
   "Pokemon - Crystal Version (USA, Europe) (Rev 1).srm.99masterballs_working"
```

---

# Replacing Pokemon (Adding Legendaries)

## Key Discovery: BOTH Banks Must Be Updated

Pokemon Crystal duplicates party data in both save banks. If you only update Bank 2, the game may still show the old Pokemon. **You must update both banks for changes to appear in-game.**

## Party Data Structure

```
Bank 2 (Primary - 0x2000+ range):
  Party count:      0x2865 (1 byte)
  Species list:     0x2866 (6 bytes + terminator)
  Pokemon data:     0x286D (6 × 48 bytes = 288 bytes)
  OT names:         0x298D (6 × 11 bytes = 66 bytes)
  Nicknames:        0x29CF (6 × 11 bytes = 66 bytes)

Bank 1 (Secondary - 0x1200+ range):
  Subtract 0x0E00 from Bank 2 offsets:
  Party count:      0x1A65
  Species list:     0x1A66
  Pokemon data:     0x1A6D
  OT names:         0x1B8D
  Nicknames:        0x1BCF
```

## Pokemon Data Structure (48 bytes per Pokemon)

| Offset | Size | Field |
|--------|------|-------|
| 0x00 | 1 | Species ID |
| 0x01 | 1 | Held Item |
| 0x02 | 1 | Move 1 |
| 0x03 | 1 | Move 2 |
| 0x04 | 1 | Move 3 |
| 0x05 | 1 | Move 4 |
| 0x06 | 2 | OT ID |
| 0x08 | 3 | Experience |
| 0x0B | 2 | HP EV |
| 0x0D | 2 | Attack EV |
| 0x0F | 2 | Defense EV |
| 0x11 | 2 | Speed EV |
| 0x13 | 2 | Special EV |
| 0x15 | 2 | DVs (IVs) - packed |
| 0x17 | 1 | PP Move 1 |
| 0x18 | 1 | PP Move 2 |
| 0x19 | 1 | PP Move 3 |
| 0x1A | 1 | PP Move 4 |
| 0x1B | 1 | Friendship |
| 0x1C | 1 | Pokerus |
| 0x1D | 2 | Caught Data |
| 0x1F | 1 | Level |
| 0x20 | 1 | Status |
| 0x22 | 2 | Current HP |
| 0x24 | 2 | Max HP |
| 0x26 | 2 | Attack |
| 0x28 | 2 | Defense |
| 0x2A | 2 | Speed |
| 0x2C | 2 | Special Attack |
| 0x2E | 2 | Special Defense |

## Legendary Beast Species IDs

| Pokemon | ID (decimal) | ID (hex) |
|---------|--------------|----------|
| Raikou | 243 | 0xF3 |
| Entei | 244 | 0xF4 |
| Suicune | 245 | 0xF5 |

## Recommended Movesets

**Suicune:**
- Surf (57), Ice Beam (58), Rain Dance (240), Aurora Beam (62)
- PP: 15, 10, 5, 20

**Raikou:**
- Thunderbolt (85), Thunder (87), Crunch (242), Roar (46)
- PP: 15, 10, 15, 20

**Entei:**
- Flamethrower (53), Fire Blast (126), Stomp (23), Roar (46)
- PP: 15, 5, 20, 20

## Shiny DVs (Gen 2)

To make a Pokemon shiny, set DVs to: Attack=15, Defense=10, Speed=10, Special=10

```python
dv_bytes = (15 << 12) | (10 << 8) | (10 << 4) | 10  # = 0xFAAA
data[offset + 0x15] = 0xFA
data[offset + 0x16] = 0xAA
```

## Text Encoding (for Nicknames)

Pokemon Crystal uses custom text encoding:

```python
# A-Z = 0x80-0x99
# Terminator = 0x50

def encode_name(name):
    result = []
    for c in name.upper():
        if 'A' <= c <= 'Z':
            result.append(0x80 + ord(c) - ord('A'))
        else:
            result.append(0x50)  # terminator for unknown chars
    while len(result) < 11:
        result.append(0x50)  # pad to 11 bytes
    return bytes(result)
```

## Complete Example: Replace Pokemon with Suicune

```python
data = bytearray(open('save.srm', 'rb').read())

SUICUNE = 245
slot = 6  # Which party slot to replace (1-6)

# Offsets for both banks
BANKS = [
    {'species_list': 0x2866, 'party_data': 0x286D, 'nicknames': 0x29CF},  # Bank 2
    {'species_list': 0x1A66, 'party_data': 0x1A6D, 'nicknames': 0x1BCF},  # Bank 1
]

for bank in BANKS:
    # Update species list
    data[bank['species_list'] + slot - 1] = SUICUNE

    # Update Pokemon data
    offset = bank['party_data'] + (slot - 1) * 48
    data[offset + 0x00] = SUICUNE      # Species
    data[offset + 0x1F] = 40           # Level
    data[offset + 0x02] = 57           # Surf
    data[offset + 0x03] = 58           # Ice Beam
    data[offset + 0x04] = 240          # Rain Dance
    data[offset + 0x05] = 62           # Aurora Beam
    data[offset + 0x17:0x1B] = bytes([15, 10, 5, 20])  # PP
    data[offset + 0x15] = 0xFA         # Shiny DVs
    data[offset + 0x16] = 0xAA
    # ... set EVs, HP, etc.

    # Update nickname
    nick_offset = bank['nicknames'] + (slot - 1) * 11
    nickname = bytes([0x92, 0x94, 0x88, 0x82, 0x94, 0x8D, 0x84, 0x50, 0x50, 0x50, 0x50])  # SUICUNE
    data[nick_offset:nick_offset + 11] = nickname

# CRITICAL: Update BOTH checksums
cs1 = sum(data[0x1209:0x1D83]) & 0xFFFF
data[0x1F0D] = cs1 & 0xFF
data[0x1F0E] = (cs1 >> 8) & 0xFF

cs2 = sum(data[0x2009:0x2D69]) & 0xFFFF
data[0x2D69] = cs2 & 0xFF
data[0x2D6A] = (cs2 >> 8) & 0xFF

open('save.srm', 'wb').write(data)
```

## Checklist for Replacing Pokemon

1. ☐ Update species in **species list** (both banks)
2. ☐ Update species in **Pokemon data** (both banks)
3. ☐ Set level, moves, PP
4. ☐ Set DVs (use shiny values if desired)
5. ☐ Set EVs (max = 65535 per stat)
6. ☐ Set HP current/max
7. ☐ Clear status, set friendship
8. ☐ Update **nickname** (both banks)
9. ☐ Recalculate **BOTH checksums**
10. ☐ Sync filesystem before ejecting

## Source

- Bulbapedia save structure documentation
- Hex analysis of known-good Pokemon Crystal saves
- Verified by calculating expected checksums and comparing to stored values
