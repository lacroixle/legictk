
import yaml
import logging

from printutils import print_hex_block, to_hex_string
from bitutils import crc8_legic, obfuscate_bytearray, deobfuscate_bytearray


mim2size = {'mim22': 22,
            'mim256': 256,
            'mim1024': 1024}


class LegicMemBlock:
    def __init__(self, mim, header, segments):
        self.mim = mim
        self.header = header
        self.segments = segments

    @classmethod
    def from_file(cls, filename):
        pass

    @classmethod
    def from_bytearray(cls, block, kinds=None):
        if len(block) == 22:
            mim = 'mim22'
        elif len(block) == 256:
            mim == 'mim256'
        elif len(block) == 1024:
            mim = 'mim1024'
        else:
            raise ValueError("Legic MIM{} does not exist! (did you forget padding?)")

        header = LegicHeader.from_bytearray(block)

        if mim == 'mim22':
            return

        cont = True
        idx = header.length
        segments = []
        while cont:
            if kinds is not None:
                kind = kinds.pop(0)
            else:
                kind = 'raw'

            if kind == 'raw':
                segment = LegicSegment.from_bytearray(header, block, idx)
            elif kind == 'kgh':
                segment = LegicSegmentKGH.from_bytearray(header, block, idx)

            length = segment.length
            idx = idx + length

            if segment.final:
                cont = False

            segments.append(segment)

        return cls(mim, header, segments)

    @classmethod
    def from_yaml(cls, input_path, is_obfuscated=True):
        with open(input_path, 'r') as f:
            y = yaml.load(f, Loader=yaml.Loader)

        header = LegicHeader.from_dict(y['header'])

        segments = []
        segment_count = len(y['segments'].keys())
        for i in range(segment_count):
            d = {}
            d['header'] = y['segments'][i+1]['header']

            if d['header']['kind'] == 'raw':
                segment_wrp_path = y['segments'][i+1]['wrp']
                segment_payload_path = y['segments'][i+1]['payload']

                with open(segment_wrp_path, 'rb') as f:
                    d['wrp'] = bytearray(f.read())

                with open(segment_payload_path, 'rb') as f:
                    d['payload'] = bytearray(f.read())

                segments.append(LegicSegment.from_dict(header, d, is_obfuscated=is_obfuscated))
            elif d['header']['kind'] == 'kgh':
                segments.append(LegicSegmentKGH.from_dict(header, d))

        return cls('mim1024', header, segments)

    def to_yaml(self, output_path, obfuscate=True):
        y = {}
        y['header'] = self.header.to_dict()
        y['segments'] = {}

        for i, segment in enumerate(self.segments):
            d = segment.to_dict(obfuscate=obfuscate)
            y['segments'][i+1] = {}
            y['segments'][i+1]['header'] = d['header']
            y['segments'][i+1]['header']['kind'] = segment.kind

            if segment.kind == 'raw':
                y['segments'][i+1]['wrp'] = str(output_path.with_name("segment{}_wrp.bin".format(i+1)))
                y['segments'][i+1]['payload'] = str(output_path.with_name("segment{}_payload.bin".format(i+1)))

                with open(output_path.with_name("segment{}_wrp.bin".format(i+1)), 'wb') as f:
                    f.write(segment.wrp(obfuscate=obfuscate))

                with open(output_path.with_name("segment{}_payload.bin".format(i+1)), 'wb') as f:
                    f.write(segment.payload(obfuscate=obfuscate))

        with open(output_path, 'w') as f:
            yaml.dump(y, f)

    def to_bytearray(self, obfuscate=True):
        b = self.header.to_bytearray()
        for segment in self.segments:
            b = b + segment.to_bytearray(obfuscate=obfuscate)

        to_pad = mim2size[self.mim] - len(b)

        b = b + bytearray([0x00]*to_pad)

        return b


    def print(self):
        self.header.print()

        for segment in self.segments:
            print("="*50)
            segment.print_header()
            segment.print_payload()


