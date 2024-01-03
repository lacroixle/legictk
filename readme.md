# Legic ToolKit
This project aims to simplify Legic Prime binary blob manipulation.

It is able to parse the header and subsequent segments, and dump it into a yaml file strucure for easier manipulation. Once those manipulations done, it can be converted back into a Legic Prime binary blob, taking care of all CRC computations. The code is also ble to interpret KGH segment, which make it particulary easy to change the stamp and ID.

# Usage

```
legictk-bin2yaml -f input.bin -o output/output.yaml --kinds=kgh,raw,raw
```

The `--kinds` argument enables interpretation of the segment, in order. `raw` segment kind output segment header into the yaml file and WRP and payload content into external binary files. `kgh` segment kind correctly interpret the WRP field as the stamp and payload as the ID.

```
legictk-yaml2bin -f input/input.yaml output.bin --is-deobfuscated --obfuscate
```

# Limitations
This code has only been tested on MIM1024 cards but should work with other medias (MIM22 and MIM256). It cannot interpret the DCF field of the header, this means no GAM, IAM, etc creation.

# Dependencies
`crcmod` for CRC computations.
