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

## Source

- Bulbapedia save structure documentation
- Hex analysis of known-good Pokemon Crystal saves
- Verified by calculating expected checksums and comparing to stored values
