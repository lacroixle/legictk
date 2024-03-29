#!/usr/bin/env python3

import sys
import argparse
import pathlib

from legictk.printutils import print_hex_block, to_hex_string
from legictk.legic import LegicMemBlock
from legictk.trace import Trace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trace', type=pathlib.Path, required=True)
    parser.add_argument('--dump', type=pathlib.Path, required=True)
    parser.add_argument('--write-op', action='store_true')

    args = parser.parse_args()

    with open(args.dump, 'rb') as f:
        b = bytearray(f.read())
        dump = LegicMemBlock.from_bytearray(b)

    trace = Trace.from_file(args.trace)
    read_addresses = trace.rw_addresses(not args.write_op)

    def _shift_addresses(addresses, shift):
        return list(filter(lambda x: x>=0, map(lambda x: x-shift, addresses)))

    if args.write_op:
        print("Write addresses from trace {} in Legic Prime dump {}".format(args.trace.name, args.dump.name))
    else:
        print("Read addresses from trace {} in Legic Prime dump {}".format(args.trace.name, args.dump.name))

    print("")
    print("Legic Prime header ===============================")
    print_hex_block(dump.header.to_bytearray(), highlight_addresses=read_addresses)
    print("")

    read_addresses = _shift_addresses(read_addresses, dump.header.length)
    for i, segment in enumerate(dump.segments):
        print("Segment {} ========================================".format(i+1))
        print("Header:")
        print_hex_block(segment.header_bytearray(obfuscate=False), highlight_addresses=read_addresses)
        read_addresses = _shift_addresses(read_addresses, 5)
        print("Stamp:")
        stamp = segment.wrp(obfuscate=False)
        print_hex_block(stamp, highlight_addresses=read_addresses)
        read_addresses = _shift_addresses(read_addresses, len(stamp))
        print("Payload:")
        payload = segment.payload(obfuscate=False)
        print_hex_block(payload, highlight_addresses=read_addresses)
        read_addresses = _shift_addresses(read_addresses, len(payload))
        print("")

    print("==================================================")


if __name__ == '__main__':
    sys.exit(main())
