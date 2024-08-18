import argparse
from equipment_loader.scraper import get_all_weapons

parser = argparse.ArgumentParser()
spell_loader_group = parser.add_argument_group('equipment-lodare')
spell_loader_group.add_argument('--dry-run', '-dr', action='store_true')
spell_loader_group.add_argument('--get-all-weapons', '-gas', action='store_true')
spell_loader_group.add_argument('--save', action='store_true')

if __name__ == '__main__':
    args = parser.parse_args()
    if args.get_all_weapons:
        get_all_weapons(args.dry_run)