from shared.helpers import load_json_object
from shared.model import Character, Skill, skill_to_abbrev
from shared.notion.notion import Notion, get_block_type_val, get_page_title, pprint, update_block_content, update_page_value
from typing import List
from shared.model import Character, Weapon
from shared.helpers import load_json_object
from copy import deepcopy
get_weapon_emoji = lambda weapon: '🏹' if 'Ammunition' in weapon.properties else '⚔️'

class TemplateFiller:
    strength_page_id = ''
    notion = Notion()
    top_level_children = []
    page = None
    template_id = ''
    char: Character = None
    all_weapons: List[Weapon] = load_json_object('./misc_loader/weapons.json', Weapon)
    
    def __init__(self, character_name: str, template_id: str) -> None:
        self.char = load_json_object(f'./generator/{character_name}.json', Character)
        self.top_level_children = self.notion.get_block_children(template_id)
        self.page = self.notion.get_page(template_id)
        self.template_id = template_id
        
    def get_equipment(self, search_for_weapons):
        for c in self.char.equipment:
            if search_for_weapons and c[1] == 'Weapon':
                for j in self.all_weapons:
                    if j.name == c[0]:
                        yield j
            elif not search_for_weapons and c[1] != 'Weapon':
                yield (c[0], c[1])
        
    def is_proficient_in_weapon(self, weapon: Weapon): return weapon.family + ' weapons' in self.char.proficiencies['Weapons']
    
    def create_weapon_block(self, to_send, weapon: Weapon):
        update_page_value(to_send, weapon.name, 'Name')
        update_page_value(to_send, weapon.damage_type, 'Damage type')
        # todo, update relation to str/dex?
        update_page_value(to_send, weapon.damage, 'Damage')
        update_page_value(to_send, f'{weapon.range_max} max, {weapon.range_normal}, normal' if weapon.range_normal else '', 'Range')
        update_page_value(to_send, self.strength_page_id, 'Skill')
        if not self.is_proficient_in_weapon(weapon):
            update_page_value(to_send, False, 'Proficient')
        
    def title(self):
        self.page['properties']['title']['title'][0]['text']['content'] = char.name
        self.notion.client.pages.update(self.template_id, properties=self.page['properties'])
        
    def header_blocks(self):
        hdr_block = self.notion.get_block_children(self.top_level_children[3]['id'])
        text_to_update = [self.char.character_class, self.char.species, self.char.background or '', char.alignment or '', '', char.level]
        for i in range(3):
            children = self.notion.get_block_children(hdr_block[i]['id'])
            for j in range(2):
                update_block_content(children[j], text_to_update[2 * i + j])
                self.notion.client.blocks.update(children[j]['id'], **{children[j]['type']: get_block_type_val(children[j])})

    def left_stat_col(self):
        skills_db_id = self.notion.get_block_children(self.stats_block[0]['id'])[0]['id']
        skills = self.notion.client.databases.query(skills_db_id)['results']
        for skill_page in skills:
            name = get_page_title(skill_page)
            char_skill_val = self.char.skills[name] if name != 'Proficiency Bonus' else self.char.proficiency_bonus
            if name == 'Strength':
                self.strength_page_id = skill_page['id']
            update_page_value(skill_page, char_skill_val, 'Amount')
            self.notion.update_page(skill_page)
            
    def middle_stats_col(self):
        middle_col = self.notion.get_block_children(self.stats_block[1]['id'])
        save_entries: List[dict] = self.notion.query_db(middle_col[0]['id'])
        for save_prof in self.char.saving_throw_profs:
            for save_page in save_entries:
                if get_page_title(save_page) == skill_to_abbrev[save_prof]:
                    update_page_value(save_page, True, 'Proficient')
                    self.notion.update_page(save_page)
                    break

        check_entries: List[dict] = self.notion.client.databases.query(middle_col[1]['id'])['results']
        for check_prof in self.char.ability_check_profs:
            for save_page in check_entries:
                if get_page_title(save_page) == check_prof:  
                    update_page_value(save_page, True, 'Proficient')
                    self.notion.update_page(save_page)
                    break
                
    def right_stats_col(self):
        right_col = filter(lambda x: x['type'] == 'callout', self.notion.get_block_children(self.stats_block[2]['id']))
        data = [(self.char.max_hp, self.char.current_hp), self.char.ac, f'{self.char.level}d{self.char.hit_die}', 'SKIP', ('+' if self.char.skills[Skill.Dexterity.value] > 10 else '') + str(self.char.get_modifier(Skill.Dexterity.value)), 'SKIP', self.char.get_spell_casting_mod()]
        for block, to_update in zip(right_col, data):
            if type(to_update) == tuple:
                update_block_content(block, f'HP ({to_update[0]})', 0)
                to_update = to_update[1]
            elif to_update == 'SKIP': continue
            update_block_content(block, to_update)
            self.notion.client.blocks.update(block['id'], **{block['type']: get_block_type_val(block)})
            
    def features_dbs(self):
        for (idx, char_features) in [(6, self.char.features), (7, self.char.other_features)]:
            if char_features:
                class_features_db_id = self.top_level_children[idx]['id']
                default_entry = self.notion.query_db(class_features_db_id)[0]
                template = self.notion.scrape_result(deepcopy(default_entry))
                block_template = self.notion.scrape_result(deepcopy(self.notion.get_block_children(default_entry['id'])[0]))
                default_entry['archived'] = True
                self.notion.update_page(default_entry)
                for feature in char_features:
                    to_send = deepcopy(template)
                    block_to_send = deepcopy(block_template)
                    update_page_value(to_send, feature, 'Name')
                    update_block_content(block_to_send, self.char.features[feature], 0)
                    new_page = self.notion.create_db_page(class_features_db_id, feature, '✨', to_send['properties'])
                    self.notion.append_block(new_page['id'], [block_to_send])
                
    def proficiencies_db(self):
        block_template = self.notion.scrape_result(self.notion.query_db(self.profs_and_weapons[0]['id'])[0])
        for prof in self.char.proficiencies:
            if type(self.char.proficiencies[prof]) == list:
                for p in self.char.proficiencies[prof]:
                    to_send = deepcopy(block_template)
                    update_page_value(to_send, p, 'Name')
                    update_page_value(to_send, prof, 'Tags')
                    self.notion.create_db_page(self.profs_and_weapons[0]['id'], p, '➕', to_send['properties'])
            else:
                to_send = deepcopy(block_template)
                update_page_value(to_send, p, 'Name')
                
    def weapons_db(self):
        profs_and_weapons = self.notion.get_block_children(self.inventory_blocks[0]['id'])
        block_template = self.notion.scrape_result(self.notion.query_db(profs_and_weapons[1]['id'])[0])
        for weapon in self.get_equipment(True):
            to_send = deepcopy(block_template)
            self.create_weapon_block(to_send, weapon)
            self.notion.create_db_page(profs_and_weapons[1]['id'], weapon.name, get_weapon_emoji(weapon), to_send['properties'])
            
    def money_and_equipment(self):
        money_and_equipment = self.notion.get_block_children(self.inventory_blocks[1]['id'])
        block_template = self.notion.scrape_result(self.notion.query_db(money_and_equipment[2]['id'])[0])
        for eq_name, eq_type in self.get_equipment(False):
            to_send = deepcopy(block_template)
            update_page_value(to_send, eq_type, 'Tags')
            update_page_value(to_send, eq_name, 'Name')
            update_page_value(to_send, '0', 'Name')
            self.notion.create_db_page(money_and_equipment[2]['id'], eq_name, '🎒', to_send['properties'])
        
def fill_character_sheet_template(template_id: str, character_name: str):
    template_filler = TemplateFiller(character_name, template_id)

    # update name
    '''
    template_filler.title()
    # header blocks
    template_filler.header_blocks()
    '''
    template_filler.stats_block = template_filler.notion.get_block_children(template_filler.top_level_children[4]['id'])
    # template_filler.left_stat_col()
    # template_filler.middle_stats_col()
    # template_filler.right_stats_col()
    # template_filler.features_dbs()
    
    template_filler.inventory_blocks = template_filler.notion.get_block_children(template_filler.top_level_children[9]['id'])
    # template_filler.proficiencies_db()
    # template_filler.weapons_db()
    # template_filler.money_and_equipment()