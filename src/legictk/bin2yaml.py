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
        args.o = args.f.with_name("out.bin")

    with open(args.f, 'rb') as f:
        b = bytearray(f.read())

    kinds = None
    if args.kinds:
        kinds = args.kinds.split(",")

    legic = LegicMemBlock.from_bytearray(b, kinds=kinds)
    legic.to_yaml(args.o, obfuscate=args.obfuscate)

if __name__ == '__main__':
    sys.exit(main())
