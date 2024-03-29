#!/usr/bin/env python3

import sys
import argparse
import pathlib
import crcmod
import yaml

from legictk.legic import LegicMemBlock
from legictk.printutils import print_hex_block


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', type=pathlib.Path, required=True)
    parser.add_argument('-o', type=pathlib.Path)
    parser.add_argument('--kinds', type=str)
    parser.add_argument('--is-deobfuscated', action='store_true')
    parser.add_argument('--obfuscate', action='store_true')

    args = parser.parse_args()

    if not args.o:
        args.o = args.f.with_name("out.yaml")

    with open(args.f, 'rb') as f:
        b = bytearray(f.read())

    l = LegicMemBlock.from_yaml(args.f, is_obfuscated=not args.is_deobfuscated)
    b = l.to_bytearray(obfuscate=args.obfuscate)
    with open(args.o, 'wb') as f:
         f.write(b)


if __name__ == '__main__':
    sys.exit(main())
