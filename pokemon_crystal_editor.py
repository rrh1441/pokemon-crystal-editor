#!/usr/bin/env python3
"""
Pokemon Crystal Save Editor - Full Featured

Usage:
    python3 pokemon_crystal_editor.py                      # Show help
    python3 pokemon_crystal_editor.py --find               # Find saves
    python3 pokemon_crystal_editor.py --info               # Show save info
    python3 pokemon_crystal_editor.py --pokemon            # Show team details
    python3 pokemon_crystal_editor.py --masterballs        # Add 99 Master Balls
    python3 pokemon_crystal_editor.py --rarecandy          # Add 99 Rare Candies
    python3 pokemon_crystal_editor.py --money              # Max out money
    python3 pokemon_crystal_editor.py --allballs           # 99 of every ball type
    python3 pokemon_crystal_editor.py --shiny 1            # Make Pokemon #1 shiny
    python3 pokemon_crystal_editor.py --shiny all          # Make all Pokemon shiny
    python3 pokemon_crystal_editor.py --maxstats 1         # Max IVs/EVs for Pokemon #1
    python3 pokemon_crystal_editor.py --level 1 100        # Set Pokemon #1 to level 100
    python3 pokemon_crystal_editor.py --heal               # Fully heal all Pokemon
"""

import sys
import os
import glob
import shutil
import struct

# =============================================================================
# POKEMON CRYSTAL SAVE FILE STRUCTURE (US/EU)
# =============================================================================

# Pokemon Crystal has TWO save banks - must edit BOTH!
# Bank 1 (0x1200+ range): secondary/backup bank
# Bank 2 (0x2000+ range): primary bank - what the game actually loads first
# If Bank 2's checksum fails, game falls back to Bank 1
BANK1_OFFSET = 0x0E00  # Offset difference between banks

# Checksum - Bank 2 (primary - what the game loads first)
CHECKSUM_OFFSET = 0x2D69
CHECKSUM_DATA_START = 0x2009
CHECKSUM_DATA_END = 0x2D68

# Checksum - Bank 1 (secondary/backup)
# Note: Despite the lower address range, this is the BACKUP bank
# The game loads Bank 2 (0x2000+) first; Bank 1 is fallback
CHECKSUM_OFFSET_BANK1 = 0x1F0D
CHECKSUM_DATA_START_BANK1 = 0x1209
CHECKSUM_DATA_END_BANK1 = 0x1D82

# Player info
PLAYER_NAME_OFFSET = 0x200B
PLAYER_NAME_LENGTH = 11
PLAYER_ID_OFFSET = 0x2009
MONEY_OFFSET = 0x23DC  # 3 bytes, BCD encoded

# Inventory pockets - Bank 2 (primary - what the game loads first)
POCKETS = {
    'items': {'count': 0x241A, 'data': 0x241B, 'max_slots': 20},
    'balls': {'count': 0x2465, 'data': 0x2466, 'max_slots': 12},
}

# Inventory pockets - Bank 1 (secondary/backup)
POCKETS_BANK1 = {
    'items': {'count': 0x161A, 'data': 0x161B, 'max_slots': 20},
    'balls': {'count': 0x1665, 'data': 0x1666, 'max_slots': 12},
}

# Pokemon party
PARTY_COUNT_OFFSET = 0x2865
PARTY_SPECIES_OFFSET = 0x2866  # 6 bytes + terminator
PARTY_DATA_OFFSET = 0x286D     # Pokemon data starts here (after species list + terminator)

# Party Pokemon structure (48 bytes each)
# Offset within each Pokemon:
PKMN_SPECIES = 0x00
PKMN_ITEM = 0x01
PKMN_MOVE1 = 0x02
PKMN_MOVE2 = 0x03
PKMN_MOVE3 = 0x04
PKMN_MOVE4 = 0x05
PKMN_OT_ID = 0x06        # 2 bytes
PKMN_EXP = 0x08          # 3 bytes
PKMN_HP_EV = 0x0B        # 2 bytes
PKMN_ATK_EV = 0x0D       # 2 bytes
PKMN_DEF_EV = 0x0F       # 2 bytes
PKMN_SPD_EV = 0x11       # 2 bytes
PKMN_SPC_EV = 0x13       # 2 bytes
PKMN_DVS = 0x15          # 2 bytes (IVs) - packed nibbles
PKMN_PP1 = 0x17
PKMN_PP2 = 0x18
PKMN_PP3 = 0x19
PKMN_PP4 = 0x1A
PKMN_FRIENDSHIP = 0x1B
PKMN_POKERUS = 0x1C
PKMN_CAUGHT_DATA = 0x1D  # 2 bytes
PKMN_LEVEL = 0x1F
PKMN_STATUS = 0x20
PKMN_HP_CURRENT = 0x22   # 2 bytes
PKMN_HP_MAX = 0x24       # 2 bytes
PKMN_ATK = 0x26          # 2 bytes
PKMN_DEF = 0x28          # 2 bytes
PKMN_SPD = 0x2A          # 2 bytes
PKMN_SPC_ATK = 0x2C      # 2 bytes
PKMN_SPC_DEF = 0x2E      # 2 bytes

PARTY_POKEMON_SIZE = 48

# =============================================================================
# DATA TABLES
# =============================================================================

