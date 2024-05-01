from bs4 import BeautifulSoup
from pprint import pprint
from typing import Tuple, List
import re
from shared.model import Spell, Components, CharacterClass, Tag
from shared.notion.notion_interface import get_notion_bullet
import csv
from .cleaner import add_description_info
from .requestor import get_spell_html
import json
base_url = 'http://dnd5e.wikidot.com/'

'''
This file scrapes actual html strings
'''

def get_school_level_and_tags(text: str) -> Tuple[int, str, List[str]]:
    '''
    given (Conjuration cantrip, 1st-level abjuration, etc) returns level, school
    '''
    vals = re.findall(r'\(([^)]*)\)', text)
    if vals:
        vals = vals[0].split(':')
        tags = [Tag[v[0].upper() + v[1:]].value for v in vals]
        text = re.sub(r'\([^)]*\)', '', text).strip()
    else: tags = []
    if text[0].isdigit():
        return (int(text[0]), text[10].upper() + text[11:], tags)
    return (0, text[:text.index(' ')], tags)


def remove_html_tags(text):
    return re.sub(r'<[^>]*>', '', text)

def parse_strong(text: str) -> Tuple[str, str]:
    '''
    Wikidot uses the convention 
        <p><strong>Column name</strong>column data</p>
    to store some information, and this method parses the 'column data'
    '''
    idx = text.find('/strong>')
    brDx = text.find('<br')
    # sometimes the colon is outside the strong box so we need to get rid of it
    parsed_text = text[idx+8:brDx if brDx != -1 else -4].replace(': ', '')
    text = text[brDx+8:] if brDx != -1 else None
    return parsed_text, text

def get_component_tags_from_string(text: str,) -> Tuple[List[str], str]:
    materials = ''
    parentheses_idx = text.find('(')
    if parentheses_idx != -1:
        materials = text[parentheses_idx+1:text.find(')')]
        text = text[:parentheses_idx]
    return [Components[val].value for val in text.replace(' ', '').split(',')], materials
    
def parse_classes(text: str) -> List[str]:
    classes = []
    while text != '</p>' and len(text) > 10:
        idx = text.find('">')
        parsed_text = text[idx+2:text.find('</a>')]
        classes.append(CharacterClass[re.sub(r'\([^)]*\)', '', parsed_text).strip()].value)
        text = text[text.find('</a>')+4:]
    return classes

def remove_p_tags(text: str) -> str:
    return text[3:-4] # remove p tags

def remove_html_tags(text):
    return re.sub(r'<[^>]*>', '', text)


def parse_spell(html, is_fighter, is_rogue) -> Spell:
    spell = Spell()
    
    soup = BeautifulSoup(html,'html.parser')
    title = soup.find('title')
    spell.name = title.text[:title.text.find(' -')].replace(' (UA)', '').replace(' (HB)', '')
    
    body = soup.find('div', attrs={'id':'page-content'})
    # change bullet point tags to p tags to use with description iteration
    uls = body.find_all('ul')
    for ul in uls:
        ul.name = 'p'
    ps = list(re.sub(r'\s+', ' ', str(p)) for p in body.find_all('p'))
    # some spells have this footer for information about potential balancing issues. I'm just deleting it for now as it's not relevant but might be a player-GM discussion
    if '<p><em><sup>' == ps[-1][:12]:
        del ps[-1]

    spell.source = ps[0][11:-4] # first p is always the source, and we clean the tags off immediately
    ua_addition_idx = spell.source.find('Arcana')
    # Wikidot adds a class suffix on UA spells that messes up tags/enums
    if ua_addition_idx != -1:
        spell.source = spell.source[:ua_addition_idx + 6]
    # same is true for critical role spells
    if 'Crit' in spell.source:
        spell.source = spell.source[:13]

    spell.level, spell.school, spell.tags = get_school_level_and_tags(ps[1][7:-9]) 
    idx = 2 #idx for ps

    spell.cast_time, ps[idx] = remove_html_tags(parse_strong(ps[idx]))
    if not ps[idx]: idx += 1
    spell.range, ps[idx] = remove_html_tags(parse_strong(ps[idx]))
    if not ps[idx]: idx += 1
    component_str, ps[idx] = remove_html_tags(parse_strong(ps[idx]))
    if not ps[idx]: idx += 1
    spell.components, spell.materials = get_component_tags_from_string(component_str)
    spell.duration = remove_html_tags(parse_strong(ps[idx])[0])
    idx += 1
    spell.description = remove_p_tags(ps[idx])
    idx += 1

    # for multiple paragraphs of description we just add to the existing description
    while idx != len(ps) - 1:
        if ps[idx][4:8] == '<li>':
            spell.description += '\n\n•' + ps[idx]
        elif '<strong>' in ps[idx]:
            spell.higher_levels = parse_strong(ps[idx])[0] # clean off end p tag, this is the last strong in this p section
        else:
            spell.description += '\n\n' + remove_p_tags(ps[idx])
        idx += 1
    # wikidot sometimes has links of the form <a href="...">content</a> so we can just remove those
    spell.description = remove_html_tags(spell.description)
    add_description_info(spell)
    
    spell.classes = parse_classes(ps[idx])
    if is_fighter:
        spell.classes.append(CharacterClass.Fighter.value)
    if is_rogue:
        spell.classes.append(CharacterClass.Rogue.value)
    return spell
    
def open_hrefs(file_name = 'all_hrefs.csv') -> List[str]:
    with open('./spell_loader/hrefs/' + file_name, 'r') as fp:
        reader = csv.reader(fp)
        for line in reader:
            hrefs = line
    return hrefs

def scrape_spell(href: str, is_fighter = False, is_rogue = False) -> Spell:
    spell_html = get_spell_html(href)
    spell = parse_spell(spell_html, is_fighter, is_rogue)
    return spell

def scrape_all_spells():
    all_hrefs = open_hrefs()
    fighter_hrefs = open_hrefs('fighter.csv')
    rogue_hrefs = open_hrefs('rogue.csv')
    spells = []
    for href in all_hrefs:
        print('parsing ' + href)
        spell = scrape_spell(href, href in fighter_hrefs, href in rogue_hrefs)
        spells.append(spell.__dict__)

    with open('./spell_loader/spells.json', 'w') as f:
        json.dump(spells, f)