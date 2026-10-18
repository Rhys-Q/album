#!/usr/bin/env python3
"""Convert a JPEG/PNG to the project's EPF1 format; no panel-native codes here."""
import argparse
import struct
import zlib
from pathlib import Path

WIDTH, HEIGHT = 1600, 1200
PALETTE = [(0, 0, 0), (255, 255, 255), (220, 30, 30),
           (255, 220, 0), (30, 70, 180), (30, 140, 60)]


def encode(indices):
    if len(indices) != WIDTH * HEIGHT or any(v > 5 or v < 0 for v in indices):
        raise ValueError('Expected 1600x1200 indices in range 0..5')
    payload = bytes((indices[i] << 4) | indices[i + 1] for i in range(0, len(indices), 2))
    header = struct.pack('<4sHHHHBBHII8s', b'EPF1', 1, 32, WIDTH, HEIGHT,
                         1, 0, 0, len(payload), zlib.crc32(payload), bytes(8))
    return header + payload


def convert(source):
    from PIL import Image, ImageOps
    with Image.open(source) as original:
        oriented = ImageOps.exif_transpose(original).convert('RGBA')
        background = Image.new('RGBA', oriented.size, 'white')
        image = Image.alpha_composite(background, oriented).convert('RGB')
    image = ImageOps.pad(image, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS, color='white')
    palette = Image.new('P', (1, 1))
    # Repeat the six valid colors; map duplicate palette entries back into 0..5.
    palette.putpalette([v for i in range(256) for v in PALETTE[i % 6]])
    indexed = image.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG)
    return encode(bytes(v % 6 for v in indexed.tobytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    data = convert(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f'{args.output}: {len(data)} bytes, EPF1; rebuild firmware to embed')


if __name__ == '__main__':
    main()
