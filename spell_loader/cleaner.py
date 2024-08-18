# This file is intended for helper functions related to data that has ALREADY been scraped. i.e. we expect a clean description

from shared.helpers import load_json_object
from shared.model import Spell, Skill, DamageType
import json
import re

def parse_damage_info(spell_description: str):
    '''
        this is a very imprecise method, but we take what we can get here.
    '''
    saving_throw = None
    damage_amount = None
    damage_type = None
    
    # Extract saving throw
    saving_throw_match = re.search(r'(\w+) saving throw', spell_description)
    if saving_throw_match:
        saving_throw = saving_throw_match.group(1).lower().capitalize()

    # Extract damage amount and type
    damage_match = re.search(r'(\d+d\d+|\d+)[\s\w]* damage', spell_description)
    if damage_match:
        damage_info = damage_match.group(1)
        
        # Extract damage amount
        damage_amount_match = re.search(r'(\d+d\d+|\d+)', damage_info)
        if damage_amount_match:
            damage_amount = damage_amount_match.group(1)
        
        # Extract damage type
        damage_type_match = re.search(r'\b(\w+)\b damage', spell_description)
        if damage_type_match:
            damage_type = damage_type_match.group(1).capitalize()
    return saving_throw, damage_amount, damage_type

def add_for_all_spells():
    spells = load_json_object('./spell_loader/spells.json', Spell)
    for spell in spells:
        add_description_info(spell)
    dump_to_cleaned_spells(spell)

        
def add_description_info(spell: Spell):
    spell.saving_throw, spell.damage, spell.damage_type = parse_damage_info(spell.description)
    try:
        spell.saving_throw = Skill[spell.saving_throw].value if spell.saving_throw and spell.saving_throw else ''
    except:
        spell.saving_throw = ''
    spell.damage = spell.damage if spell.damage else ''
    if 'd' not in spell.damage and spell.damage != '':
        spell.damage = ''
    spell.damage_type = DamageType[spell.damage_type].value if spell.damage_type and spell.damage_type in DamageType.__dict__ else ''

def dump_to_cleaned_spells(spells):
    with open('cleaned_spells.json', 'w') as f:
        json.dump([spell.__dict__ for spell in spells], f)