BALLS = {
    0x01: 'Master Ball', 0x02: 'Ultra Ball', 0x03: 'Great Ball', 0x04: 'Poke Ball',
    0x07: 'Safari Ball', 0xA0: 'Level Ball', 0xA1: 'Lure Ball', 0xA2: 'Fast Ball',
    0xA3: 'Heavy Ball', 0xA4: 'Friend Ball', 0xA5: 'Moon Ball', 0xA6: 'Love Ball',
}

ITEMS = {
    0x01: 'Master Ball', 0x02: 'Ultra Ball', 0x03: 'Great Ball', 0x04: 'Poke Ball',
    0x08: 'Rare Candy', 0x0D: 'Max Potion', 0x0E: 'Full Restore', 0x10: 'Max Revive',
    0x12: 'Max Elixir', 0x19: 'Full Heal', 0x1E: 'Nugget', 0x2D: 'HP Up',
    0x2E: 'Protein', 0x2F: 'Iron', 0x30: 'Carbos', 0x31: 'Calcium', 0x4A: 'PP Max',
}

# Pokemon species (Gen 2 index)
POKEMON = {
    1: 'Bulbasaur', 2: 'Ivysaur', 3: 'Venusaur', 4: 'Charmander', 5: 'Charmeleon',
    6: 'Charizard', 7: 'Squirtle', 8: 'Wartortle', 9: 'Blastoise', 10: 'Caterpie',
    11: 'Metapod', 12: 'Butterfree', 13: 'Weedle', 14: 'Kakuna', 15: 'Beedrill',
    16: 'Pidgey', 17: 'Pidgeotto', 18: 'Pidgeot', 19: 'Rattata', 20: 'Raticate',
    21: 'Spearow', 22: 'Fearow', 23: 'Ekans', 24: 'Arbok', 25: 'Pikachu',
    26: 'Raichu', 27: 'Sandshrew', 28: 'Sandslash', 29: 'Nidoran♀', 30: 'Nidorina',
    31: 'Nidoqueen', 32: 'Nidoran♂', 33: 'Nidorino', 34: 'Nidoking', 35: 'Clefairy',
    36: 'Clefable', 37: 'Vulpix', 38: 'Ninetales', 39: 'Jigglypuff', 40: 'Wigglytuff',
    41: 'Zubat', 42: 'Golbat', 43: 'Oddish', 44: 'Gloom', 45: 'Vileplume',
    46: 'Paras', 47: 'Parasect', 48: 'Venonat', 49: 'Venomoth', 50: 'Diglett',
    51: 'Dugtrio', 52: 'Meowth', 53: 'Persian', 54: 'Psyduck', 55: 'Golduck',
    56: 'Mankey', 57: 'Primeape', 58: 'Growlithe', 59: 'Arcanine', 60: 'Poliwag',
    61: 'Poliwhirl', 62: 'Poliwrath', 63: 'Abra', 64: 'Kadabra', 65: 'Alakazam',
    66: 'Machop', 67: 'Machoke', 68: 'Machamp', 69: 'Bellsprout', 70: 'Weepinbell',
    71: 'Victreebel', 72: 'Tentacool', 73: 'Tentacruel', 74: 'Geodude', 75: 'Graveler',
    76: 'Golem', 77: 'Ponyta', 78: 'Rapidash', 79: 'Slowpoke', 80: 'Slowbro',
    81: 'Magnemite', 82: 'Magneton', 83: 'Farfetchd', 84: 'Doduo', 85: 'Dodrio',
    86: 'Seel', 87: 'Dewgong', 88: 'Grimer', 89: 'Muk', 90: 'Shellder',
    91: 'Cloyster', 92: 'Gastly', 93: 'Haunter', 94: 'Gengar', 95: 'Onix',
    96: 'Drowzee', 97: 'Hypno', 98: 'Krabby', 99: 'Kingler', 100: 'Voltorb',
    101: 'Electrode', 102: 'Exeggcute', 103: 'Exeggutor', 104: 'Cubone', 105: 'Marowak',
    106: 'Hitmonlee', 107: 'Hitmonchan', 108: 'Lickitung', 109: 'Koffing', 110: 'Weezing',
    111: 'Rhyhorn', 112: 'Rhydon', 113: 'Chansey', 114: 'Tangela', 115: 'Kangaskhan',
    116: 'Horsea', 117: 'Seadra', 118: 'Goldeen', 119: 'Seaking', 120: 'Staryu',
    121: 'Starmie', 122: 'Mr. Mime', 123: 'Scyther', 124: 'Jynx', 125: 'Electabuzz',
    126: 'Magmar', 127: 'Pinsir', 128: 'Tauros', 129: 'Magikarp', 130: 'Gyarados',
    131: 'Lapras', 132: 'Ditto', 133: 'Eevee', 134: 'Vaporeon', 135: 'Jolteon',
    136: 'Flareon', 137: 'Porygon', 138: 'Omanyte', 139: 'Omastar', 140: 'Kabuto',
    141: 'Kabutops', 142: 'Aerodactyl', 143: 'Snorlax', 144: 'Articuno', 145: 'Zapdos',
    146: 'Moltres', 147: 'Dratini', 148: 'Dragonair', 149: 'Dragonite', 150: 'Mewtwo',
    151: 'Mew', 152: 'Chikorita', 153: 'Bayleef', 154: 'Meganium', 155: 'Cyndaquil',
    156: 'Quilava', 157: 'Typhlosion', 158: 'Totodile', 159: 'Croconaw', 160: 'Feraligatr',
    161: 'Sentret', 162: 'Furret', 163: 'Hoothoot', 164: 'Noctowl', 165: 'Ledyba',
    166: 'Ledian', 167: 'Spinarak', 168: 'Ariados', 169: 'Crobat', 170: 'Chinchou',
    171: 'Lanturn', 172: 'Pichu', 173: 'Cleffa', 174: 'Igglybuff', 175: 'Togepi',
    176: 'Togetic', 177: 'Natu', 178: 'Xatu', 179: 'Mareep', 180: 'Flaaffy',
    181: 'Ampharos', 182: 'Bellossom', 183: 'Marill', 184: 'Azumarill', 185: 'Sudowoodo',
    186: 'Politoed', 187: 'Hoppip', 188: 'Skiploom', 189: 'Jumpluff', 190: 'Aipom',
    191: 'Sunkern', 192: 'Sunflora', 193: 'Yanma', 194: 'Wooper', 195: 'Quagsire',
    196: 'Espeon', 197: 'Umbreon', 198: 'Murkrow', 199: 'Slowking', 200: 'Misdreavus',
    201: 'Unown', 202: 'Wobbuffet', 203: 'Girafarig', 204: 'Pineco', 205: 'Forretress',
    206: 'Dunsparce', 207: 'Gligar', 208: 'Steelix', 209: 'Snubbull', 210: 'Granbull',
    211: 'Qwilfish', 212: 'Scizor', 213: 'Shuckle', 214: 'Heracross', 215: 'Sneasel',
    216: 'Teddiursa', 217: 'Ursaring', 218: 'Slugma', 219: 'Magcargo', 220: 'Swinub',
    221: 'Piloswine', 222: 'Corsola', 223: 'Remoraid', 224: 'Octillery', 225: 'Delibird',
    226: 'Mantine', 227: 'Skarmory', 228: 'Houndour', 229: 'Houndoom', 230: 'Kingdra',
    231: 'Phanpy', 232: 'Donphan', 233: 'Porygon2', 234: 'Stantler', 235: 'Smeargle',
    236: 'Tyrogue', 237: 'Hitmontop', 238: 'Smoochum', 239: 'Elekid', 240: 'Magby',
    241: 'Miltank', 242: 'Blissey', 243: 'Raikou', 244: 'Entei', 245: 'Suicune',
    246: 'Larvitar', 247: 'Pupitar', 248: 'Tyranitar', 249: 'Lugia', 250: 'Ho-Oh',
    251: 'Celebi',
}

