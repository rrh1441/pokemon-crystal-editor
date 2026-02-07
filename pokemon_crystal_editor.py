#!/usr/bin/env python3
"""
Pokemon Crystal Save Editor - Multi-purpose

Usage:
    python3 pokemon_crystal_editor.py                      # Interactive mode
    python3 pokemon_crystal_editor.py --find               # Find saves
    python3 pokemon_crystal_editor.py --info SAVE          # Show save info
    python3 pokemon_crystal_editor.py --masterballs SAVE   # Add 99 Master Balls
    python3 pokemon_crystal_editor.py --rarecandy SAVE     # Add 99 Rare Candies
    python3 pokemon_crystal_editor.py --money SAVE         # Max out money
    python3 pokemon_crystal_editor.py --allballs SAVE      # 99 of every ball type
    python3 pokemon_crystal_editor.py --Pokemon SAVE       # View Pokemon team
"""

import sys
import os
import glob
import shutil

# =============================================================================
# POKEMON CRYSTAL SAVE FILE STRUCTURE (US/EU)
# =============================================================================

# Checksum
CHECKSUM_OFFSET = 0x2D69
CHECKSUM_DATA_START = 0x2009
CHECKSUM_DATA_END = 0x2D68

# Player info
PLAYER_NAME_OFFSET = 0x200B
PLAYER_NAME_LENGTH = 11
PLAYER_ID_OFFSET = 0x2009
MONEY_OFFSET = 0x23DC  # 3 bytes, BCD encoded

# Inventory pockets
POCKETS = {
    'items': {'count': 0x241A, 'data': 0x241B, 'max_slots': 20},
    'key_items': {'count': 0x2449, 'data': 0x244A, 'max_slots': 25},
    'balls': {'count': 0x2465, 'data': 0x2466, 'max_slots': 12},
    'tm_hm': {'count': 0x247D, 'data': 0x247E, 'max_slots': 57},
}

# Pokemon team
TEAM_COUNT_OFFSET = 0x2865
TEAM_DATA_OFFSET = 0x2867
POKEMON_SIZE = 48  # bytes per Pokemon

# =============================================================================
# ITEM DEFINITIONS
# =============================================================================

BALLS = {
    0x01: 'Master Ball',
    0x02: 'Ultra Ball',
    0x03: 'Great Ball',
    0x04: 'Poke Ball',
    0x07: 'Safari Ball',
    0xA0: 'Level Ball',
    0xA1: 'Lure Ball',
    0xA2: 'Fast Ball',
    0xA3: 'Heavy Ball',
    0xA4: 'Friend Ball',
    0xA5: 'Moon Ball',
    0xA6: 'Love Ball',
}

ITEMS = {
    0x01: 'Master Ball',
    0x02: 'Ultra Ball',
    0x03: 'Great Ball',
    0x04: 'Poke Ball',
    0x08: 'Rare Candy',
    0x09: 'Bike Voucher',
    0x0A: 'Potion',
    0x0B: 'Super Potion',
    0x0C: 'Hyper Potion',
    0x0D: 'Max Potion',
    0x0E: 'Full Restore',
    0x0F: 'Revive',
    0x10: 'Max Revive',
    0x11: 'Elixir',
    0x12: 'Max Elixir',
    0x13: 'Ether',
    0x14: 'Max Ether',
    0x19: 'Full Heal',
    0x1E: 'Nugget',
    0x1F: 'PP Up',
    0x23: 'Escape Rope',
    0x24: 'Repel',
    0x25: 'Super Repel',
    0x26: 'Max Repel',
    0x2D: 'HP Up',
    0x2E: 'Protein',
    0x2F: 'Iron',
    0x30: 'Carbos',
    0x31: 'Calcium',
    0x4A: 'PP Max',
}

