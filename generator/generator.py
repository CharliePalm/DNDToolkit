from random import choice, randint, sample
from typing import List
from shared.helpers import get_dice_info, get_var_case, parse_strong, safe_word_to_num, write_obj_to_json, load_json_object
from shared.model import CharacterClass, Character, Skill, Species, Weapon, WeaponFamily, skill_priority_tree, standard_skill_arr
from bs4 import BeautifulSoup, Tag
from shared.requestor import get_class_html
from pprint import pprint
import re
from word2number.w2n import word_to_num
import json

word_to_num('two')
should_be_number = lambda val: type(val) == int or val.replace('+', '').isnumeric()
clean_col = lambda col: int(col) if should_be_number(col) else col
indicates_one = lambda val: val == 'a' or val == 'an'

class Generator:
    level: int = 0
    def __init__(self, **kwargs):
        for arg in kwargs:
            self.__setattr__(arg, kwargs.get(arg))
        self.level = int(self.level)

    def parse_header_table(self):
        class_table = self.soup.find('table')
        rows = class_table.find_all('tr')
        self.features = []
        headers = [get_var_case(h.text.strip()) for h in rows[1].findAll('th')]

        # parses 
        for row in rows[2:(self.level+2)]:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            for idx, col in enumerate(cols):
                if headers[idx] == 'features':
                    self.features.extend(col.split(', '))
                else:
                    if col == '-':
                        col = 0
                    if headers[idx] in ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th']:
                        self.char.spell_slots[int(headers[idx][0])] = clean_col(col)
                    elif headers[idx] != 'level':
                        self.char.__setattr__(headers[idx], clean_col(col))

    def manage_choice(self, element: Tag):
        element.find_next('table')
        # rows = table_element.find_all('a')
        # print(rows)

    def get_features(self):
        features = self.soup.find('div', {'class': 'feature'})
        profs_headers = features.find_all('h5')
        self.add_base_proficiencies_and_equipment(profs_headers)
        class_headers: List[Tag] = features.find_all('h3')
        header_idx = 0
        for f in class_headers[0].nextSiblingGenerator():
            if header_idx >= len(self.features):
                break
            if f == class_headers[header_idx + 1]:
                header_idx += 1
                continue
            text = f.get_text()
            if 'choose' in text[:75]:
                self.manage_choice(f)
            if self.features[header_idx] not in self.char.features:
                self.char.features[self.features[header_idx]] = ''
            self.char.features[self.features[header_idx]] += text[:-1]
        
    def choose_skills(self):
        skill_map = skill_priority_tree[CharacterClass(self.char.character_class)]
        skill_arr_idx = 0
        skills = set(Skill)
        for skill_arr_idx in range(len(standard_skill_arr)):
            if skill_map:
                keys = list(skill_map.keys())
            else:
                keys = list(skills)
            key = choice(keys) if len(keys) > 1 else keys[0]
            skills.remove(key)
            self.char.skills[key.value] = standard_skill_arr[skill_arr_idx]
            if skill_map: skill_map = skill_map[key]

    def add_species_features(self):
        # todo, get species features and bonuses
        pass

    def add_base_proficiencies_and_equipment(self, feature_soup: List[Tag]):
        # hit dice
        f = feature_soup[0].find_next_sibling()
        self.char.hit_die = get_dice_info(re.search(r'\b\d+d\d+\b', f.get_text()).group())[1]
        self.char.hit_points = self.char.hit_die + sum([randint(2, self.char.hit_die) + self.char.get_modifier(Skill.Constitution.value) for _ in range(self.char.level - 1)])
        
        # proficiencies 
        f = feature_soup[1].find_next_sibling()
        strongs, next_text = [s.get_text() for s in f.find_all('strong')], str(f)
        for strong in strongs:
            prof, next_text = parse_strong(next_text)
            prof = prof.strip()
            if strong == 'Saving Throws:':
                for p in prof.split(', '):
                    self.char.saving_throw_profs.add(p)
            elif strong == 'Skills:':
                # check if we need to make a choice
                num = re.search(r'\b[Cc]hoose\s+(\w+)', prof)
                if num:
                    num =  word_to_num(num.group())
                    skills = sample(re.search(r'\bfrom\b\s*(.*)', prof).group().split(', '), num)
                else: skills = prof
                [self.char.ability_check_profs.add(skill.capitalize()) for skill in skills]
            elif prof != 'None':
                # remove last colon
                self.char.proficiencies[strong[:-1]] = [p.capitalize() for p in prof.split(', ')]

        # equipment
        f = feature_soup[2].find_next_sibling().find_next_sibling()
        for li in f.find_all('li'):
            li = li.get_text()
            # look to see if we have multiple options
            matches = re.findall(r'\(\w\)\s*(.*?)(?=\s*\(\w\)|$)', li)
            if matches:
                matches = [re.sub(r'\b(and|or)\b', '', match).strip() for match in matches]
                if 'martial' in matches[1]:
                    weapons: List[Weapon] = load_json_object('./equipment_loader/weapons.json', Weapon)
                    f = lambda v: v.family == WeaponFamily.Martial.value and ('Ammunition' not in v.properties if 'melee' in matches[1] else ('Ammunition' in v.properties if 'ranged' in matches[1] else True))
                    self.char.equipment.append((choice(list(filter(f, weapons))).name, 1))
                elif 'simple' in matches[1]:
                    f = lambda v: v.family == WeaponFamily.Simple.value and ('Ammunition' not in v.properties if 'melee' in matches[1] else ('Ammunition' in v.properties if 'ranged' in matches[1] else True))
                    self.char.equipment.append((choice(list(filter(f, weapons))).name, 1))
                else:
                    # todo figure out how to handle non choices
                    print(matches)
                continue

            # might get multiple things with an "and" splitting them
            matches = li.split(' and ')
            for match in matches:
                num = safe_word_to_num(re.search(r'^\s*(\w+)', match).group(1))
                self.char.equipment.append((re.search(r'^\s*\w+\s+(.*)', match).group(1).strip().capitalize(), num or 1))
            

    def make_base_selections(self):
        if self.species:
            self.char.species = self.species
        else:
            self.char.species = choice(list(Species)).value
        self.add_species_features()
        self.choose_skills()

    def execute(self, dry_run):
        self.char = Character()
        self.char.level = int(self.level)
        self.char.name = self.name or 'my_char'
        self.char.character_class = choice(list(CharacterClass)).value if not self.character_class else CharacterClass(self.character_class[0].upper() + self.character_class[1:]).value
        self.make_base_selections()
        html = None
        if dry_run:
            with open('./generator/test_html/'+get_var_case(self.char.character_class)+'.html', 'r') as fp:
                html = fp.read()
        if html is None or html == '':
            html = get_class_html(self.char.character_class)
        self.soup = BeautifulSoup(html, 'html.parser')
        self.parse_header_table()
        self.get_features()
        # print(self.char)
        write_obj_to_json(self.char, f'./generator/{self.char.name}.json')