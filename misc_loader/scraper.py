

from typing import List, Set
from shared.helpers import safe_word_to_num, write_obj_to_json
from shared.model import Weapon, WeaponFamily
from shared.requestor import make_get_request
from bs4 import BeautifulSoup, Tag
import re
from pprint import pprint
def get_all_weapons(is_dry_run):
    html = None
    if is_dry_run:
        with open('./misc_loader/equipment.html', 'r') as fp:
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
    
    write_obj_to_json(weapons, './misc_loader/weapons.json')


def get_all_backgrounds(is_dry_run):
    html = None
    if is_dry_run:
        with open('./misc_loader/backgrounds.html', 'r') as fp:
            html = fp.read()
    if not html:
        html = make_get_request('https://5ebackgrounds.com/')
        with open('./misc_loader/backgrounds.html', 'w') as fp:
            fp.write(html)
        
    soup = BeautifulSoup(html, features="html.parser")
    
    rows = soup.find('table', attrs={'id': 'tablepress-1'}).find_all('tr')
    bgs: List[Tag] = [(row.find('td', attrs={'class':'column-1'}), row.find('td', attrs={'class':'column-6'})) for row in rows[1:]]
    #pprint([(a.text, b.text) if a else '' for a, b in bgs])
    to_write = {}
    for key, val in bgs[1:]:
        if not val or len(val.text) == 0 or 'special' in val.text: continue
        val = val.text
        if 'choose' in val.lower():
            val = re.sub(r'\bChoose\s+(\d+):', r'\1' + ',', val, flags=re.IGNORECASE).replace(', and ', ', ')
        val = [word.strip().capitalize() for word in re.sub( r'\(.*?\)', '', val.replace(' and ', ', ')).split(', ')]
        to_write[key.text] = val
    write_obj_to_json(to_write, './misc_loader/backgrounds.json')