from .model import Spell
from typing import List
import json
def load_spell_from_dict(d):
    s = Spell()
    for key in d:
        setattr(s, key, d[key])
    return s

def load_json_spells(filename = 'spells.json') -> List[Spell]:
    with open('spell_loader/' + filename, 'rb') as fp:
        spells = json.loads(fp.read(), object_hook=load_spell_from_dict)
    return spells
