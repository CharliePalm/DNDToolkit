from shared.model import Character, Spell, Weapon

'''
Notion objects are monstrosities so we use this separate file to build them
'''
def get_spell_properties(spell: Spell):
    properties = {
            "Cast time": {
                "rich_text": [{
                    "text": {
                        "content": spell.cast_time
                    }
                }]
            },
            "Classes": {
                "multi_select": [{"name": spell_class} for spell_class in spell.classes]
            },
            "Components": {
                "multi_select": [{"name": component} for component in spell.components]
            },
            "Tags": {
                "multi_select": [{"name": tag} for tag in spell.tags]
            },
            "Damage": {
                "rich_text": [{
                    "text": {
                        "content": spell.damage
                    }
                }]
            },
            "Duration": {
                "rich_text": [{
                    "text": {
                        "content": spell.duration
                    }
                }]
            },
            "Level": { "number": spell.level },
            "Materials": {
                "rich_text": [{
                    "text": {
                        "content": spell.materials
                    }
                }]
            },
            "Name": {
                "title": [{
                    "text": {
                        "content": spell.name
                    }
                }]
            },
            "Range": {
                "rich_text": [{
                    "text": {
                        "content": spell.range
                    }
                }]
            },
            "School": {
                "select": {
                    "name": spell.school
                }
            },
            "Higher Levels": {
                "rich_text": [{
                    "text": {
                        "content": spell.higher_levels
                    }
                }]
            },
            "Source": {
                "select": {
                    "name": spell.source
                }
            },
        }
    if spell.damage_type:
        properties["Damage Type"] = {
            "multi_select": [{"name": spell.damage_type}]
        }
    if spell.saving_throw:
        properties["Saving Throw"] = {
            "select": {
                "name": spell.saving_throw
            }
        }
    return properties

def get_weapon_properties(weapon: Weapon):
    props = {
        "Name": {
            "title": [{
                "text": {
                    "content": weapon.name
                }
            }]
        },
        "Weight": { "number": weapon.weight },
        "Damage": {
            "rich_text": [{
                "text": {
                    "content": str(weapon.damage)
                }
            }]
        },
        "Properties": {
            "multi_select": [{"name": weapon_property} for weapon_property in weapon.properties]
        },
        "Cost": { "number": weapon.cost },
        "Family": {
            "select": {"name": weapon.family}
        },
        "Normal Range": { "number": weapon.range_normal },
        "Max Range": { "number": weapon.range_max },
    }
    if weapon.damage_type:
        props["Damage Type"] = {
            "select": {"name": weapon.damage_type}
        }
    return props

def get_page_props(title: str):
    return {
        "title": {
            "id": "title",
            "type": "title",
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": title,
                    },
                    "annotations": {
                        "color": "default"
                    },
                    "plain_text": title,
                }
            ]
        }
    }

def get_icon(icon: str, external = False):
    return {'emoji': icon} if not external else {
        "type": "external",
        "external": {
            "url": icon
        }
    }

def get_header_blocks(character: Character, parent_id):
    return [
    {
        "parent": {
            "type": "block_id",
            "block_id": parent_id
        },
        "type": "callout",
        "callout": {
            "icon": {
                "type": "external",
                "external": {
                    "url": "https://notion-emojis.s3-us-west-2.amazonaws.com/v0/svg-twitter/1f454.svg"
                }
            },
            "color": "gray_background",
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": "Class",
                    },
                    "annotations": {
                        "color": "default"
                    },
                    "plain_text": "Class",
                },
                {
                    "type": "text",
                    "text": {
                        "content": f"\n{character.character_class}",
                    },
                    "annotations": {
                        "color": "default"
                    },
                    "plain_text": f"\n{character.character_class}",
                }
            ]
        }
    },
    {
        "parent": {
            "type": "block_id",
            "block_id": parent_id
        },
        "type": "callout",
        "callout": {
            "icon": {
                "type": "external",
                "external": {
                    "url": "https://notion-emojis.s3-us-west-2.amazonaws.com/v0/svg-twitter/1f479.svg"
                }
            },
            "color": "gray_background",
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": "Race",
                    },
                    "annotations": {
                        "color": "default"
                    },
                    "plain_text": "Race",
                },
                {
                    "type": "text",
                    "text": {
                        "content": f"\n{character.species}",
                    },
                    "annotations": {
                        "color": "default"
                    },
                    "plain_text": f"\n{character.species}",
                }
            ]
        }
    },
    {
        "parent": {
            "type": "block_id",
            "block_id": parent_id
        },
        "type": "paragraph",
        "paragraph": {
            "color": "default",
            "rich_text": []
        }
    }
]
