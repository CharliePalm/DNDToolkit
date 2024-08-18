import os
from .scraper import parse_spell
directory = os.fsencode('./spell_loader/practice_spells')
    
def full_dry_run():
    for file in os.listdir(directory):
        file_name = os.fsdecode(file)
        spell_dry_run(file_name)


def spell_dry_run(spell_file):
    with open('./spell_loader/practice_spells/' + spell_file) as fp:
        s = ''
        line = fp.readline()
        while line:
            s += line
            line = fp.readline()
        spell = parse_spell(s, False, False)
        print(str(spell))
        return spell