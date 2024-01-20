#!/usr/bin/env python3

# from colorama import init
from termcolor import colored
from collections.abc import Iterable


def print_hex_block(block, column_bytes=8, column_count=2, highlight_addresses=None, highlight_color='green'):
    for i, byte in enumerate(block):
        if highlight_addresses is not None and i in highlight_addresses:
            print(colored(hex(byte)[2:].zfill(2).upper(), highlight_color), end="")
        else:
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
