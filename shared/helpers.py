from typing import Any, List, Tuple
import json
from word2number.w2n import word_to_num

get_var_case = lambda text: text.lower().replace(" ", "_")


def parse_strong(text: str) -> Tuple[str, str | None]:
    """
    Wikidot uses the convention
        <p><strong>Column name</strong>column data</p>
    to store some information, and this method parses the 'column data'
    """
    idx = text.find("/strong>")
    brDx = text.find("<br")
    # sometimes the colon is outside the strong box so we need to get rid of it
    parsed_text = text[idx + 8 : brDx if brDx != -1 else -4].replace(": ", "")
    part2 = text[brDx + 8 :] if brDx != -1 else None
    return parsed_text, part2


def get_dice_info(text: str) -> tuple[int, int]:
    """
    given a die descriptor (1d6, 2d8, etc.) returns the numerical values
    """
    parts = text.lower().split("d")
    if len(parts) != 2:
        raise ValueError(f"Invalid dice format: {text}")
    return (int(parts[0]), int(parts[1]))


def write_obj_to_json(obj: Any, path: str) -> None:
    if type(obj) == list:
        to_overwrite = []
        for entity in obj:
            to_overwrite.append(serialize(entity) if type(obj) != dict else obj)
        obj = to_overwrite
    elif type(obj) != dict:
        obj = serialize(obj)
    write_serialized_obj_to_disk(obj, path)


def write_serialized_obj_to_disk(obj: Any, path: str):
    with open(path, "w") as fp:
        json.dump(obj, fp, indent=4)


def serialize(obj):
    d = {}
    for attr in obj.__dir__():
        if attr[0] != "_" and not type(obj.__getattribute__(attr)).__name__ == "method":
            if type(obj.__getattribute__(attr)) == set:
                v = list(obj.__getattribute__(attr))
            else:
                v = obj.__getattribute__(attr)
            d[attr] = v
    return d


def safe_word_to_num(word: str) -> float | int:
    try:
        if word in ["an", "a"]:
            return 1
        if "/" in word:
            vals = word.split("/")
            return word_to_num(vals[0]) / word_to_num(vals[1])
        elif word == "—":
            return 0
        else:
            return word_to_num(word)
    except:
        return 0


def load_obj_from_dict(d, objType):
    if objType == dict:
        return d
    s = objType()
    for key in d:
        try:
            t = s.__getattribute__(key)
            setattr(s, key, type(t)(d[key]))
        except:
            setattr(s, key, d[key])
    return s


def load_json_object(filename, objType) -> List[object] | object:
    with open(filename, "rb") as fp:
        objects = json.loads(fp.read())
        if type(objects) == list:
            objects = [load_obj_from_dict(obj, objType) for obj in objects]
        else:
            objects = load_obj_from_dict(objects, objType)
    return objects


def pick(obj, *options):
    to_ret = {}
    for option in options:
        if option in obj:
            to_ret[option] = obj[option]
    return to_ret
