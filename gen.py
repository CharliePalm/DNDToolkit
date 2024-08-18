
import argparse
from generator import generator
parser = argparse.ArgumentParser()

generator_group = parser.add_argument_group('generator')
generator_group.add_argument('--gen-char', action='store_true')
generator_group.add_argument('--character-class', '-cc')
generator_group.add_argument('--name', '-n')
generator_group.add_argument('--species', '-s')
generator_group.add_argument('--level', '-l', required=True)
generator_group.add_argument('--dry-run', '-dr', action='store_true')
generator_group.add_argument('--sub-class', '-sc')

if __name__ == '__main__':
    args = parser.parse_args()
    print(args)
    if args.gen_char:
        character_class, name, species, level, subclass = args.character_class, args.name, args.species, args.level, args.sub_class
        gen = generator.Generator(name=name, character_class=character_class, species=species, level=level)
        gen.execute(args.dry_run)
        