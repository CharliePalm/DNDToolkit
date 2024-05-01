import notion_client
import os
from typing import List
from shared.model import Spell, school_emoji_map, bullet_char
from shared.utility_functions import load_json_spells
from pprint import pprint

class Notion:
    spells_db_id = 'd01a32f616a34027a3787fc9e2523fb5'
    my_spells_db_id = 'b473c31801204470986b88aafd051b05'
    client: notion_client.Client
    def __init__(self):
        self.client = notion_client.Client(auth=os.environ["NOTION_TOKEN"])
        
    def get_spell_properties(self, spell: Spell):
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
        
    def create_spell(self, spell: Spell):
        response = self.client.pages.create(
            parent={ 'database_id': self.my_spells_db_id }, 
            icon={ 'emoji': school_emoji_map[spell.school] },
            properties=self.get_spell_properties(spell),
        )
        page_id = response['id']
        # do this after for description
        for desc_paragraph in spell.description.split('\n\n'):
            p_type = 'paragraph'
            if desc_paragraph[0] == bullet_char:
                p_type = 'bulleted_list_item'
                desc_paragraph = desc_paragraph[1:]
            
            self.client.blocks.children.append(page_id, children=[
                {
                    "object": "block",
                    "type": p_type,
                    p_type: {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": desc_paragraph 
                                }
                            }
                        ]
                    }
                }
            ])
        
    def get_db_page(self, id: str):
        return self.client.blocks.children.list(id)

    def upload_spell(self, spell_name: str):
        spells = load_json_spells('spells.json')
        for i in spells:
            if i.name == spell_name:
                print(i)
                self.create_spell(i)
                break
    def upload_all_spells(self):
        for spell in load_json_spells('spells.json'):
            print('creating spell ' + spell.name)
            self.create_spell(spell)
