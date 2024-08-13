import argparse
from shared.notion.notion import Notion
from spell_loader import cleaner, dry_run, scraper
import json
parser = argparse.ArgumentParser()
spell_loader_group = parser.add_argument_group('spell-loader')
spell_loader_group.add_argument('--clean', '-c-', action='store_true')
spell_loader_group.add_argument('--dry-run', '-dr')
spell_loader_group.add_argument('--get-spell', '-gs')
spell_loader_group.add_argument('--get-all-spells', '-gas', action='store_true')
spell_loader_group.add_argument('--save', action='store_true')

notion_group = parser.add_argument_group('notion')
notion_group.add_argument('--get', '-g')
notion_group.add_argument('--put-all', '-pa', action='store_true')
notion_group.add_argument('--put', '-p')

if __name__ == '__main__':
    args = parser.parse_args()
    print(args)
    pass
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
    if args.get:
        notion = Notion()
        result = notion.get_db_page(args.get)
        print(result)
    if args.put_all:
        notion = Notion()
        notion.upload_all_spells()
    if args.put:
        notion = Notion()
        notion.upload_spell(args.put)