# Moves (Gen 2)
MOVES = {
    0: '—', 1: 'Pound', 2: 'Karate Chop', 3: 'Double Slap', 4: 'Comet Punch',
    5: 'Mega Punch', 6: 'Pay Day', 7: 'Fire Punch', 8: 'Ice Punch', 9: 'Thunder Punch',
    10: 'Scratch', 11: 'Vice Grip', 12: 'Guillotine', 13: 'Razor Wind', 14: 'Swords Dance',
    15: 'Cut', 16: 'Gust', 17: 'Wing Attack', 18: 'Whirlwind', 19: 'Fly',
    20: 'Bind', 21: 'Slam', 22: 'Vine Whip', 23: 'Stomp', 24: 'Double Kick',
    25: 'Mega Kick', 26: 'Jump Kick', 27: 'Rolling Kick', 28: 'Sand Attack', 29: 'Headbutt',
    30: 'Horn Attack', 31: 'Fury Attack', 32: 'Horn Drill', 33: 'Tackle', 34: 'Body Slam',
    35: 'Wrap', 36: 'Take Down', 37: 'Thrash', 38: 'Double-Edge', 39: 'Tail Whip',
    40: 'Poison Sting', 41: 'Twineedle', 42: 'Pin Missile', 43: 'Leer', 44: 'Bite',
    45: 'Growl', 46: 'Roar', 47: 'Sing', 48: 'Supersonic', 49: 'Sonic Boom',
    50: 'Disable', 51: 'Acid', 52: 'Ember', 53: 'Flamethrower', 54: 'Mist',
    55: 'Water Gun', 56: 'Hydro Pump', 57: 'Surf', 58: 'Ice Beam', 59: 'Blizzard',
    60: 'Psybeam', 61: 'Bubble Beam', 62: 'Aurora Beam', 63: 'Hyper Beam', 64: 'Peck',
    65: 'Drill Peck', 66: 'Submission', 67: 'Low Kick', 68: 'Counter', 69: 'Seismic Toss',
    70: 'Strength', 71: 'Absorb', 72: 'Mega Drain', 73: 'Leech Seed', 74: 'Growth',
    75: 'Razor Leaf', 76: 'Solar Beam', 77: 'Poison Powder', 78: 'Stun Spore', 79: 'Sleep Powder',
    80: 'Petal Dance', 81: 'String Shot', 82: 'Dragon Rage', 83: 'Fire Spin', 84: 'Thunder Shock',
    85: 'Thunderbolt', 86: 'Thunder Wave', 87: 'Thunder', 88: 'Rock Throw', 89: 'Earthquake',
    90: 'Fissure', 91: 'Dig', 92: 'Toxic', 93: 'Confusion', 94: 'Psychic',
    95: 'Hypnosis', 96: 'Meditate', 97: 'Agility', 98: 'Quick Attack', 99: 'Rage',
    100: 'Teleport', 101: 'Night Shade', 102: 'Mimic', 103: 'Screech', 104: 'Double Team',
    105: 'Recover', 106: 'Harden', 107: 'Minimize', 108: 'Smokescreen', 109: 'Confuse Ray',
    110: 'Withdraw', 111: 'Defense Curl', 112: 'Barrier', 113: 'Light Screen', 114: 'Haze',
    115: 'Reflect', 116: 'Focus Energy', 117: 'Bide', 118: 'Metronome', 119: 'Mirror Move',
    120: 'Self-Destruct', 121: 'Egg Bomb', 122: 'Lick', 123: 'Smog', 124: 'Sludge',
    125: 'Bone Club', 126: 'Fire Blast', 127: 'Waterfall', 128: 'Clamp', 129: 'Swift',
    130: 'Skull Bash', 131: 'Spike Cannon', 132: 'Constrict', 133: 'Amnesia', 134: 'Kinesis',
    135: 'Soft-Boiled', 136: 'High Jump Kick', 137: 'Glare', 138: 'Dream Eater', 139: 'Poison Gas',
    140: 'Barrage', 141: 'Leech Life', 142: 'Lovely Kiss', 143: 'Sky Attack', 144: 'Transform',
    145: 'Bubble', 146: 'Dizzy Punch', 147: 'Spore', 148: 'Flash', 149: 'Psywave',
    150: 'Splash', 151: 'Acid Armor', 152: 'Crabhammer', 153: 'Explosion', 154: 'Fury Swipes',
    155: 'Bonemerang', 156: 'Rest', 157: 'Rock Slide', 158: 'Hyper Fang', 159: 'Sharpen',
    160: 'Conversion', 161: 'Tri Attack', 162: 'Super Fang', 163: 'Slash', 164: 'Substitute',
    165: 'Struggle', 166: 'Sketch', 167: 'Triple Kick', 168: 'Thief', 169: 'Spider Web',
    170: 'Mind Reader', 171: 'Nightmare', 172: 'Flame Wheel', 173: 'Snore', 174: 'Curse',
    175: 'Flail', 176: 'Conversion 2', 177: 'Aeroblast', 178: 'Cotton Spore', 179: 'Reversal',
    180: 'Spite', 181: 'Powder Snow', 182: 'Protect', 183: 'Mach Punch', 184: 'Scary Face',
    185: 'Faint Attack', 186: 'Sweet Kiss', 187: 'Belly Drum', 188: 'Sludge Bomb', 189: 'Mud-Slap',
    190: 'Octazooka', 191: 'Spikes', 192: 'Zap Cannon', 193: 'Foresight', 194: 'Destiny Bond',
    195: 'Perish Song', 196: 'Icy Wind', 197: 'Detect', 198: 'Bone Rush', 199: 'Lock-On',
    200: 'Outrage', 201: 'Sandstorm', 202: 'Giga Drain', 203: 'Endure', 204: 'Charm',
    205: 'Rollout', 206: 'False Swipe', 207: 'Swagger', 208: 'Milk Drink', 209: 'Spark',
    210: 'Fury Cutter', 211: 'Steel Wing', 212: 'Mean Look', 213: 'Attract', 214: 'Sleep Talk',
    215: 'Heal Bell', 216: 'Return', 217: 'Present', 218: 'Frustration', 219: 'Safeguard',
    220: 'Pain Split', 221: 'Sacred Fire', 222: 'Magnitude', 223: 'Dynamic Punch', 224: 'Megahorn',
    225: 'Dragon Breath', 226: 'Baton Pass', 227: 'Encore', 228: 'Pursuit', 229: 'Rapid Spin',
    230: 'Sweet Scent', 231: 'Iron Tail', 232: 'Metal Claw', 233: 'Vital Throw', 234: 'Morning Sun',
    235: 'Synthesis', 236: 'Moonlight', 237: 'Hidden Power', 238: 'Cross Chop', 239: 'Twister',
    240: 'Rain Dance', 241: 'Sunny Day', 242: 'Crunch', 243: 'Mirror Coat', 244: 'Psych Up',
    245: 'Extreme Speed', 246: 'Ancient Power', 247: 'Shadow Ball', 248: 'Future Sight',
    249: 'Rock Smash', 250: 'Whirlpool', 251: 'Beat Up',
}