class LegicHeader:
    def __init__(self, MCD, MSN, DCF, BCK):
        self.MCD = MCD
        self.MSN = MSN
        self.DCF = DCF
        self.BCK = BCK
        self.length = 22

        self.MCC = crc8_legic(self.UID)
        self.BCC = LegicHeader.compute_BCC(self.UID, self.BCK)

    @classmethod
    def from_bytearray(cls, b):
        MCD = bytearray(b[0:1])
        MSN = b[1:4]
        DCF = (b[6] << 8) + b[5]
        BCK = b[13:19]

        UID = b[0:4]
        MCC = b[4:5]
        BCC = b[19]

        # Fugly but okay..
        if MCC[0] != crc8_legic(UID):
            logging.warning("LegicHeader.from_bytearray(): wrong MCC CRC! Got {:02x}, should be {:02x}".format(MCC, crc8_legic(UID)))

        if BCC != LegicHeader.compute_BCC(UID, BCK):
            logging.warning("LegicHeader.from_bytearray(): wrong BCC CRC! Got {:02x}, should be {:02x}".format(int(BCC), int(LegicHeader.compute_BCC(UID, BCK))))

        return cls(MCD, MSN, DCF, BCK)

    @classmethod
    def from_dict(cls, d):
        MCD = bytearray.fromhex(d['MCD'])
        MSN = bytearray.fromhex(d['MSN'])
        DCF = bytearray.fromhex(d['DCF'])
        BCK = bytearray.fromhex(d['BCK'])

        return cls(MCD, MSN, DCF, BCK)

    def to_bytearray(self):
        block = bytearray([0x00]*self.length)

        block[0:1] = self.MCD
        block[1:4] = self.MSN
        block[4] = self.MCC
        # block[5:6] = self.DCF
        block[7:13] = bytearray([0x9F, 0xFF, 0x00, 0x00, 0x00, 0x11])
        block[13:19] = self.BCK
        block[19] = self.BCC

        return block

    def to_dict(self):
        d = {'MCD': to_hex_string(self.MCD),
             'MSN': to_hex_string(self.MSN),
             'DCF': to_hex_string(self.DCF),
             'BCK': to_hex_string(self.BCK)}
        return d

    @property
    def UID(self):
        return self.MCD + self.MSN

    def check_crc(self, silent=True):
        if not silent:
            logging.info("Checking Legic header CRCs")
            logging.info("CRC UID... ", end="")
        if crc8_legic(self.UID) == self.MCC:
            if not silent:
                logging.info("OK")
        else:
            logging.warning("CRC UID not matching!")

        print("CRC BCK... ", end="")
        if LegicHeader.compute_BCC(self.UID, self.BCK) == self.BCC:
            if not silent:
                logging.info("OK")
        else:
            logging.warning("CRC UID not matching!")

    @classmethod
    def compute_BCC(self, UID, BCK):
        b = UID + BCK
        b[4] = b[4] + 0x80
        return crc8_legic(b)

    def print(self):
        print("MCD={:02x}".format(self.MCD))
        print("MSN={}".format(to_hex_string(self.MSN)))
        print("MCC={:02x}".format(self.MCC))
        print("DCF={}".format(self.DCF))
        print("BCK={}".format(to_hex_string(self.BCK)))
        print("BCC={:02x}".format(self.BCC))


