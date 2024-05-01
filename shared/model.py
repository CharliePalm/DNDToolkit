from dataclasses import dataclass
from enum import Enum
from typing import List, Set

bullet_char = '•'

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
    Yuan_Ti_Pureblood = "Yuan-Ti Pureblood"
    
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

skill_priority_tree = {
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

# classes
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
    name: str
    species: Species
    character_class: CharacterClass
    skills = {
        Skill.Strength: 10,
        Skill.Dexterity: 10,
        Skill.Constitution: 10,
        Skill.Charisma: 10,
        Skill.Intelligence: 10,
        Skill.Wisdom: 10,
    }
    proficiencyBonus: int = 2
    saving_throw_profs: Set[Skill]
    ability_check_profs: Set[Ability]
    
    def make_check(self, ability: Ability):
        return self.get_modifier(ability_to_skill[ability]) + (self.proficiencyBonus if ability in self.ability_check_profs else 0)

    def make_save(self, skill: Skill):
        return self.get_modifier(skill) + (self.proficiencyBonus if skill in self.saving_throw_profs else 0)
    
    def get_modifier(self, skill: Skill):
        return self.skills[skill] / 2 - 5