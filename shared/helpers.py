
from typing import List, Tuple
import json
from word2number.w2n import word_to_num

get_var_case = lambda text: text.lower().replace(' ', '_')
    
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

def get_dice_info(text: str) -> Tuple[int, int]:
    '''
    given a die descriptor (1d6, 2d8, etc.) returns the numerical values
    '''
    return tuple(int(t) for t in text.split('d'))

def write_obj_to_json(obj: any, path: str) -> None:
    if type(obj) == list:
        to_overwrite = []
        for entity in obj:
            to_overwrite.append(serialize(entity))
        obj = to_overwrite
    else: obj = serialize(obj)
    write_serialized_obj_to_disk(obj, path)

def write_serialized_obj_to_disk(obj: any, path:str):
    with open(path, 'w') as fp:
        json.dump(obj, fp, indent=4)

    
def serialize(obj):
    d = {}
    for attr in obj.__dir__():
        if attr[0] != '_' and not type(obj.__getattribute__(attr)).__name__ == 'method':
            if type(obj.__getattribute__(attr)) == set:
                v = list(obj.__getattribute__(attr))
            else:
                v = obj.__getattribute__(attr)    
            d[attr] = v
    return d

def safe_word_to_num(word: str) -> float | int:
    try: 
        if word in ['an', 'a']:
            return 1
        if '/' in word:
            vals = word.split('/')
            return word_to_num(vals[0]) / word_to_num(vals[1])
        elif word == '—':
            return 0
        else:
            return word_to_num(word)
    except:
        return 0

def load_obj_from_dict(d, objType):
    if objType == dict: return d
    s = objType()
    for key in d:
        try:
            t = s.__getattribute__(key)
            setattr(s, key, type(t)(d[key]))
        except:
            setattr(s, key, (d[key]))
    return s

def load_json_object(filename, objType) -> List[object] | object:
    with open(filename, 'rb') as fp:
        objects = json.loads(fp.read())
        objects = load_obj_from_dict(objects, objType)
    return objects

def pick(obj, *options):
    to_ret = {}
    for option in options:
        if option in obj:
            to_ret[option] = obj[option]
    return to_ret
    