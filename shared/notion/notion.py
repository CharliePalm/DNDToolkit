from typing import Dict, List, Tuple
import notion_client
import os
from shared.model import Character, Skill, Spell, Weapon, school_emoji_map, bullet_char
import shared.notion.data_builders as builders
from shared.helpers import load_json_object
from .model import has_children
import json
from copy import deepcopy

def pprint(to_print): print(json.dumps(to_print, indent=4))
def get_block_type_val(block): return block[block['type']]
def update_block_content(block, text, index = 1):
    val = get_block_type_val(block)
    for v in val:
        if type(val[v]) == list and len(val[v]):
            inner_val = val[v][index]
            v_type = inner_val['type']
            inner_val[v_type]['content'] = ('\n' if index > 0 else '') + text
            break
    return block
    
def get_page_title(page):
    for p in page['properties']:
        if 'title' in page['properties'][p]:
            return page['properties'][p]['title'][0]['text']['content']
        
def update_page_value(page, new_value, value_name): 
    prop = page['properties'][value_name]
    if prop['type'] in ['number', 'checkbox']:
        prop[prop['type']] = new_value
    elif prop['type'] in ['title']:
        secondary_type = prop[prop['type']][0]['type']
        prop[prop['type']][0][secondary_type]['content'] = new_value
        # todo when we need to
        pass

def remove_problematic_properties(page):
    to_del = []
    for p in page['properties']:
        t = page['properties'][p]['type']
        if t in ['rollup', 'relation', 'formula']:
            to_del.append(p)
    for d in to_del: del page['properties'][d]