# Held items
HELD_ITEMS = {
    0: '(none)', 0x01: 'Master Ball', 0x02: 'Ultra Ball', 0x08: 'Rare Candy',
    0x0E: 'Full Restore', 0x1E: 'Nugget', 0x53: 'Leftovers', 0x54: 'Dragon Scale',
    0x64: 'Berry', 0x8B: 'Focus Band', 0x8E: 'Kings Rock', 0xAF: 'Lucky Egg',
    0xB4: 'Scope Lens', 0xC3: 'Quick Claw', 0xC4: 'Bright Powder',
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


def calculate_checksum(data, start, end):
    """Calculate Pokemon Crystal checksum for a given range."""
    checksum = 0
    for i in range(start, end + 1):
        checksum = (checksum + data[i]) & 0xFFFF
    return checksum


def update_checksum(data):
    """Recalculate and update checksums for BOTH save banks."""
    # Bank 1 (secondary/backup)
    checksum1 = calculate_checksum(data, CHECKSUM_DATA_START_BANK1, CHECKSUM_DATA_END_BANK1)
    data[CHECKSUM_OFFSET_BANK1] = checksum1 & 0xFF
    data[CHECKSUM_OFFSET_BANK1 + 1] = (checksum1 >> 8) & 0xFF

    # Bank 2 (primary - what game loads first)
    checksum2 = calculate_checksum(data, CHECKSUM_DATA_START, CHECKSUM_DATA_END)
    data[CHECKSUM_OFFSET] = checksum2 & 0xFF
    data[CHECKSUM_OFFSET + 1] = (checksum2 >> 8) & 0xFF

    return checksum1, checksum2


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


def get_pokemon_offset(slot):
    """Get the data offset for a party Pokemon (1-indexed)."""
    return PARTY_DATA_OFFSET + (slot - 1) * PARTY_POKEMON_SIZE


def read_word(data, offset):
    """Read 16-bit big-endian value."""
    return (data[offset] << 8) | data[offset + 1]


def write_word(data, offset, value):
    """Write 16-bit big-endian value."""
    data[offset] = (value >> 8) & 0xFF
    data[offset + 1] = value & 0xFF


def get_dvs(data, offset):
    """
    Get DVs (IVs) from 2-byte packed format.
    Format: AAAABBBB SSSSCCCC
    A=Attack, B=Defense, S=Speed, C=Special
    HP is derived: HP = (Atk&1)<<3 | (Def&1)<<2 | (Spd&1)<<1 | (Spc&1)
    """
    dv_bytes = (data[offset] << 8) | data[offset + 1]
    atk = (dv_bytes >> 12) & 0xF
    def_ = (dv_bytes >> 8) & 0xF
    spd = (dv_bytes >> 4) & 0xF
    spc = dv_bytes & 0xF
    hp = ((atk & 1) << 3) | ((def_ & 1) << 2) | ((spd & 1) << 1) | (spc & 1)
    return {'hp': hp, 'atk': atk, 'def': def_, 'spd': spd, 'spc': spc}


def set_dvs(data, offset, atk, def_, spd, spc):
    """Set DVs (IVs) in 2-byte packed format."""
    dv_bytes = (atk << 12) | (def_ << 8) | (spd << 4) | spc
    data[offset] = (dv_bytes >> 8) & 0xFF
    data[offset + 1] = dv_bytes & 0xFF


def is_shiny(dvs):
    """
    Check if DVs make a Pokemon shiny in Gen 2.
    Shiny requires: Spd=10, Def=10, Spc=10, Atk in {2,3,6,7,10,11,14,15}
    """
    if dvs['spd'] != 10 or dvs['def'] != 10 or dvs['spc'] != 10:
        return False
    return dvs['atk'] in [2, 3, 6, 7, 10, 11, 14, 15]


def make_shiny_dvs():
    """Return DVs that make a Pokemon shiny with good stats."""
    # Atk=15, Def=10, Spd=10, Spc=10 -> HP=15
    return {'atk': 15, 'def': 10, 'spd': 10, 'spc': 10}


def make_perfect_dvs():
    """Return perfect DVs (15 in all stats). Note: NOT shiny."""
    return {'atk': 15, 'def': 15, 'spd': 15, 'spc': 15}


# =============================================================================
# POKEMON FUNCTIONS
# =============================================================================

def get_party_pokemon(data, slot):
    """Get info for a party Pokemon (1-indexed slot)."""
    if slot < 1 or slot > 6:
        return None

    count = data[PARTY_COUNT_OFFSET]
    if slot > count:
        return None

    offset = get_pokemon_offset(slot)
    dvs = get_dvs(data, offset + PKMN_DVS)

    return {
        'slot': slot,
        'offset': offset,
        'species': data[offset + PKMN_SPECIES],
        'species_name': POKEMON.get(data[offset + PKMN_SPECIES], f"#{data[offset + PKMN_SPECIES]}"),
        'item': data[offset + PKMN_ITEM],
        'item_name': HELD_ITEMS.get(data[offset + PKMN_ITEM], f"Item #{data[offset + PKMN_ITEM]}"),
        'moves': [
            data[offset + PKMN_MOVE1],
            data[offset + PKMN_MOVE2],
            data[offset + PKMN_MOVE3],
            data[offset + PKMN_MOVE4],
        ],
        'move_names': [
            MOVES.get(data[offset + PKMN_MOVE1], '?'),
            MOVES.get(data[offset + PKMN_MOVE2], '?'),
            MOVES.get(data[offset + PKMN_MOVE3], '?'),
            MOVES.get(data[offset + PKMN_MOVE4], '?'),
        ],
        'level': data[offset + PKMN_LEVEL],
        'dvs': dvs,
        'is_shiny': is_shiny(dvs),
        'hp_ev': read_word(data, offset + PKMN_HP_EV),
        'atk_ev': read_word(data, offset + PKMN_ATK_EV),
        'def_ev': read_word(data, offset + PKMN_DEF_EV),
        'spd_ev': read_word(data, offset + PKMN_SPD_EV),
        'spc_ev': read_word(data, offset + PKMN_SPC_EV),
        'hp_current': read_word(data, offset + PKMN_HP_CURRENT),
        'hp_max': read_word(data, offset + PKMN_HP_MAX),
        'friendship': data[offset + PKMN_FRIENDSHIP],
    }


def show_pokemon(data, detailed=False):
    """Display Pokemon team."""
    count = data[PARTY_COUNT_OFFSET]
    print(f"\n{'='*50}")
    print(f"Pokemon Team ({count}/6)")
    print(f"{'='*50}")

    for i in range(1, count + 1):
        pkmn = get_party_pokemon(data, i)
        if not pkmn:
            continue

        shiny_star = "★ " if pkmn['is_shiny'] else ""
        print(f"\n{i}. {shiny_star}{pkmn['species_name']} (Lv.{pkmn['level']})")
        print(f"   Item: {pkmn['item_name']}")
        print(f"   Moves: {', '.join(m for m in pkmn['move_names'] if m != '—')}")

        if detailed:
            dvs = pkmn['dvs']
            print(f"   DVs (IVs): HP={dvs['hp']} Atk={dvs['atk']} Def={dvs['def']} Spd={dvs['spd']} Spc={dvs['spc']}")
            print(f"   EVs: HP={pkmn['hp_ev']} Atk={pkmn['atk_ev']} Def={pkmn['def_ev']} Spd={pkmn['spd_ev']} Spc={pkmn['spc_ev']}")
            print(f"   HP: {pkmn['hp_current']}/{pkmn['hp_max']}")
            print(f"   Friendship: {pkmn['friendship']}")


def make_pokemon_shiny(data, slot):
    """Make a Pokemon shiny by adjusting DVs."""
    pkmn = get_party_pokemon(data, slot)
    if not pkmn:
        print(f"No Pokemon in slot {slot}")
        return False

    if pkmn['is_shiny']:
        print(f"{pkmn['species_name']} is already shiny!")
        return False

    offset = pkmn['offset']
    shiny_dvs = make_shiny_dvs()
    set_dvs(data, offset + PKMN_DVS, shiny_dvs['atk'], shiny_dvs['def'], shiny_dvs['spd'], shiny_dvs['spc'])

    print(f"★ {pkmn['species_name']} is now SHINY!")
    return True


def max_pokemon_stats(data, slot):
    """Max out DVs and EVs for a Pokemon."""
    pkmn = get_party_pokemon(data, slot)
    if not pkmn:
        print(f"No Pokemon in slot {slot}")
        return False

    offset = pkmn['offset']

    # Max DVs (15 in all) - note this won't be shiny
    set_dvs(data, offset + PKMN_DVS, 15, 15, 15, 15)

    # Max EVs (65535 in all - Gen 2 uses "Stat Exp" which maxes at 65535)
    write_word(data, offset + PKMN_HP_EV, 65535)
    write_word(data, offset + PKMN_ATK_EV, 65535)
    write_word(data, offset + PKMN_DEF_EV, 65535)
    write_word(data, offset + PKMN_SPD_EV, 65535)
    write_word(data, offset + PKMN_SPC_EV, 65535)

    print(f"Maxed stats for {pkmn['species_name']}! (DVs=15, EVs=65535)")
    return True


def set_pokemon_level(data, slot, level):
    """Set a Pokemon's level."""
    pkmn = get_party_pokemon(data, slot)
    if not pkmn:
        print(f"No Pokemon in slot {slot}")
        return False

    level = max(1, min(100, level))
    offset = pkmn['offset']
    data[offset + PKMN_LEVEL] = level

    print(f"Set {pkmn['species_name']} to level {level}")
    return True


def heal_all_pokemon(data):
    """Fully heal all Pokemon (HP, PP, status)."""
    count = data[PARTY_COUNT_OFFSET]

    for i in range(1, count + 1):
        pkmn = get_party_pokemon(data, i)
        if not pkmn:
            continue

        offset = pkmn['offset']

        # Heal HP to max
        max_hp = read_word(data, offset + PKMN_HP_MAX)
        write_word(data, offset + PKMN_HP_CURRENT, max_hp)

        # Clear status
        data[offset + PKMN_STATUS] = 0

        # Restore PP (set to max for each move - simplified: set to 35 PP each)
        data[offset + PKMN_PP1] = 35
        data[offset + PKMN_PP2] = 35
        data[offset + PKMN_PP3] = 35
        data[offset + PKMN_PP4] = 35

    print(f"Healed all {count} Pokemon!")


def set_pokemon_move(data, slot, move_slot, move_id):
    """Set a Pokemon's move."""
    pkmn = get_party_pokemon(data, slot)
    if not pkmn:
        print(f"No Pokemon in slot {slot}")
        return False

    if move_slot < 1 or move_slot > 4:
        print("Move slot must be 1-4")
        return False

    offset = pkmn['offset']
    move_offsets = [PKMN_MOVE1, PKMN_MOVE2, PKMN_MOVE3, PKMN_MOVE4]
    data[offset + move_offsets[move_slot - 1]] = move_id

    move_name = MOVES.get(move_id, f"Move #{move_id}")
    print(f"Set {pkmn['species_name']} move {move_slot} to {move_name}")
    return True


def give_pokemon_item(data, slot, item_id):
    """Give a Pokemon a held item."""
    pkmn = get_party_pokemon(data, slot)
    if not pkmn:
        print(f"No Pokemon in slot {slot}")
        return False

    offset = pkmn['offset']
    data[offset + PKMN_ITEM] = item_id

    item_name = HELD_ITEMS.get(item_id, f"Item #{item_id}")
    print(f"Gave {pkmn['species_name']} a {item_name}")
    return True


def set_pokemon_species(data, slot, species_id, level=None):
    """Change a Pokemon's species (transform it into another Pokemon)."""
    pkmn = get_party_pokemon(data, slot)
    if not pkmn:
        print(f"No Pokemon in slot {slot}")
        return False

    old_name = pkmn['species_name']
    new_name = POKEMON.get(species_id, f"#{species_id}")
    offset = pkmn['offset']

    # Update species in party list (0x2866 + slot-1)
    data[PARTY_SPECIES_OFFSET + slot - 1] = species_id

    # Update species in Pokemon data
    data[offset + PKMN_SPECIES] = species_id

    # Update level if specified
    if level:
        data[offset + PKMN_LEVEL] = min(100, max(1, level))

    print(f"Transformed {old_name} into {new_name}!")
    return True


def add_suicune(data, slot):
    """Replace a Pokemon with Suicune (for Ho-Oh quest)."""
    SUICUNE_ID = 245

    pkmn = get_party_pokemon(data, slot)
    if not pkmn:
        print(f"No Pokemon in slot {slot}")
        return False

    old_name = pkmn['species_name']
    offset = pkmn['offset']

    # Set species to Suicune
    data[PARTY_SPECIES_OFFSET + slot - 1] = SUICUNE_ID
    data[offset + PKMN_SPECIES] = SUICUNE_ID

    # Set level 40 (encounter level)
    data[offset + PKMN_LEVEL] = 40

    # Give good moves: Surf, Ice Beam, Rain Dance, Aurora Beam
    data[offset + PKMN_MOVE1] = 57   # Surf
    data[offset + PKMN_MOVE2] = 58   # Ice Beam
    data[offset + PKMN_MOVE3] = 240  # Rain Dance
    data[offset + PKMN_MOVE4] = 62   # Aurora Beam

    # Set PP for moves
    data[offset + PKMN_PP1] = 15  # Surf
    data[offset + PKMN_PP2] = 10  # Ice Beam
    data[offset + PKMN_PP3] = 5   # Rain Dance
    data[offset + PKMN_PP4] = 20  # Aurora Beam

    # Give it shiny DVs (it's a legendary, why not)
    set_dvs(data, offset + PKMN_DVS, 15, 10, 10, 10)

    # Max EVs for good stats
    write_word(data, offset + PKMN_HP_EV, 65535)
    write_word(data, offset + PKMN_ATK_EV, 65535)
    write_word(data, offset + PKMN_DEF_EV, 65535)
    write_word(data, offset + PKMN_SPD_EV, 65535)
    write_word(data, offset + PKMN_SPC_EV, 65535)

    # Set reasonable HP (Suicune base HP 100, at lvl 40 ~140-150)
    write_word(data, offset + PKMN_HP_MAX, 160)
    write_word(data, offset + PKMN_HP_CURRENT, 160)

    # Clear status, max friendship
    data[offset + PKMN_STATUS] = 0
    data[offset + PKMN_FRIENDSHIP] = 255

    # No held item
    data[offset + PKMN_ITEM] = 0

    print(f"★ Replaced {old_name} with a SHINY Suicune (Lv.40)!")
    print("  Moves: Surf, Ice Beam, Rain Dance, Aurora Beam")
    return True


# =============================================================================
# ITEM/MONEY FUNCTIONS
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


def add_item_to_pocket_single(data, pocket, item_id, quantity=99):
    """Add or update an item in a single pocket (one bank)."""
    count = data[pocket['count']]

    # Check if item exists
    for i in range(count):
        offset = pocket['data'] + i * 2
        if data[offset] == item_id:
            old = data[offset + 1]
            data[offset + 1] = min(quantity, 99)
            return f"Updated: {old} -> {min(quantity, 99)}"

    # Add new item
    if count < pocket['max_slots']:
        offset = pocket['data'] + count * 2
        data[offset] = item_id
        data[offset + 1] = min(quantity, 99)
        data[pocket['count']] = count + 1
        return f"Added x{min(quantity, 99)}"
    else:
        return "Pocket full!"


def add_item_to_pocket(data, pocket_name, item_id, quantity=99):
    """Add or update an item in BOTH save banks."""
    # Edit Bank 1 (secondary/backup)
    pocket1 = POCKETS_BANK1[pocket_name]
    result1 = add_item_to_pocket_single(data, pocket1, item_id, quantity)

    # Edit Bank 2 (primary - what the game loads first)
    pocket2 = POCKETS[pocket_name]
    result2 = add_item_to_pocket_single(data, pocket2, item_id, quantity)

    return f"Bank1: {result1}, Bank2: {result2}"


def add_master_balls(data, qty=99):
    result = add_item_to_pocket(data, 'balls', 0x01, qty)
    print(f"Master Ball: {result}")


def add_rare_candy(data, qty=99):
    result = add_item_to_pocket(data, 'items', 0x08, qty)
    print(f"Rare Candy: {result}")


def add_all_balls(data, qty=99):
    for ball_id, ball_name in BALLS.items():
        result = add_item_to_pocket(data, 'balls', ball_id, qty)
        print(f"{ball_name}: {result}")


def max_money(data):
    bcd = int_to_bcd(999999, 3)
    for i, b in enumerate(bcd):
        data[MONEY_OFFSET + i] = b
    print("Money set to $999,999")


def add_healing_items(data, qty=99):
    items = [(0x0D, 'Max Potion'), (0x0E, 'Full Restore'), (0x10, 'Max Revive'), (0x12, 'Max Elixir'), (0x19, 'Full Heal')]
    for item_id, name in items:
        result = add_item_to_pocket(data, 'items', item_id, qty)
        print(f"{name}: {result}")


def add_stat_items(data, qty=99):
    items = [(0x08, 'Rare Candy'), (0x2D, 'HP Up'), (0x2E, 'Protein'), (0x2F, 'Iron'), (0x30, 'Carbos'), (0x31, 'Calcium'), (0x4A, 'PP Max')]
    for item_id, name in items:
        result = add_item_to_pocket(data, 'items', item_id, qty)
        print(f"{name}: {result}")


# =============================================================================
# MAIN
# =============================================================================

def get_save_path():
    """Get save path from args or find automatically."""
    for arg in sys.argv[1:]:
        if not arg.startswith('--') and os.path.exists(arg):
            return arg

    default = "/Volumes/JOE/Saves/CurrentProfile/saves/Gambatte/Pokemon - Crystal Version (USA, Europe) (Rev 1).srm"
    if os.path.exists(default):
        return default

    saves = find_saves()
    if saves:
        return saves[0]

    return None


def print_help():
    print("""
Pokemon Crystal Save Editor
============================

FIND & INFO:
  --find              Find Crystal saves on mounted drives
  --info              Show player info and inventory
  --pokemon           Show Pokemon team (brief)
  --pokemon-detailed  Show Pokemon team with full stats

ITEMS & MONEY:
  --masterballs       Add 99 Master Balls
  --rarecandy         Add 99 Rare Candies
  --allballs          Add 99 of every ball type
  --money             Max out money ($999,999)
  --healing           Add healing items
  --stats             Add stat items (vitamins, Rare Candy)
  --all-items         All item cheats at once

POKEMON EDITING:
  --shiny N           Make Pokemon #N shiny (1-6, or 'all')
  --maxstats N        Max DVs/EVs for Pokemon #N (1-6, or 'all')
  --level N LVL       Set Pokemon #N to level LVL
  --heal              Fully heal all Pokemon
  --suicune N         Replace Pokemon #N with Suicune (for Ho-Oh quest)

EXAMPLES:
  python3 pokemon_crystal_editor.py --pokemon-detailed
  python3 pokemon_crystal_editor.py --shiny 1 --maxstats 1
  python3 pokemon_crystal_editor.py --shiny all --money
  python3 pokemon_crystal_editor.py --level 1 100
""")


def main():
    args = sys.argv[1:]

    if not args or '--help' in args or '-h' in args:
        print_help()
        return

    if '--find' in args:
        saves = find_saves()
        if saves:
            print("Found saves:")
            for s in saves:
                print(f"  {s}")
        else:
            print("No saves found")
        return

    save_path = get_save_path()
    if not save_path:
        print("No save file found. Use --find or specify path.")
        return

    print(f"Save: {save_path}")
    data = read_save(save_path)
    backup_save(save_path)

    modified = False

    # Info commands (read-only)
    if '--info' in args:
        show_info(data)

    if '--pokemon-detailed' in args:
        show_pokemon(data, detailed=True)
    elif '--pokemon' in args or '--team' in args:
        show_pokemon(data, detailed=False)

    # Item commands
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

    if '--all-items' in args:
        add_master_balls(data)
        add_all_balls(data)
        add_rare_candy(data)
        add_healing_items(data)
        add_stat_items(data)
        max_money(data)
        modified = True

    # Pokemon commands
    if '--shiny' in args:
        idx = args.index('--shiny')
        if idx + 1 < len(args):
            target = args[idx + 1]
            if target == 'all':
                count = data[PARTY_COUNT_OFFSET]
                for i in range(1, count + 1):
                    make_pokemon_shiny(data, i)
                modified = True
            else:
                try:
                    slot = int(target)
                    make_pokemon_shiny(data, slot)
                    modified = True
                except ValueError:
                    print(f"Invalid slot: {target}")

    if '--maxstats' in args:
        idx = args.index('--maxstats')
        if idx + 1 < len(args):
            target = args[idx + 1]
            if target == 'all':
                count = data[PARTY_COUNT_OFFSET]
                for i in range(1, count + 1):
                    max_pokemon_stats(data, i)
                modified = True
            else:
                try:
                    slot = int(target)
                    max_pokemon_stats(data, slot)
                    modified = True
                except ValueError:
                    print(f"Invalid slot: {target}")

    if '--level' in args:
        idx = args.index('--level')
        if idx + 2 < len(args):
            try:
                slot = int(args[idx + 1])
                level = int(args[idx + 2])
                set_pokemon_level(data, slot, level)
                modified = True
            except ValueError:
                print("Usage: --level SLOT LEVEL")

    if '--heal' in args:
        heal_all_pokemon(data)
        modified = True

    if '--suicune' in args:
        idx = args.index('--suicune')
        if idx + 1 < len(args):
            try:
                slot = int(args[idx + 1])
                add_suicune(data, slot)
                modified = True
            except ValueError:
                print("Usage: --suicune SLOT (1-6)")
        else:
            print("Usage: --suicune SLOT (1-6)")

    # Save if modified
    if modified:
        write_save(save_path, data)
        print(f"\nSave updated!")


if __name__ == "__main__":
    main()
