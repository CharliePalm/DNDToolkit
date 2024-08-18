from dataclasses import dataclass
from enum import Enum
from typing import List, Set, Dict, Tuple
bullet_char = '•'

# lambdas

is_caster = lambda charClass: charClass in casters

# enums
class CharacterClass(Enum):
    Barbarian = "Barbarian"
    Bard = "Bard"
    Cleric = "Cleric"
    Druid = "Druid"
    Fighter = "Fighter"
    Monk = "Monk"
    Paladin = "Paladin"
    Ranger = "Ranger"
    Rogue = "Rogue"
    Sorcerer = "Sorcerer"
    Warlock = "Warlock"
    Wizard = "Wizard"
    Artificer = "Artificer"
    Blood_Hunter = "Blood Hunter"
    Mystic = "Mystic"
    
class Components(Enum):
    V = 'Verbal' 
    S = 'Somatic' 
    M = 'Material'
    
class School(Enum):
    Abjuration = 'Abjuration'
    Conjuration = 'Conjuration'
    Divination = 'Divination'
    Enchantment = 'Enchantment'
    Evocation = 'Evocation'
    Illusion = 'Illusion'
    Necromancy = 'Necromancy'
    Transmutation = 'Transmutation'

class Tag(Enum):
    Dunamancy = 'Dunamancy'
    Ritual = 'Ritual'
    Graviturgy = 'Graviturgy'
    Chronurgy = 'Chronurgy'
    Technomagic = 'Technomagic'

class DamageType(Enum):
    Cold = 'Cold'
    Fire = 'Fire'
    Bludgeoning = 'Bludgeoning'
    Radiant = 'Radiant'
    Necrotic = 'Necrotic'
    Psychic = 'Psychic'
    Force = 'Force'
    Elemental = 'Elemental'
    Piercing = 'Piercing'
    Lightning = 'Lightning'
    Thunder = 'Thunder'
    Acid = 'Acid'
    Poison = 'Poison'
    Slashing = 'Slashing'
    Physical = 'Physical'

class Skill(Enum):
    Strength = 'Strength'
    Dexterity = 'Dexterity'
    Constitution = 'Constitution'
    Charisma = 'Charisma'
    Intelligence = 'Intelligence'
    Wisdom = 'Wisdom'

class Ability(Enum):
    Acrobatics = "Acrobatics"
    Animal_Handling = "Animal Handling"
    Arcana = "Arcana"
    Athletics = "Athletics"
    Deception = "Deception"
    History = "History"
    Insight = "Insight"
    Intimidation = "Intimidation"
    Investigation = "Investigation"
    Medicine = "Medicine"
    Nature = "Nature"
    Perception = "Perception"
    Performance = "Performance"
    Persuasion = "Persuasion"
    Religion = "Religion"
    Sleight_of_Hand = "Sleight of Hand"
    Stealth = "Stealth"
    Survival = "Survival"

class Species(Enum):
    Dwarf = "Dwarf"
    Elf = "Elf"
    Halfling = "Halfling"
    Human = "Human"
    Dragonborn = "Dragonborn"
    Gnome = "Gnome"
    Half_Elf = "Half-Elf"
    Half_Orc = "Half-Orc"
    Tiefling = "Tiefling"
    Aarakocra = "Aarakocra"
    Genasi = "Genasi"
    Goliath = "Goliath"
    Firbolg = "Firbolg"
    Triton = "Triton"
    
class WeaponFamily(Enum):
    Simple = 'Simple'
    Martial = 'Martial'

class Alignment(Enum):
    LawfulEvil = 'Lawful Evil'
    ChaoticEvil = 'Chaotic Evil'
    NeutralEvil = 'Neutral Evil'
    LawfulNeutral = 'Lawful Neutral'
    ChaoticNeutral = 'Chaotic Neutral'
    TrueNeutral = 'True Neutral'
    LawfulGood = 'Lawful Good'
    ChaoticGood = 'Chaotic Good'
    NeutralGood = 'Neutral Good'

