#!/usr/bin/env python3

import crcmod


def reflect(x):
    return (x * 0x0202020202 & 0x010884422010) % 1023


crc8 = crcmod.mkCrcFun(0x163, initCrc=0x55, xorOut=0x0)


def crc8_legic(x):
    return reflect(crc8(x))


def obfuscate_bytearray(b, crc):
    _b = b.copy()
    for i in range(len(b)):
        _b[i] = _b[i] ^ crc

    return _b

def deobfuscate_bytearray(b, crc):
    return obfuscate_bytearray(b, crc)
