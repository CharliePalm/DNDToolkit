

from typing import List, Set
from shared.helpers import safe_word_to_num, write_obj_to_json
from shared.model import Weapon, WeaponFamily
from shared.requestor import make_get_request
from bs4 import BeautifulSoup
import re

def get_all_weapons(is_dry_run):
    html = None
    if is_dry_run:
        with open('./equipment_loader/equipment.html', 'r') as fp:
            html = fp.read()
    if not html:
        html = make_get_request('https://dnd5e.wikidot.com/weapons')
    soup = BeautifulSoup(html, features="html.parser")
    equipment_tables = soup.find_all('table', {'class': 'wiki-content-table'})[:2]
    weapons = []
    for idx, table in enumerate(equipment_tables):
        rows = table.find_all('tr')
        for row in rows:
            tds = [r.get_text().replace(u'\xa0', u' ') for r in  row.find_all('td')]
            if tds:
                weapon = Weapon()
                weapon.name = tds[0]
                weapon.cost = safe_word_to_num(tds[1].split(' ')[0])
                if tds[1].split(' ')[1] != 'gp':
                    if tds[1].split(' ')[1] == 'sp': weapon.cost = weapon.cost / 10
                    else: weapon.cost = weapon.cost / 100
                if tds[2] != '—':
                    weapon.damage, weapon.damage_type = tds[2].split(' ')
                    weapon.damage_type = weapon.damage_type.capitalize()
                else: weapon.damage, weapon.damage_type = 0, ''
                weapon.weight = safe_word_to_num(tds[3].split(' ')[0])
                weapon.properties = set(p.capitalize() for p in tds[4].split(', '))
                to_remove = None
                for p in weapon.properties:
                    lower_p = p.lower()
                    if 'thrown' in lower_p or 'range' in lower_p:
                        to_remove = p
                        weapon.range_normal, weapon.range_max = [int(v) for v in re.search(r'\((.*?)\)', p).group(1).split('/')]
                    if p == '—':
                        to_remove = p
                if to_remove:
                    weapon.properties.remove(to_remove)
                weapon.family = WeaponFamily.Simple.value if idx == 0 else WeaponFamily.Martial.value
                weapons.append(weapon)
    
    write_obj_to_json(weapons, './equipment_loader/weapons.json')