# maps
school_emoji_map = {
    School.Abjuration.value: '🛡️',
    School.Conjuration.value: '🌀',
    School.Divination.value: '🔮',
    School.Enchantment.value: '✨',
    School.Evocation.value: '🔥',
    School.Illusion.value: '👁️‍🗨️',
    School.Necromancy.value: '💀',
    School.Transmutation.value: '🔄',
}

ability_to_skill = {
    Ability.Acrobatics: Skill.Dexterity,
    Ability.Animal_Handling: Skill.Wisdom,
    Ability.Arcana: Skill.Intelligence,
    Ability.Athletics: Skill.Strength,
    Ability.Deception: Skill.Charisma,
    Ability.History: Skill.Intelligence,
    Ability.Insight: Skill.Wisdom,
    Ability.Intimidation: Skill.Charisma,
    Ability.Investigation: Skill.Intelligence,
    Ability.Medicine: Skill.Wisdom,
    Ability.Nature: Skill.Intelligence,
    Ability.Perception: Skill.Wisdom,
    Ability.Performance: Skill.Charisma,
    Ability.Persuasion: Skill.Charisma,
    Ability.Religion: Skill.Intelligence,
    Ability.Sleight_of_Hand: Skill.Dexterity,
    Ability.Stealth: Skill.Dexterity,
    Ability.Survival: Skill.Wisdom
}

standard_skill_arr: List[int] = [15, 14, 13, 12, 10, 8]

skill_priority_tree: Dict[CharacterClass, Dict[any, any]] = {
    CharacterClass.Barbarian: {
        Skill.Strength: {
            Skill.Constitution: {}
        }
    },
    CharacterClass.Bard: {
        Skill.Charisma: {
            Skill.Dexterity: {
                Skill.Constitution: {}
            },
            Skill.Wisdom: {
                Skill.Constitution: {}
            }
        }
    },
    CharacterClass.Cleric: {
        Skill.Wisdom: {}
    },
    CharacterClass.Druid: {
        Skill.Wisdom: {
            Skill.Dexterity: {
                Skill.Constitution: {}
            },
            Skill.Constitution: {
                Skill.Dexterity: {}
            }
        }
    },
    CharacterClass.Fighter: {
        Skill.Strength: {
            Skill.Constitution: {}
        },
        Skill.Dexterity: {
            Skill.Constitution: {}
        },
    },
    CharacterClass.Monk: {
        Skill.Dexterity: {
            Skill.Wisdom: {
                Skill.Constitution: {}
            },
            Skill.Constitution: {
                Skill.Wisdom: {}
            }
        }
    },
    CharacterClass.Paladin: {
        Skill.Strength: {
            Skill.Charisma: {
                Skill.Constitution: {}
            }
        },
        Skill.Charisma: {
            Skill.Strength: {
                Skill.Constitution: {}
            }
        }
    },
    CharacterClass.Ranger: {
        Skill.Dexterity: {
            Skill.Wisdom: {
                Skill.Constitution: {},
                Skill.Strength: {}
            }
        }
    },
    CharacterClass.Rogue: {
        Skill.Dexterity: {
            Skill.Charisma: {
                Skill.Constitution: {}
            },
            Skill.Intelligence: {
                Skill.Constitution: {}
            }
        }
    },
    CharacterClass.Sorcerer: {
        Skill.Charisma: {
            Skill.Dexterity: {
                Skill.Constitution: {}
            },
            Skill.Constitution: {
                Skill.Dexterity: {}
            }
        }
    },
    CharacterClass.Warlock: {
        Skill.Charisma: {
            Skill.Dexterity: {
                Skill.Constitution: {}
            },
            Skill.Constitution: {
                Skill.Dexterity: {}
            }
        }
    },
    CharacterClass.Wizard: {
        Skill.Intelligence: {
            Skill.Constitution: {
                Skill.Dexterity: {
                    Skill.Wisdom: {}
                }
            },
            Skill.Dexterity: {
                Skill.Constitution: {
                    Skill.Wisdom: {}
                }
            }
        }
    },
    CharacterClass.Artificer: {
        Skill.Intelligence: {
            Skill.Dexterity: {
                Skill.Constitution: {}
            },
            Skill.Constitution: {
                Skill.Dexterity: {}
            }
        }
    },
    CharacterClass.Blood_Hunter: {
        Skill.Dexterity: {
            Skill.Constitution: {
                Skill.Strength: {}
            }
        }
    },
    CharacterClass.Mystic: {
        Skill.Intelligence: {
            Skill.Wisdom: {
                Skill.Dexterity: {}
            },
            Skill.Dexterity: {
                Skill.Wisdom: {}
            }
        }
    }
}

