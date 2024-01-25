#!/usr/bin/env python3

import sys
import argparse
import pathlib
import crcmod
import yaml

from legictk.legic import LegicMemBlock


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', type=pathlib.Path, required=True)
    parser.add_argument('-o', type=pathlib.Path)

    args = parser.parse_args()

    if not args.o:
        args.o = args.f.with_name("out.bin")

    with open(args.f, 'rb') as f:
        b = bytearray(f.read())

    legic = LegicMemBlock.from_bytearray(b)
    out = legic.to_bytearray(obfuscate=False)

    with open(args.o, 'wb') as f:
        f.write(out)


if __name__ == '__main__':
    sys.exit(main())
