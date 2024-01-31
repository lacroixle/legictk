#!/usr/bin/env python3

import math

class Trace:
    def __init__(self, traces):
        self._traces = traces

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'rb') as f:
            b = f.read()

        initial_timestamp = None
        cont = True
        idx = 0
        traces = []
        while cont:
            timestamp = int.from_bytes(b[idx:idx+4], 'little')
            duration = int.from_bytes(b[idx+4:idx+6], 'little')
            data_length = int.from_bytes(b[idx+6:idx+8], 'little') & 0b0111111111111111
            is_response = bool(b[idx+7] & (1<<7))
            data = b[idx+8:idx+8+data_length]
            parity_length = math.ceil(data_length/8)
            parity = b[idx+8+data_length:idx+8+data_length+parity_length]

            traces.append({'timestamp': timestamp, 'duration': duration, 'is_response': is_response, 'data': data, 'parity': parity})
            idx = idx + 8 + data_length + parity_length

            if idx >= len(b):
                cont = False

        return cls(traces)

    def rw_addresses(self, read=True):
        if read:
            op_cmdbit = 1
        else:
            op_cmdbit = 0

        addresses = []
        for trace in self._traces:
            data = trace['data']
            bitsend = int(data[0])
            cmdbit = int(data[1] & 1)
            if (bitsend == 9 or bitsend == 11) and (cmdbit == op_cmdbit):
                addresses.append((data[2] << 7) | (data[1] >> 1))
            elif (op_cmdbit == 0) & (bitsend == 21):
                addresses.append(((data[2] << 7) | (data[1] >> 1)) & 0xFF)
            elif (op_cmdbit == 0) & (bitsend == 23):
                addresses.append(((data[2] << 7) | (data[1] >> 1)) & 0x3FF)

        return sorted(list(set(addresses)))


