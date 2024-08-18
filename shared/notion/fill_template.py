from shared.helpers import load_json_object
from shared.model import Character
from shared.notion.notion import Notion, pprint, update_block_content, update_page_value
from typing import Dict, List, Tuple
import notion_client
import os
from shared.model import Character, Spell, Weapon, school_emoji_map, bullet_char
import shared.notion.data_builders as builders
from shared.helpers import load_json_object
from .model import has_children
import json
from copy import deepcopy


def fill_character_sheet_template(template_id: str, character_name: str):
    notion = Notion()
    char: Character = load_json_object(f'./generator/{character_name}.json', Character)
    top_level_children = notion.get_block_children(template_id)

    # page = notion.get_page(template_id)
    # update name
    '''
    page['properties']['title']['title'][0]['text']['content'] = character.name
    notion.client.pages.update(template_id, properties=page['properties'])
    '''
    # header blocks
    '''
    hdr_block = notion.get_block_children(top_level_children[1]['id'])
    text_to_update = [char.character_class, char.species, char.background or '', char.alignment or '', '', char.level]
    for i in range(3):
        children = notion.get_block_children(hdr_block[i]['id'])
        for j in range(2):
            update_block_content(children[j], text_to_update[2 * i + j])
            notion.client.blocks.update(children[j]['id'], **{children[j]['type']: get_block_type_val(children[j])})

    stats_block = notion.get_block_children(top_level_children[2]['id'])
    skills_db_id = notion.get_block_children(stats_block[0]['id'])[0]['id']
    skill_entries = notion.client.databases.query(skills_db_id)['results']
    for skill_page in skill_entries:
        name = get_page_title(skill_page)
        char_skill_val = char.skills[name] if name != 'Proficiency Bonus' else char.proficiency_bonus
        update_page_value(skill_page, char_skill_val, 'Amount')
        notion.update_page(skill_page)
    
    
    middle_col = notion.get_block_children(stats_block[1]['id'])
    save_entries: List[dict] = notion.client.databases.query(middle_col[0]['id'])['results']
    for save_prof in char.saving_throw_profs:
        for save_page in save_entries:
            if get_page_title(save_page) == save_prof:  
                update_page_value(save_page, True, 'Proficient')
                notion.update_page(save_page)
                break

    check_entries: List[dict] = notion.client.databases.query(middle_col[1]['id'])['results']
    for check_prof in char.ability_check_profs:
        for save_page in check_entries:
            if get_page_title(save_page) == check_prof:  
                update_page_value(save_page, True, 'Proficient')
                notion.update_page(save_page)
                break

    right_col = filter(lambda x: x['type'] == 'callout', notion.get_block_children(stats_block[2]['id']))
    data = [(char.max_hp, char.current_hp), char.ac, f'{char.level}d{char.hit_die}', 'SKIP', ('+' if char.skills[Skill.Dexterity.value] > 10 else '') + str(char.get_modifier(Skill.Dexterity.value)), 'SKIP', char.get_spell_casting_mod()]
    print(data)
    for block, to_update in zip(right_col, data):
        if type(to_update) == tuple:
            update_block_content(block, f'HP ({to_update[0]})', 0)
            to_update = to_update[1]
        elif to_update == 'SKIP': continue
        update_block_content(block, to_update)
        notion.client.blocks.update(block['id'], **{block['type']: get_block_type_val(block)})
    
    '''

    class_features_db_id = top_level_children[4]['id']
    default_entry = notion.query_db(class_features_db_id)[0]
    template = notion.scrape_result(deepcopy(default_entry))
    block_template = notion.scrape_result(deepcopy(notion.get_block_children(default_entry['id'])[0]))
    default_entry['archived'] = True
    notion.update_page(default_entry)
    for feature in char.features:
        to_send = deepcopy(template)
        block_to_send = deepcopy(block_template)
        update_page_value(to_send, feature, 'Name')
        update_block_content(block_to_send, char.features[feature], 0)
        pprint(to_send)
        new_page = notion.create_db_page(class_features_db_id, feature, '✨', to_send['properties'])
        notion.append_block(new_page['id'], [block_to_send])