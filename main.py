import argparse
from shared.notion.notion import Notion
from spell_loader import cleaner, dry_run, scraper
parser = argparse.ArgumentParser()
spell_loader_group = parser.add_argument_group('spell-loader')
spell_loader_group.add_argument('--clean', '-c-', action='store_true')
spell_loader_group.add_argument('--dry-run', '-dr')
spell_loader_group.add_argument('--get-spell')
spell_loader_group.add_argument('--get-all-spells', '-gas', action='store_true')

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
                dry_run.spell_dry_run(spell + '.txt')
    if args.clean:
        cleaner.check_spells_for_incomplete_descriptions()
    if args.get_spell:
        spell = scraper.scrape_spell('/spell:' + args.get_spell)
        print(spell)
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