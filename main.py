import argparse
from shared.helpers import write_obj_to_json, write_serialized_obj_to_disk
from shared.notion.fill_template import fill_character_sheet_template
from shared.notion.notion import Notion
from spell_loader import cleaner, dry_run, scraper
import json
parser = argparse.ArgumentParser()
spell_loader_group = parser.add_argument_group('spell-loader')
spell_loader_group.add_argument('--clean', '-c', action='store_true')
spell_loader_group.add_argument('--dry-run', '-dr')
spell_loader_group.add_argument('--get-spell', '-gs')
spell_loader_group.add_argument('--get-all-spells', '-gas', action='store_true')
spell_loader_group.add_argument('--save', action='store_true')

notion_group = parser.add_argument_group('notion')
notion_group.add_argument('--get', '-g')
notion_group.add_argument('--get-page', '-gp')
notion_group.add_argument('--get-full', '-gf')
notion_group.add_argument('--get-db', '-gdb')
notion_group.add_argument('--get-block', '-gb')
notion_group.add_argument('--query-db', '-qd')
notion_group.add_argument('--put-all', '-pa', action='store_true')
notion_group.add_argument('--obj')
notion_group.add_argument('--put', '-p')
notion_group.add_argument('--name', '-n')
notion_group.add_argument('--fill-template', '-ft')
notion_group.add_argument('--scrape', '-s', action='store_true')
notion_group.add_argument('--create-db-test', action='store_true')

def get_func_and_params(args):
    if args.get: return notion.get_block_children, args.get
    if args.get_page: return notion.get_page, args.get_page
    if args.get_db: return notion.get_db, args.get_db
    if args.get_full: return notion.get_page_deep_copy, args.get_full
    if args.get_block: return notion.get_block, args.get_block
    if args.query_db: return notion.query_db, args.query_db

if __name__ == '__main__':
    args = parser.parse_args()
    if args.dry_run:
        if args.dry_run == 'all': 
            dry_run.full_dry_run()
        else:
            for spell in args.dry_run.split(' '):
                spell = dry_run.spell_dry_run(spell + '.txt')
                if args.save:
                    scraper.dump_spells([spell.__dict__])
    if args.clean:
        cleaner.check_spells_for_incomplete_descriptions()
    if args.get_spell:
        spells = [scraper.scrape_spell('/spell:' + spell).__dict__ for spell in args.get_spell.split(' ')]
        with open('./output.json', 'w') as fp:
            fp.write(json.dumps(spells, indent=4))
    if args.get_all_spells:
        scraper.scrape_all_spells()

    # notion args
    notion = Notion()
    if args.create_db_test:
        notion._create_db_test()
    if args.fill_template: fill_character_sheet_template(args.fill_template, args.name)
    if args.get or args.get_page or args.get_full or args.get_db or args.get_block or args.query_db:
        func, param = get_func_and_params(args)
        result = func(param)
        if args.save or args.scrape:
            result = notion.scrape_result(result) if args.scrape else result
            write_serialized_obj_to_disk(result, './results.json')
        else: print(json.dumps(result, indent=4))
    if args.put_all:
        if args.obj == 'Weapon':
            notion.upload_all_weapons()
        elif args.obj == 'Spell':
            notion.upload_all_spells()
    if args.put:
        if args.obj == 'Weapon':
            notion.upload_weapon(args.put)
        elif args.obj == 'Spell':
            notion.upload_spell(args.put)
        elif args.obj == 'Character':
            notion.upload_character(args.put)