class LegicSegment:
    def __init__(self, legic_header, length, valid, final, wrc, rd, wrp, payload):
        self.legic_header = legic_header

        self.length = length
        self.valid = valid
        self.final = final
        self.wrc = wrc
        self.rd = rd

        self._wrp = wrp
        self._payload = payload

    @property
    def kind(self):
        return 'raw'

    @classmethod
    def from_bytearray(cls, legic_header, b, idx, is_obfuscated=True):
        if is_obfuscated:
            header_bytes = deobfuscate_bytearray(b[idx:idx+5], legic_header.MCC) # Deobfuscate first 5 bytes
        else:
            header_bytes = b[idx:idx+5]

        valid = bool(header_bytes[1] & (1 << 6))
        final = bool(header_bytes[1] & (1 << 7))
        wrc = (header_bytes[3] & 0b01110000) >> 4 # Not sure about this one
        rd = bool(header_bytes[3] & (1<<7))

        length = header_bytes[0] + ((header_bytes[1] & 0b00001111) << 8)
        wrp_length = header_bytes[2]
        payload_length = length - 5 - wrp_length

        assert (5+wrp_length+payload_length) == length

        wrp = b[idx+5:idx+5+wrp_length]
        payload = b[idx+5+wrp_length:idx+length]

        if is_obfuscated:
            wrp = deobfuscate_bytearray(wrp, legic_header.MCC)
            payload = deobfuscate_bytearray(payload, legic_header.MCC)

        return cls(legic_header, length, valid, final, wrc, rd, wrp, payload)

    @classmethod
    def from_dict(cls, legic_header, d, is_obfuscated=True):
        if is_obfuscated:
            wrp = deobfuscate_bytearray(d['wrp'], legic_header.MCC)
            payload = deobfuscate_bytearray(d['payload'], legic_header.MCC)
        else:
            wrp = d['wrp']
            payload = d['payload']

        return cls(legic_header, 5+len(d['wrp'])+len(d['payload']), d['header']['valid'], d['header']['final'], d['header']['wrc'], d['header']['rd'], wrp, payload)

    def header_bytearray(self, obfuscate=True):
        header = bytearray([0x00]*5)
        header[0] = int(self.length << 4) >> 4
        header[1] = int(self.length >> 8) << 8
        header[1] = header[1] | (self.valid << 6)
        header[1] = header[1] | (self.final << 7)
        header[2] = len(self.wrp())
        header[3] = self.rd << 7
        header[4] = crc8_legic(self.legic_header.UID + header[:4])

        if obfuscate:
            header = obfuscate_bytearray(header, self.legic_header.MCC)

        return header

    def to_bytearray(self, obfuscate=True):
        return self.header_bytearray(obfuscate=obfuscate) + self.wrp(obfuscate=obfuscate) + self.payload(obfuscate=obfuscate)

    def to_dict(self, obfuscate=True):
        d = {'final': self.final, 'valid': self.valid, 'wrc': self.wrc, 'rd': self.rd, 'kind': self.kind}

        return {'header': d, 'wrp': self.wrp(obfuscate=obfuscate), 'payload': self.payload(obfuscate=obfuscate)}

    def wrp(self, obfuscate=True):
        if obfuscate:
            return obfuscate_bytearray(self._wrp, self.legic_header.MCC)
        else:
            return self._wrp

    def payload(self, obfuscate=True):
        if obfuscate:
            return obfuscate_bytearray(self._payload, self.legic_header.MCC)
        else:
            return self._payload

    def print_header(self):
        print("Length={}".format(self.length))
        print("Valid={}".format(self.valid))
        print("Final={}".format(self.final))
        print("WRP={}".format(len(self.wrp)))
        print("WRC={}".format(self.wrc))
        print("RD={}".format(self.rd))


class LegicSegmentKGH(LegicSegment):
    def __init__(self, legic_header, length, valid, final, wrc, rd, stamp, key):
        self.stamp = stamp
        self.key = key

        # Fill in None WRP and payload as they are generated on the fly
        super().__init__(legic_header, length, valid, final, wrc, rd, None, None)

    @classmethod
    def from_bytearray(cls, legic_header, b, idx, is_obfuscated=True):
        segment = LegicSegment.from_bytearray(legic_header, b, idx, is_obfuscated=is_obfuscated)
        stamp = segment._wrp
        key = segment._payload[:3]
        return cls(legic_header, segment.length, segment.valid, segment.final, segment.wrc, segment.rd, stamp, key)

    @classmethod
    def from_dict(cls, legic_header, d):
        length = 5+len(bytearray.fromhex(d['header']['stamp']))+12
        return cls(legic_header, length, d['header']['valid'], d['header']['final'], d['header']['wrc'], d['header']['rd'], bytearray.fromhex(d['header']['stamp']), bytearray.fromhex(d['header']['key']))

    def to_dict(self, obfuscate=True):
        d = {'final': self.final, 'valid': self.valid, 'wrc': self.wrc, 'rd': self.rd, 'key': to_hex_string(self.key), 'stamp': to_hex_string(self.stamp), 'kind': self.kind}

        return {'header': d}

    def compute_KGC(self):
        print(self.key)
        print(self.header_bytearray(obfuscate=False))
        print(self.header_bytearray(obfuscate=False)[3:])
        return crc8_legic(self.legic_header.UID + self.header_bytearray(obfuscate=False)[3:] + bytearray([0x00, 0x00]) + self.stamp + self.key)

    def wrp(self, obfuscate=True):
        wrp = self.stamp.copy()

        if obfuscate:
            return obfuscate_bytearray(wrp, self.legic_header.MCC)
        else:
            return wrp

    def payload(self, obfuscate=True):
        payload = bytearray([0x00]*12)
        payload[:3] = self.key
        payload[3] = self.compute_KGC()
        if obfuscate:
            return obfuscate_bytearray(payload, self.legic_header.MCC)
        else:
            return payload

    @property
    def kind(self):
        return 'kgh'