# if a class compiles features instead of sets to be latest, we note that here
uses_list_of_dicts = [
    'features'
]

casters = set([
    CharacterClass.Artificer,
    CharacterClass.Bard,
    CharacterClass.Cleric,
    CharacterClass.Druid,
    CharacterClass.Ranger,
    CharacterClass.Paladin,
    CharacterClass.Sorcerer,
    CharacterClass.Warlock,
    CharacterClass.Wizard,
])

# classes

class Weapon:
    name: str
    cost: int # number of gold pieces
    damage: str
    damage_type: DamageType
    weight: int # number of lbs
    properties: Set[str]
    range_normal: int = 0
    range_max: int = 0
    family: WeaponFamily

class Spell:
    name: str = ''
    description: str = ''
    duration: str = ''
    components: List[Components] = []
    materials: str = ''
    classes: List[CharacterClass] = []
    school: School = ''
    level: int
    cast_time: str = ''
    range: str = ''
    higher_levels: str = ''
    source: str = ''
    tags: List[Tag] = []
    damage_type: DamageType = ''
    damage: str = ''
    saving_throw: Skill = ''
    def __init__(self):
        pass
    def __str__(self):
        to_ret = ''
        for attr in self.__dir__():
            if attr[0] != '_':
                to_ret += attr + ': ' + str(self.__getattribute__(attr)) + '\n'
        return to_ret

class Character:
    name: str = ''
    species: Species = ''
    character_class: CharacterClass = ''
    skills = {
        Skill.Strength.value: 10,
        Skill.Dexterity.value: 10,
        Skill.Constitution.value: 10,
        Skill.Charisma.value: 10,
        Skill.Intelligence.value: 10,
        Skill.Wisdom.value: 10,
    }
    proficiency_bonus: int = 2
    saving_throw_profs: Set[Skill] = set()
    ability_check_profs: Set[Ability] = set()
    features: Dict[str, str] = {}
    spell_slots: Dict[int, int] = {}
    proficiencies: Dict[str, str | List] = {} # key is name of proficiency, 
    level: int = 0
    equipment: List[Tuple[str | Weapon, int]] = [] # item + count
    background: str = ''# todo
    alignment: Alignment = ''# todo
    max_hp: int = 0
    current_hp: int = 0
    ac: int = 10
     
    def __init__(self): pass

    def get_spell_casting_mod(self):
        if not is_caster(self.character_class): return 0
        x = 0
        if self.character_class in [CharacterClass.Bard, CharacterClass.Sorcerer, CharacterClass.Warlock, CharacterClass.Paladin]:
            x = self.skills[Skill.Charisma.value]
        elif self.character_class in [CharacterClass.Wizard, CharacterClass.Fighter, CharacterClass.Rogue, CharacterClass.Artificer]:
            x = self.skills[Skill.Intelligence.value]
        else: x = self.skills[Skill.Wisdom.value]
        return x + self.proficiency_bonus

    def get_spell_save(self): return (8 + self.get_spell_casting_mod()) if is_caster(self.character_class) else 0

    def make_check(self, ability: Ability):
        return self.get_modifier(ability_to_skill[ability]) + (self.proficiencyBonus if ability in self.ability_check_profs else 0)

    def make_save(self, skill: Skill):
        return self.get_modifier(skill) + (self.proficiencyBonus if skill in self.saving_throw_profs else 0)
    
    def get_modifier(self, skill: Skill):
        return int(self.skills[skill] / 2 - 5)
    
    def __str__(self):
        to_ret = ''
        for attr in self.__dir__():
            if attr[0] != '_':
                to_ret += attr + ': ' + str(self.__getattribute__(attr)) + '\n'
        return to_ret
