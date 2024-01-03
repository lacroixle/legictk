#!/usr/bin/env python3
#

from collections.abc import Iterable


def print_hex_block(block, column_bytes=8, column_count=2):
    for i, byte in enumerate(block):
        print(hex(byte)[2:].zfill(2).upper(), end="")
        if ((i+1) % (column_bytes*column_count)) == 0:
            print("")
        elif ((i+1) % column_bytes) == 0:
            print("  ", end="")
        else:
            print(" ", end="")

    print("")

def to_hex_string(array):
    if isinstance(array, Iterable):
        return "".join("{:02x}".format(b) for b in array).upper()
    else:
        return "{:02x}".format(array).upper()