class Notion:
    spells_db_id = 'd01a32f616a34027a3787fc9e2523fb5'
    my_spells_db_id = 'b473c31801204470986b88aafd051b05'
    equipment_db_id = '6671d93daefd4501aee012fb55cd9378'
    characters_db_id = '5856500531444c34bf89a9f9074e7cdc'
    template_page = '548ab0377082480d818f68232c63ef7b'
    client: notion_client.Client
    def __init__(self):
        self.client = notion_client.Client(auth=os.environ["NOTION_TOKEN"])
        
    def scrape_result(self, result, remove_ids = False):
        if 'object' in result and result['object'] == 'list' or type(result) == list:
            to_ret = []
            result = result if type(result) == list else result['results']
            for r in result:
                to_ret.append(self.scrape_result(r, remove_ids))
            return to_ret
        for v in ['has_children', 'created_time', 'last_edited_time', 'last_edited_by', 'created_by', 'archived', 'in_trash', 'public_url', 'request_id', 'id' if remove_ids else None, 'parent' if remove_ids else None]:
            if v in result:
                del result[v]
        for property in result:
            if (type(result[property]) == dict or type(result[property]) == list) and property != 'mention':
                result[property] = self.scrape_result(result[property], remove_ids)
        return result
        
    def create_weapon(self, weapon: Weapon):
        return self.client.pages.create(
            parent={ 'database_id': self.equipment_db_id }, 
            icon={ 'emoji': '🗡️' if weapon.range_normal == 0 or 'Ammunition' not in weapon.properties else '🏹' },
            properties=builders.get_weapon_properties(weapon),
        )
    
    def create_spell(self, spell: Spell):
        response = self.client.pages.create(
            parent={ 'database_id': self.my_spells_db_id }, 
            icon={ 'emoji': school_emoji_map[spell.school] },
            properties=builders.get_spell_properties(spell),
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


    def upload_spell(self, spell_name: str):
        spells = load_json_object('./spell_loader/spells.json', Spell)
        for i in spells:
            if i.name == spell_name:
                print('uploading spell ' + i)
                self.create_spell(i)
                break
    
    def upload_weapon(self, weapon_name: str):
        print(weapon_name)
        weapons = load_json_object('./equipment_loader/weapons.json', Weapon)
        for i in weapons:
            if i.name == weapon_name:
                print('creating weapon ' + weapon_name)
                self.create_weapon(i)
                break

    def upload_all_spells(self):
        for spell in load_json_object('./spell_loader/spells.json', Spell):
            print('creating spell ' + spell.name)
            self.create_spell(spell)

    def upload_all_weapons(self):
        for weapon in load_json_object('./equipment_loader/weapons.json', Weapon):
            print('creating weapon ' + weapon.name)
            self.create_weapon(weapon)

    def upload_character(self, character_name: str):
        '''
        Creates a new character
        load character json
        add top blocks
        add dbs
        add three column section?
        add side blocks
        '''
        character: Character = load_json_object(f'./generator/{character_name}.json', Character)
        self.deep_copy_page('b00ddeb5e9e944269066508dce078d26', 'page_id', '2e7458dcad594ba2ad2fc57d63c75fdd')

        # create notes page
        # self.create_page(page['id'], 'Notes', '📓')
        # load template
        # template = self.scrape_result(self.get_block_children(self.template_page), True)[1:]
        # create header blocks
        # for block in template[1:]:
        #     block['parent']['page_id'] = page['id']
        # top_block_children = self.scrape_result(self.get_block_children(template[0]['id']), True)
        # template[0]['column_list']['children'] = top_block_children
        # 

    def _create_db_test(self):
        db = self.scrape_result(load_json_object('./DB.json', dict), True)
        db['parent'] = {
            'type': 'page_id',
            'page_id': 'b00ddeb5e9e944269066508dce078d26'
        }
        db = self.create_db(db)
        db['parent'] = {
            'type': 'block_id',
            'block_id': 'fb2a687b-28da-40ed-a86f-a4a4046f8296'
        }
        self.update_db(db)
        pass

    # base methods
    # getters
    def get_block_children(self, id: str):
        return self.client.blocks.children.list(id)['results']
    
    def get_block(self, id: str):
        x = self.client.blocks.retrieve(id)
        return x

    # not really sure why these are diferentiated as they serve similar purposes and don't use different UUIDs
    def get_page(self, id: str):
        return self.client.pages.retrieve(id)
    
    def insert_into_db(self, db_id: str, properties: dict, icon, map_icon = False):
        return self.client.pages.create(
            parent={ 'database_id': db_id },
            icon={ 'emoji': icon } if map_icon else icon,
            properties=properties,
        )
    
    def create_page(self, parent_id: str, title: str, icon='⚔️', properties=None):
        return self.client.pages.create(
            properties=properties if properties else builders.get_page_props(title),
            parent={
                "type": "page_id",
                "page_id": parent_id
            },
            icon=builders.get_icon(icon)
        )
    def create_db_page(self, parent_id: str, title: str, icon='⚔️', properties=None):
        return self.client.pages.create(
            properties=properties if properties else builders.get_page_props(title),
            parent={
                "type": "database_id",
                "database_id": parent_id
            },
            icon=builders.get_icon(icon)
        )


    def append_block(self, parent_id, children):
        with open('./body.json', 'w') as fp: json.dump(children, fp, indent=4)
        return self.client.blocks.children.append(parent_id, children=children) if len(children) else []
    
    def query_db(self, block_id):
        return self.client.databases.query(block_id)['results']
    
    def get_db(self, db_id):
        return self.client.databases.retrieve(db_id)
    
    def get_all_children(self, block, dbs_to_copy: List[Tuple[str, int]] = [], depth = 0):
        if block['type'] == 'child_database':
            dbs_to_copy.append((block['id'], depth))
            block['type'] = 'paragraph'
            block['paragraph'] = {
                "rich_text": [],
                "color": "default"
            }
            del block['child_database']
        elif block['type'] in has_children:
            block[block['type']]['children'] = self.get_block_children(block['id'])
            for child in block[block['type']]['children']:
                self.get_all_children(child, dbs_to_copy, depth + 1)
        return block, dbs_to_copy
    
    def copy_child_db(self, db_id, new_parent):
        db = self.scrape_result(self.get_db(db_id), True)
        db['parent'] = new_parent()
        db = self.create_db(db)
        existing_items = self.scrape_result(self.query_db(db_id), True)
        for item in existing_items:
            self.insert_into_db(db['id'], item['properties'], item['icon'])
            # add call to deep_copy_page here?


    def deep_copy_page(self, parent_id, parent_type, to_copy_id = None):
        '''
        Copies a page and all its children to a new page
        Couple of things to explain here as this isn't the most intuitive code to read due to notion's interesting way of notating objects/dealing with object children
        Notion does not accept databases or pages as children, only entities like paragraphs, rich text, etc.
        Notion also does not return children from the block.children.list endpoint.
            Therefore we need to load all the children ourselves to truly make a copy.
            We also need to keep track of nested child databases to make them after we finish
        '''
        page = self.get_block_children(to_copy_id or parent_id)
        depth_continuation = []
        children_to_put = []
        get_parent = lambda: {'type': parent_type, parent_type: parent_id}
        def flush_queue():
            result = self.append_block(parent_id, children_to_put)                 
            children_to_put = []
            return result
        
        dbs_to_copy: Dict[int, Tuple[str, int]] = {} # index in children_to_put
        for idx, child in enumerate(page):
            if child['type'] in ['child_database', 'child_page']:
                # if there's a child database here we can just flush and continue
                results = results + flush_queue()
                if child['type'] == 'child_database':
                    self.copy_child_db(child['id'], get_parent())
                else:
                    pass #todo
            else:
                depth_continuation.append((child['id'], child['type']))
                if child['type'] in has_children:
                    child, dbs_with_depth = self.get_all_children(child)
                    child = self.scrape_result(child)
                    dbs_to_copy[idx] = dbs_with_depth
                children_to_put.append(deepcopy(child))
        results = results + flush_queue()
        for idx in dbs_with_depth:
            parent_entry = results[idx]
            self.copy_child_db(db)
        for child_id, child_type in depth_continuation:
            self.deep_copy_page(child_id, child_type)
    
    def create_db(self, db):
        return self.client.databases.create(parent=db['parent'], title=db['title'], properties=db['properties'], idcon=db['icon'], cover=db['cover'], is_inline=db['is_inline'])

    def update_db(self, db):
        print('happy new year')
        return self.client.databases.update(db['id'], parent=db['parent'], title=db['title'], properties=db['properties'], idcon=db['icon'], cover=db['cover'], is_inline=db['is_inline'])

    def update_page(self, page):
        remove_problematic_properties(page)
        return self.client.pages.update(page['id'], properties=page['properties'], icon=page['icon'], archived=page['archived'])