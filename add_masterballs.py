#!/usr/bin/env python3
"""
Pokemon Crystal Save Editor - Add Master Balls

Usage:
    python3 add_masterballs.py                           # Auto-find on /Volumes/JOE
    python3 add_masterballs.py /path/to/save.srm         # Specific save, 99 balls
    python3 add_masterballs.py /path/to/save.srm 50      # Specific save, 50 balls
    python3 add_masterballs.py --find                    # Find all Crystal saves
"""

import sys
import os
import glob
import shutil

# Pokemon Crystal (US/EU) save file offsets
BALL_POCKET_COUNT_OFFSET = 0x2465
BALL_POCKET_DATA_OFFSET = 0x2466
MAX_BALL_POCKET_SIZE = 12

# Item IDs
MASTER_BALL_ID = 0x01
BALL_NAMES = {
    0x01: 'Master Ball',
    0x02: 'Ultra Ball',
    0x03: 'Great Ball',
    0x04: 'Poke Ball',
    0x07: 'Safari Ball',
    0x09: 'Heavy Ball',
    0xA0: 'Level Ball',
    0xA1: 'Lure Ball',
    0xA2: 'Fast Ball',
    0xA4: 'Friend Ball',
    0xA5: 'Moon Ball',
    0xA6: 'Love Ball',
}

# Checksum
CHECKSUM_OFFSET = 0x2D69
CHECKSUM_DATA_START = 0x2009
CHECKSUM_DATA_END = 0x2D68


def find_crystal_saves():
    """Find all Pokemon Crystal save files on mounted volumes."""
    patterns = [
        "/Volumes/*/Saves/CurrentProfile/saves/Gambatte/*[Cc]rystal*.srm",
        "/Volumes/*/Saves/**/[Pp]okemon*[Cc]rystal*.srm",
        "/Volumes/*/**/*[Cc]rystal*.sav",
    ]
    saves = []
    for pattern in patterns:
        saves.extend(glob.glob(pattern, recursive=True))
    # Filter out macOS resource forks
    saves = [s for s in saves if not os.path.basename(s).startswith('._')]
    return saves


def calculate_checksum(data, start, end):
    """Calculate the 16-bit checksum for Pokemon Crystal save data."""
    checksum = 0
    for i in range(start, end + 1):
        checksum = (checksum + data[i]) & 0xFFFF
    return checksum


def show_ball_pocket(data):
    """Display current ball pocket contents."""
    ball_count = data[BALL_POCKET_COUNT_OFFSET]
    print(f"\nCurrent ball pocket ({ball_count} types):")
    for i in range(ball_count):
        item_offset = BALL_POCKET_DATA_OFFSET + (i * 2)
        item_id = data[item_offset]
        item_qty = data[item_offset + 1]
        name = BALL_NAMES.get(item_id, f'Unknown (0x{item_id:02X})')
        print(f"  {name}: x{item_qty}")


def add_master_balls(save_path, quantity=99):
    """Add Master Balls to the ball pocket."""

    # Create backup
    backup_path = save_path + '.backup_before_masterballs'
    if not os.path.exists(backup_path):
        shutil.copy2(save_path, backup_path)
        print(f"Created backup: {backup_path}")

    # Read save file
    with open(save_path, 'rb') as f:
        data = bytearray(f.read())

    if len(data) != 32768:
        print(f"Warning: Unexpected save size {len(data)} bytes (expected 32768)")

    show_ball_pocket(data)

    # Look for existing Master Ball
    ball_count = data[BALL_POCKET_COUNT_OFFSET]
    master_ball_found = False

    for i in range(ball_count):
        item_offset = BALL_POCKET_DATA_OFFSET + (i * 2)
        if data[item_offset] == MASTER_BALL_ID:
            old_qty = data[item_offset + 1]
            data[item_offset + 1] = min(quantity, 99)
            master_ball_found = True
            print(f"\nUpdated Master Ball: {old_qty} -> {min(quantity, 99)}")
            break

    if not master_ball_found:
        if ball_count < MAX_BALL_POCKET_SIZE:
            new_slot = BALL_POCKET_DATA_OFFSET + (ball_count * 2)
            data[new_slot] = MASTER_BALL_ID
            data[new_slot + 1] = min(quantity, 99)
            data[BALL_POCKET_COUNT_OFFSET] = ball_count + 1
            print(f"\nAdded Master Ball x{min(quantity, 99)}")
        else:
            print("\nError: Ball pocket is full!")
            return False

    # Recalculate checksum
    new_checksum = calculate_checksum(data, CHECKSUM_DATA_START, CHECKSUM_DATA_END)
    data[CHECKSUM_OFFSET] = new_checksum & 0xFF
    data[CHECKSUM_OFFSET + 1] = (new_checksum >> 8) & 0xFF

    # Write modified save
    with open(save_path, 'wb') as f:
        f.write(data)

    print(f"\nSave updated! Checksum: 0x{new_checksum:04X}")
    return True


def main():
    # Handle --find flag
    if '--find' in sys.argv:
        print("Searching for Pokemon Crystal saves...\n")
        saves = find_crystal_saves()
        if saves:
            for s in saves:
                print(f"  {s}")
        else:
            print("No saves found. Make sure SD card is mounted.")
        return

    # Determine save path
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        save_path = sys.argv[1]
    else:
        # Default: look on JOE volume
        default_path = "/Volumes/JOE/Saves/CurrentProfile/saves/Gambatte/Pokemon - Crystal Version (USA, Europe) (Rev 1).srm"
        if os.path.exists(default_path):
            save_path = default_path
        else:
            # Try to find automatically
            saves = find_crystal_saves()
            if saves:
                save_path = saves[0]
                print(f"Auto-detected save: {save_path}")
            else:
                print("No save file found. Usage:")
                print("  python3 add_masterballs.py /path/to/save.srm [quantity]")
                print("  python3 add_masterballs.py --find")
                return

    if not os.path.exists(save_path):
        print(f"Error: Save file not found: {save_path}")
        return

    # Determine quantity
    quantity = 99
    if len(sys.argv) > 2:
        try:
            quantity = int(sys.argv[2])
        except ValueError:
            print(f"Invalid quantity: {sys.argv[2]}")
            return

    print(f"Save file: {save_path}")
    print(f"Adding: {quantity} Master Balls")

    add_master_balls(save_path, quantity)


if __name__ == "__main__":
    main()