POKEMON_NAMES = {
    1: 'Bulbasaur', 2: 'Ivysaur', 3: 'Venusaur', 4: 'Charmander', 5: 'Charmeleon',
    6: 'Charizard', 7: 'Squirtle', 8: 'Wartortle', 9: 'Blastoise', 25: 'Pikachu',
    26: 'Raichu', 150: 'Mewtwo', 151: 'Mew', 152: 'Chikorita', 155: 'Cyndaquil',
    158: 'Totodile', 243: 'Raikou', 244: 'Entei', 245: 'Suicune', 249: 'Lugia',
    250: 'Ho-Oh', 251: 'Celebi',
    # Add more as needed
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def find_saves():
    """Find Pokemon Crystal saves on mounted volumes."""
    patterns = [
        "/Volumes/*/Saves/CurrentProfile/saves/Gambatte/*[Cc]rystal*.srm",
        "/Volumes/*/Saves/**/*[Cc]rystal*.srm",
        "/Volumes/*/**/*[Cc]rystal*.sav",
    ]
    saves = []
    for pattern in patterns:
        saves.extend(glob.glob(pattern, recursive=True))
    return [s for s in saves if not os.path.basename(s).startswith('._')]


def backup_save(path):
    """Create backup if not exists."""
    backup = path + '.backup_original'
    if not os.path.exists(backup):
        shutil.copy2(path, backup)
        print(f"Backup created: {backup}")


def calculate_checksum(data):
    """Calculate Pokemon Crystal checksum."""
    checksum = 0
    for i in range(CHECKSUM_DATA_START, CHECKSUM_DATA_END + 1):
        checksum = (checksum + data[i]) & 0xFFFF
    return checksum


def update_checksum(data):
    """Recalculate and update checksum in save data."""
    checksum = calculate_checksum(data)
    data[CHECKSUM_OFFSET] = checksum & 0xFF
    data[CHECKSUM_OFFSET + 1] = (checksum >> 8) & 0xFF
    return checksum


def read_save(path):
    """Read save file."""
    with open(path, 'rb') as f:
        return bytearray(f.read())


def write_save(path, data):
    """Write save file with updated checksum."""
    update_checksum(data)
    with open(path, 'wb') as f:
        f.write(data)


def decode_name(data, offset, length):
    """Decode Pokemon text to ASCII."""
    chars = {
        0x80: 'A', 0x81: 'B', 0x82: 'C', 0x83: 'D', 0x84: 'E', 0x85: 'F',
        0x86: 'G', 0x87: 'H', 0x88: 'I', 0x89: 'J', 0x8A: 'K', 0x8B: 'L',
        0x8C: 'M', 0x8D: 'N', 0x8E: 'O', 0x8F: 'P', 0x90: 'Q', 0x91: 'R',
        0x92: 'S', 0x93: 'T', 0x94: 'U', 0x95: 'V', 0x96: 'W', 0x97: 'X',
        0x98: 'Y', 0x99: 'Z',
        0xA0: 'a', 0xA1: 'b', 0xA2: 'c', 0xA3: 'd', 0xA4: 'e', 0xA5: 'f',
        0xA6: 'g', 0xA7: 'h', 0xA8: 'i', 0xA9: 'j', 0xAA: 'k', 0xAB: 'l',
        0xAC: 'm', 0xAD: 'n', 0xAE: 'o', 0xAF: 'p', 0xB0: 'q', 0xB1: 'r',
        0xB2: 's', 0xB3: 't', 0xB4: 'u', 0xB5: 'v', 0xB6: 'w', 0xB7: 'x',
        0xB8: 'y', 0xB9: 'z',
        0x50: '', 0x7F: ' ', 0xE3: '-', 0xE8: '.', 0xEF: '♂', 0xF5: '♀',
    }
    name = ''
    for i in range(length):
        byte = data[offset + i]
        if byte == 0x50:  # Terminator
            break
        name += chars.get(byte, '?')
    return name


def bcd_to_int(data, offset, length):
    """Convert BCD encoded bytes to integer."""
    value = 0
    for i in range(length):
        byte = data[offset + i]
        value = value * 100 + ((byte >> 4) * 10) + (byte & 0x0F)
    return value


def int_to_bcd(value, length):
    """Convert integer to BCD encoded bytes."""
    result = []
    for _ in range(length):
        low = value % 10
        value //= 10
        high = value % 10
        value //= 10
        result.insert(0, (high << 4) | low)
    return bytes(result)


# =============================================================================
# EDIT FUNCTIONS
# =============================================================================

def show_info(data):
    """Display save file information."""
    name = decode_name(data, PLAYER_NAME_OFFSET, PLAYER_NAME_LENGTH)
    trainer_id = (data[PLAYER_ID_OFFSET] << 8) | data[PLAYER_ID_OFFSET + 1]
    money = bcd_to_int(data, MONEY_OFFSET, 3)

    print(f"\n{'='*40}")
    print(f"Player: {name}")
    print(f"Trainer ID: {trainer_id}")
    print(f"Money: ${money:,}")
    print(f"{'='*40}")

    # Show main pockets (skip key_items and tm_hm as offsets may vary)
    for pocket_name in ['items', 'balls']:
        pocket = POCKETS[pocket_name]
        count = data[pocket['count']]
        if count > pocket['max_slots']:  # Sanity check
            continue
        print(f"\n{pocket_name.upper()} ({count} types):")
        lookup = BALLS if pocket_name == 'balls' else ITEMS
        for i in range(count):
            item_id = data[pocket['data'] + i * 2]
            qty = data[pocket['data'] + i * 2 + 1]
            name = lookup.get(item_id, f'Item 0x{item_id:02X}')
            print(f"  {name}: x{qty}")


def show_team(data):
    """Display Pokemon team."""
    count = data[TEAM_COUNT_OFFSET]
    print(f"\nPokemon Team ({count}/6):")
    print("-" * 40)

    for i in range(count):
        offset = TEAM_DATA_OFFSET + i * POKEMON_SIZE
        species = data[offset]
        level = data[offset + 31]  # Level offset within Pokemon struct
        name = POKEMON_NAMES.get(species, f'Pokemon #{species}')
        print(f"  {i+1}. {name} (Lv.{level})")


def add_item_to_pocket(data, pocket_name, item_id, quantity=99):
    """Add or update an item in a pocket."""
    pocket = POCKETS[pocket_name]
    count = data[pocket['count']]

    # Check if item exists
    for i in range(count):
        offset = pocket['data'] + i * 2
        if data[offset] == item_id:
            old = data[offset + 1]
            data[offset + 1] = min(quantity, 99)
            return f"Updated quantity: {old} -> {min(quantity, 99)}"

    # Add new item
    if count < pocket['max_slots']:
        offset = pocket['data'] + count * 2
        data[offset] = item_id
        data[offset + 1] = min(quantity, 99)
        data[pocket['count']] = count + 1
        return f"Added x{min(quantity, 99)}"
    else:
        return "Pocket full!"


def add_master_balls(data, qty=99):
    """Add Master Balls."""
    result = add_item_to_pocket(data, 'balls', 0x01, qty)
    print(f"Master Ball: {result}")


def add_rare_candy(data, qty=99):
    """Add Rare Candies."""
    result = add_item_to_pocket(data, 'items', 0x08, qty)
    print(f"Rare Candy: {result}")


def add_all_balls(data, qty=99):
    """Add all ball types."""
    for ball_id, ball_name in BALLS.items():
        result = add_item_to_pocket(data, 'balls', ball_id, qty)
        print(f"{ball_name}: {result}")


def max_money(data):
    """Set money to maximum (999999)."""
    bcd = int_to_bcd(999999, 3)
    for i, b in enumerate(bcd):
        data[MONEY_OFFSET + i] = b
    print("Money set to $999,999")


def add_healing_items(data, qty=99):
    """Add healing items."""
    items = [
        (0x0D, 'Max Potion'),
        (0x0E, 'Full Restore'),
        (0x10, 'Max Revive'),
        (0x12, 'Max Elixir'),
        (0x19, 'Full Heal'),
    ]
    for item_id, name in items:
        result = add_item_to_pocket(data, 'items', item_id, qty)
        print(f"{name}: {result}")


def add_stat_items(data, qty=99):
    """Add stat-boosting items."""
    items = [
        (0x08, 'Rare Candy'),
        (0x2D, 'HP Up'),
        (0x2E, 'Protein'),
        (0x2F, 'Iron'),
        (0x30, 'Carbos'),
        (0x31, 'Calcium'),
        (0x4A, 'PP Max'),
    ]
    for item_id, name in items:
        result = add_item_to_pocket(data, 'items', item_id, qty)
        print(f"{name}: {result}")


# =============================================================================
# MAIN
# =============================================================================

def get_save_path():
    """Get save path from args or find automatically."""
    # Check for explicit path in args
    for arg in sys.argv[1:]:
        if not arg.startswith('--') and os.path.exists(arg):
            return arg

    # Try default location
    default = "/Volumes/JOE/Saves/CurrentProfile/saves/Gambatte/Pokemon - Crystal Version (USA, Europe) (Rev 1).srm"
    if os.path.exists(default):
        return default

    # Auto-find
    saves = find_saves()
    if saves:
        return saves[0]

    return None


def main():
    args = sys.argv[1:]

    # Find saves
    if '--find' in args:
        saves = find_saves()
        if saves:
            print("Found saves:")
            for s in saves:
                print(f"  {s}")
        else:
            print("No saves found")
        return

    # Get save path
    save_path = get_save_path()
    if not save_path:
        print("No save file found. Use --find or specify path.")
        return

    print(f"Save: {save_path}")
    data = read_save(save_path)
    backup_save(save_path)

    # Commands
    if '--info' in args:
        show_info(data)
        return

    if '--pokemon' in args or '--team' in args:
        show_team(data)
        return

    modified = False

    if '--masterballs' in args:
        add_master_balls(data)
        modified = True

    if '--rarecandy' in args:
        add_rare_candy(data)
        modified = True

    if '--allballs' in args:
        add_all_balls(data)
        modified = True

    if '--money' in args:
        max_money(data)
        modified = True

    if '--healing' in args:
        add_healing_items(data)
        modified = True

    if '--stats' in args:
        add_stat_items(data)
        modified = True

    if '--all' in args:
        add_master_balls(data)
        add_all_balls(data)
        add_rare_candy(data)
        add_healing_items(data)
        add_stat_items(data)
        max_money(data)
        modified = True

    # Interactive mode if no commands
    if not modified and not any(a.startswith('--') for a in args):
        print("\nAvailable commands:")
        print("  --info         Show save info")
        print("  --pokemon      Show Pokemon team")
        print("  --masterballs  Add 99 Master Balls")
        print("  --rarecandy    Add 99 Rare Candies")
        print("  --allballs     Add 99 of every ball type")
        print("  --money        Max out money ($999,999)")
        print("  --healing      Add healing items")
        print("  --stats        Add stat items (Rare Candy, vitamins)")
        print("  --all          All of the above")
        print("\nExample: python3 pokemon_crystal_editor.py --masterballs --money")
        return

    if modified:
        write_save(save_path, data)
        print(f"\nSave updated!")


if __name__ == "__main__":
    main()
